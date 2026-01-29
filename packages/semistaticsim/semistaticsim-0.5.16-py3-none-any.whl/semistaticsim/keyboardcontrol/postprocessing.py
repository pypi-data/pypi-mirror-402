import shutil
import numpy as np
import os
import jax.numpy as jnp

from pathlib import Path
from tqdm import tqdm
import json

from semistaticsim.datawrangling.sssd import load_sssd, GeneratedSemiStaticData

def purge_dir(res_path, prefix):
    for item in os.listdir(res_path):
        item_path = os.path.join(res_path, item)
        if not os.path.isdir(item_path) or not item.startswith(prefix):
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)


def move_indexed_files(src_dir: Path, dst_dir: Path, indices, ext):
    dst_dir.mkdir(parents=True, exist_ok=True)
    for trg_idx, src_idx in enumerate(indices):
        shutil.move(src_dir / f"{src_idx:05d}.{ext}", dst_dir / f"{trg_idx:05d}.{ext}")


def save_run(
    mask: np.ndarray,
    sssd_data: GeneratedSemiStaticData,
    res_path: str,
    tmpdir: str,
    batch_size: int,
    gt_sss_data: GeneratedSemiStaticData,
):
    # Delete existing results
    if os.path.exists(res_path):
        shutil.rmtree(res_path)
    os.makedirs(res_path, exist_ok=True)
    # Index df samples
    indices = np.nonzero(mask)[0]
    subset = sssd_data.take_by_global_timestep(stop_or_start=None, indices=indices)

    # --- Move Images ---
    images_src = tmpdir / "images"
    images_dst = res_path / "images"
    for subdir in images_src.iterdir():
        if subdir.is_dir():
            # detect extension from first file
            sample = next(subdir.iterdir())
            ext = sample.suffix.lstrip(".")

            move_indexed_files(src_dir=subdir, dst_dir=images_dst / subdir.name, indices=indices, ext=ext)

    # --- Move poses ---
    move_indexed_files(src_dir=tmpdir / "poses", dst_dir=res_path / "poses", indices=indices, ext="json")

    # Save parquet
    subset.dump_to_parquet(res_path, dump_leftover=True, verbose=False, batch_size=batch_size)

    # Move keyframes txt and fix indices
    keyframes_src = tmpdir / "keyframes.txt"
    with open(keyframes_src, "r") as f:
        keyframe_lines = f.readlines()
    keyframe_indices = [int(line.strip()) for line in keyframe_lines]
    # Map from global indices to run indices
    index_map = {global_idx: run_idx for run_idx, global_idx in enumerate(indices)}
    keyframe_run_indices = [index_map[idx] for idx in keyframe_indices if idx in index_map]
    keyframes_dst = res_path / "keyframes.txt"
    with open(keyframes_dst, "w") as f:
        for idx in keyframe_run_indices:
            f.write(f"{idx:05d}\n")

    # Copy id_to_color mapping if exists
    id_to_color_src = tmpdir / "id_to_color.json"
    if id_to_color_src.exists():
        shutil.copy(id_to_color_src, res_path / "id_to_color.json")

    def accuracy(subset):
        preds: jnp.array = subset.sum_up_minors_into_major()._assignment
        targets: jnp.array = gt_sss_data._assignment
        # Only get actual predictions
        valid_mask = preds >= 0
        matches = (preds == targets) & valid_mask
        # Global accuracy
        total_correct = matches.sum()
        total_valid = valid_mask.sum()
        global_acc = jnp.where(total_valid > 0, total_correct / total_valid, 0.0)
        # Object accuracy
        obj_correct = matches.sum(axis=-1)
        obj_valid = valid_mask.sum(axis=-1)
        object_acc = jnp.where(obj_valid > 0, obj_correct / obj_valid, 0.0)
        return global_acc.item(), object_acc.squeeze().tolist()

    global_acc, object_acc = accuracy(subset)
    # Save accuracy as json
    with open(os.path.join(res_path, "accuracy.json"), "w") as f:
        json.dump({"global_accuracy": global_acc, "object_accuracy": object_acc}, f)


def format_results(res_path: str, tmpdir: str, batch_size: int, gt_sss_data: GeneratedSemiStaticData) -> dict:
    sssd_data = load_sssd(tmpdir)
    # Get timestamps to split data folder
    timestamps = np.concatenate([data._timestamp for data in sssd_data.get_generator_of_selves()])
    floored_timestamps = np.floor(timestamps)
    unique_timestamps = np.unique(floored_timestamps)
    # Split data into multiple folders based on timestamps
    for t in tqdm(unique_timestamps, desc="Formatting results"):
        mask = floored_timestamps == t
        if mask.sum() > 1:
            print(f"Processing run_id: {int(t.item())} with {mask.sum()} samples")
            gt_data_for_this_major = gt_sss_data.take_by_global_timestep(int(t), int(t) + 1)
            save_run(
                mask,
                sssd_data,
                res_path=Path(res_path) / f"run_{int(t.item())}",
                tmpdir=Path(tmpdir),
                batch_size=batch_size,
                gt_sss_data=gt_data_for_this_major,
            )
