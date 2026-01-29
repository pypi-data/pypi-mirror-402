import os
import random
import re
import json
import numpy as np
from pathlib import Path
from natsort import natsorted
import jax


def objects_to_txt():
    curdir = "/".join(__file__.split("/")[:-1])

    with open(os.path.join(curdir, "pickupables_prior.json")) as f:
        pickupable_prior = json.load(f)
    with open(os.path.join(curdir, "receptacles_prior.json")) as f:
        receptacle_prior = json.load(f)

    def split_camel_preserve_acronyms(name):
        # Insert space between lowercase → uppercase
        # OR between acronym → normal word
        s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)
        s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
        return s.lower()

    objects = set(pickupable_prior.keys()) | set(receptacle_prior.keys())
    objects = {split_camel_preserve_acronyms(obj) for obj in objects}

    # Save to txt file
    with open(os.path.join(curdir, "objects.txt"), "w") as f:
        for obj in sorted(objects):
            f.write(f"{obj}\n")


def seed_everything(seed: int = 42) -> jax.random.PRNGKey:
    random.seed(seed)
    np.random.seed(seed)
    # Make hashing deterministic
    os.environ["PYTHONHASHSEED"] = str(seed)
    return jax.random.PRNGKey(seed)

def is_sublevel(name: str) -> str:
    # Check if receptacle is a sublevel one by looking for '___' pattern
    return bool(re.search(r"___", name))


def format_receptacle(name: str) -> str:
    # Extract all digit sequences and join them
    numbers = "".join(re.findall(r"\d+", name))

    # Remove everything after last non-digit separator, then strip trailing '|' or whitespace
    label = re.split(r"\d+", name)[0].rstrip("| ").strip()

    return f"{label} # {numbers}" if numbers else label


def evaluate_runs_accuracy(res_root: str) -> dict:
    folder_path = Path(res_root)
    run_folders = natsorted(folder_path.glob("run_*"))

    # Load object names to map the accuracy array back to specific objects
    with open(folder_path.parent / 'groundtruth' / "pickupable_names.json", "r") as f:
        pickupable_names = json.load(f)

    # Initialize accumulators
    total_scene_accuracy = 0.0
    # Create a dictionary to sum accuracies per object name: {'Apple': 0.0, 'Cup': 0.0}
    per_object_acc_sums = {name: 0.0 for name in pickupable_names}
    valid_runs_count = 0
    print(f"Found {len(run_folders)} runs. Evaluating...")

    for i, run_folder in enumerate(run_folders):
        accuracy_file = run_folder / "accuracy.json"
        
        if accuracy_file.exists():
            try:
                with open(accuracy_file, "r") as f:
                    data = json.load(f)
                
                # Extract data
                run_global = float(data["global_accuracy"])
                run_objects = data["object_accuracy"]  

                # 1. Print Global Accuracy for this iteration
                print(f"Run {i} ({run_folder.name}): Global Accuracy = {run_global:.4f}")

                # 2. Accumulate Global
                total_scene_accuracy += run_global
                valid_runs_count += 1

                # 3. Accumulate Per Object
                # We assume the order in 'object_accuracy' matches 'pickupable_names'
                if len(run_objects) != len(pickupable_names):
                    print(f"  [Warning] Mismatch in object counts for {run_folder.name}")
                    
                for name, acc in zip(pickupable_names, run_objects):
                    per_object_acc_sums[name] += float(acc)

            except (json.JSONDecodeError, KeyError) as e:
                print(f"Run {i} ({run_folder.name}): Error reading JSON - {e}")
        else:
            print(f"Run {i} ({run_folder.name}): Accuracy file not found.")

    # --- Calculate Averages ---
    if valid_runs_count > 0:
        avg_scene_accuracy = total_scene_accuracy / valid_runs_count
        avg_object_accuracy = {
            name: total / valid_runs_count 
            for name, total in per_object_acc_sums.items()
        }
    else:
        avg_scene_accuracy = 0.0
        avg_object_accuracy = {name: 0.0 for name in per_object_acc_sums}

    # --- Print Summary ---
    print("\n" + "#" * 40)
    print(f"Overall Scene Accuracy: {avg_scene_accuracy:.4f}")
    print("-" * 40)
    print("Per Object Accuracy:")
    for name, acc in avg_object_accuracy.items():
        print(f"  {name:<20}: {acc:.4f}")
    print("#" * 40)

    return {
        "scene_accuracy": avg_scene_accuracy,
        "per_object_accuracy": avg_object_accuracy
    }

def find_missing_runs(res_root: str, expected_runs: int = 100) -> list:
    folder_path = Path(res_root)
    run_folders = natsorted(folder_path.glob("run_*"))
    existing_run_indices = {
        int(run_folder.name.split("_")[-1]) for run_folder in run_folders
    }
    missing_runs = [
        i for i in range(expected_runs) if i not in existing_run_indices
    ]
    print(f"Missing runs: {missing_runs}")

if __name__ == "__main__":
    run_id = 336
    split = "test"
    seed = 0
    # objects_to_txt()
    evaluate_runs_accuracy(
        f"generated_data/semistaticsim/{split}/{run_id}/{seed}/privileged"
    )  # Replace with actual path
    find_missing_runs(
        f"generated_data/semistaticsim/{split}/{run_id}/{seed}/privileged",
        expected_runs=672
    )  
