from typing import Dict
import cv2
import shutil
import math
from typing import Sequence
import numpy as np
from copy import deepcopy
import os
import hydra
import json
from omegaconf import DictConfig
import yaml
from pathlib import Path
from natsort import natsorted
from omegaconf import DictConfig, OmegaConf

from semistaticsim.datawrangling.sssd import GeneratedSemiStaticData
from semistaticsim.spoof_hydra import maybe_spoof_hydra

if not OmegaConf.has_resolver("eval"):
    OmegaConf.register_new_resolver("eval", eval)

actionList = {
    "MoveAhead": "w",
    "MoveBack": "s",
    "MoveLeft": "a",
    "MoveRight": "d",
    "RotateLeft": "q",
    "RotateRight": "e",
    "LookUp": "r",
    "LookDown": "f",
    "FINISH": "p",
    # Interact action
    "PickupObject": "z",
    "PutObject": "x",
    "OpenObject": "c",
    "CloseObject": "v",
    "ToggleObjectOn": "b",
    "ToggleObjectOff": "n",
    "SliceObject": "m",
    "GoToObject": "k",
    "StepSemiStaticObjects": "i",
    "GoToAllInstances": "l",
}

ROBOTS = [
    {
        "name": "robot1",
        "skills": [
            "GoToObject",
            "OpenObject",
            "CloseObject",
            "BreakObject",
            "SliceObject",
            "SwitchOn",
            "SwitchOff",
            "PickupObject",
            "PutObject",
            "DropHandObject",
            "ThrowObject",
            "PushObject",
            "PullObject",
        ],
    },
    {
        "name": "robot2",
        "skills": [
            "GoToObject",
            "OpenObject",
            "CloseObject",
            "BreakObject",
            "SliceObject",
            "SwitchOn",
            "SwitchOff",
            "PickupObject",
            "PutObject",
            "DropHandObject",
            "ThrowObject",
            "PushObject",
            "PullObject",
        ],
    },
]


def save_sim_results(
    sim,
    res_path: str,
    batch_size: int,
    cleanup_previous_data=False,
    generate_video=False,
    generate_gif=False,
):
    from semistaticsim.keyboardcontrol.postprocessing import format_results, purge_dir

    # Delete ALL data including formatted runs
    if cleanup_previous_data and os.path.exists(res_path):
        shutil.rmtree(res_path)
    # Delete data but leave run folders
    elif os.path.exists(res_path):
        purge_dir(res_path, prefix="run_")
    os.makedirs(res_path, exist_ok=True)

    # Save id_to_color mapping if exists
    with open(os.path.join(sim.tmpdir, "id_to_color.json"), "w") as f:
        json.dump(sim.id_to_color, f, indent=4)

    if sim.privileged_apn and sim.privileged_apn.global_length > 0:
        sim.privileged_apn.dump_to_parquet(sim.tmpdir, dump_leftover=True, batch_size=batch_size)
    # Delete privileged_apn to save memory
    del sim.privileged_apn
    # Privileged data (presence/absence)
    format_results(res_path, sim.tmpdir, batch_size, sim.sss_data)

    # Videos & Gifs
    if generate_video or generate_gif:
        # Generate videos and gifs for each run
        run_folders = natsorted(Path(res_path).glob("run_*"))
        for run_folder in run_folders:
            vid_root = run_folder / "video"
            gif_root = run_folder / "gif"
            os.makedirs(vid_root, exist_ok=True)
            os.makedirs(gif_root, exist_ok=True)
            img_root = run_folder / "images"
            # Read the images and compile them into videos
            for item in os.listdir(img_root):
                frame_list = []
                img_dir = img_root / item
                img_files = sorted(os.listdir(img_dir))
                for img_file in img_files:
                    img_path = img_dir / img_file
                    frame = (
                        cv2.imread(str(img_path), cv2.IMREAD_UNCHANGED)[..., None]
                        if "depth" in item
                        else cv2.cvtColor(cv2.imread(str(img_path)), cv2.COLOR_RGB2BGR)
                    )
                    frame_list.append(frame)
                if generate_video:
                    export_video(str(vid_root / f"{item}.mp4"), frame_list, depth=("depth" in item))
                if generate_gif:
                    clip = show_video(frame_list, fps=5, depth=("depth" in item))
                    clip.write_gif(str(gif_root / f"{item}.gif"))


def get_interact_object(env, visible_only=True):
    candidates = []
    objectId = ""

    for obj in env.last_event.metadata["objects"]:
        if visible_only:
            if obj["visible"]:
                candidates.append(obj["objectId"])
        else:
            candidates.append(obj["objectId"])

    if len(candidates) == 0:
        print("no valid interact object candidates")
        return None
    else:
        print("===========choose index from the candidates==========")

        # Create mapping from characters to indices
        char_to_index = {}
        index = 0

        # Add digits 0-9
        for i in range(10):
            if index < len(candidates):
                char_to_index[str(i)] = index
                print(f"{i} : {candidates[index]}")
                index += 1

        # Add lowercase letters a-z (will also handle uppercase via normalization)
        for c in "abcdefghijklmnopqrstuvwxyz":
            if index < len(candidates):
                char_to_index[c] = index
                char_to_index[c.upper()] = index  # Map both cases to same index
                print(f"{c}/{c.upper()} : {candidates[index]}")
                index += 1

        # Add remaining uppercase letters if we have more than 36 objects
        for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if index < len(candidates) and c not in char_to_index:
                char_to_index[c] = index
                print(f"{c} : {candidates[index]}")
                index += 1

        # Define shift key codes (common shift key codes)
        SHIFT_CODES = {225, 65505, 65506}  # Left Shift, Right Shift, etc.

        while True:
            keystroke = cv2.waitKey()
            print(f"Raw keystroke: {keystroke}")

            if keystroke == actionList["FINISH"]:
                print("stop interact")
                break

            # Ignore shift keys
            if keystroke in SHIFT_CODES:
                print("Ignoring Shift key...")
                continue

            # Convert keystroke to character
            try:
                # Convert ASCII code to character
                if 0 <= keystroke <= 255:
                    char = chr(keystroke)
                    print(f"Converted to char: '{char}'")

                    # Normalize to lowercase for letters (since we map both cases)
                    if char.isalpha():
                        normalized_char = char.lower()
                    else:
                        normalized_char = char

                    # Check if character is in our mapping
                    if normalized_char in char_to_index:
                        object_index = char_to_index[normalized_char]
                        objectId = candidates[object_index]
                        print(f"Selected object: {objectId}")
                        break
                    else:
                        print(f"INVALID KEY '{char}' - not in available options")
                else:
                    print(f"INVALID KEYCODE {keystroke}")
            except Exception as e:
                print(f"ERROR processing keystroke: {e}")
                continue

        return objectId


def keyboard_play(
    env,
    sim=None,
):
    sim.kill_sim_on_condition_failure = False
    sim.raise_exception_on_condition_failure = False
    env.humanviewing.incr_action_idx()

    if sim is None:
        raise NotImplementedError()

    step = 0
    while True:
        keystroke = cv2.waitKey(0)
        step += 1

        if keystroke == ord(actionList["FINISH"]):
            env.stop()
            cv2.destroyAllWindows()
            print("action: STOP")
            break

        if keystroke == ord(actionList["MoveAhead"]):
            action = "MoveAhead"
            print("action: MoveAhead")
            sim.MoveAhead(ROBOTS[0], None)
        elif keystroke == ord(actionList["MoveBack"]):
            action = "MoveBack"
            print("action: MoveBack")
            sim.MoveBack(ROBOTS[0], None)
        elif keystroke == ord(actionList["MoveLeft"]):
            action = "MoveLeft"
            print("action: MoveLeft")
            sim.MoveLeft(ROBOTS[0], None)
        elif keystroke == ord(actionList["MoveRight"]):
            action = "MoveRight"
            print("action: MoveRight")
            sim.MoveRight(ROBOTS[0], None)
        elif keystroke == ord(actionList["RotateLeft"]):
            action = "RotateLeft"
            print("action: RotateLeft")
            sim.RotateLeft(ROBOTS[0], None)
        elif keystroke == ord(actionList["RotateRight"]):
            action = "RotateRight"
            print("action: RotateRight")
            sim.RotateRight(ROBOTS[0], None)
        elif keystroke == ord(actionList["LookUp"]):
            action = "LookUp"
            print("action: LookUp")
            sim.LookUp(ROBOTS[0])
        elif keystroke == ord(actionList["LookDown"]):
            action = "LookDown"
            print("action: LookDown")
            sim.LookDown(ROBOTS[0])

        elif keystroke == ord(actionList["GoToObject"]):
            action = "GoToObject"
            print("Go to which object?")
            objectId = get_interact_object(env, visible_only=False)
            sim.GoToObject(ROBOTS[0], objectId)
        elif keystroke == ord(actionList["PickupObject"]):
            action = "PickupObject"
            print("action: PickupObject")
            objectId = get_interact_object(env)
            sim.PickupObject(ROBOTS[0], objectId)
            # if len(sim.exception_queue) <= 0:
            pickedupobj = objectId
        elif keystroke == ord(actionList["PutObject"]):
            action = "PutObject"
            print("action: PutObject")
            objectId = get_interact_object(env)
            # if len(sim.exception_queue) <= 0:
            sim.PutObject(ROBOTS[0], pickedupobj, objectId)
            pickedupobj = None
        elif keystroke == ord(actionList["OpenObject"]):
            action = "OpenObject"
            print("action: OpenObject")
            objectId = get_interact_object(env)
            sim.OpenObject(ROBOTS[0], objectId)
        elif keystroke == ord(actionList["CloseObject"]):
            action = "CloseObject"
            print("action: CloseObject")
            objectId = get_interact_object(env)
            sim.CloseObject(ROBOTS[0], objectId)
        elif keystroke == ord(actionList["ToggleObjectOn"]):
            action = "ToggleObjectOn"
            print("action: ToggleObjectOn")
            objectId = get_interact_object(env)
            sim.ToggleObjectOn(ROBOTS[0], objectId)
        elif keystroke == ord(actionList["ToggleObjectOff"]):
            action = "ToggleObjectOff"
            print("action: ToggleObjectOff")
            objectId = get_interact_object(env)
            sim.ToggleObjectOff(ROBOTS[0], objectId)
        elif keystroke == ord(actionList["StepSemiStaticObjects"]):
            action = "StepSemiStaticObjects"
            print("action: StepSemiStaticObjects")
            sim.StepSemiStaticObjects()
        elif keystroke == ord(actionList["SliceObject"]):
            action = "SliceObject"
            print("action: SliceObject")
            objectId = get_interact_object(env)
            sim.SliceObject(ROBOTS[0], objectId)
        elif keystroke == ord(actionList["GoToAllInstances"]):
            action = "GoToAllInstances"
            print("action: GoToAllInstances")
            sim.GoToAllInstances(ROBOTS[0])
        else:
            print("INVALID KEY", keystroke)
            continue

        print("Interact object:")
        try:
            print(objectId)
        except UnboundLocalError:
            pass

        print("Waiting for sim to reply")
        print(env.last_action)


def show_video(frames: Sequence[np.ndarray], fps: int = 10, depth: bool = False):
    """Show a video composed of a sequence of frames.

    Example:
    frames = [
        controller.step("RotateRight", degrees=5).frame
        for _ in range(72)
    ]
    show_video(frames, fps=5)
    """
    rgb_frames = deepcopy(frames)
    if depth:
        rgb_frames = []
        for frame in frames:
            frame = frame.astype(np.float32)
            frame = (frame / (frame.max() + 1e-8)) * 255.0
            frame = frame.astype(np.uint8)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            rgb_frames.append(frame)

    from moviepy import ImageSequenceClip

    frames = ImageSequenceClip(rgb_frames, fps=fps)
    return frames


def export_video(path, frames, depth: bool = False):
    """Merges all the saved frames into a .mp4 video and saves it to `path`"""

    video = cv2.VideoWriter(
        path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        5,
        (frames[0].shape[1], frames[0].shape[0]),
    )
    for frame in frames:
        if depth:
            frame = frame.astype(np.float32)
            frame = (frame / (frame.max() + 1e-8)) * 255.0
            frame = frame.astype(np.uint8)
            frame_color = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            video.write(frame_color)
        else:
            video.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    cv2.destroyAllWindows()
    video.release()


def compute_rotate_camera_pose(center, pose, degree_per_frame=6):
    """degree_per_frame: set the degree of rotation for each frame"""

    def rotate_pos(x1, y1, x2, y2, degree):
        angle = math.radians(degree)
        n_x1 = (x1 - x2) * math.cos(angle) - (y1 - y2) * math.sin(angle) + x2
        n_y1 = (x1 - x2) * math.sin(angle) + (y1 - y2) * math.cos(angle) + y2

        return n_x1, n_y1

    x, z = rotate_pos(pose["position"]["x"], pose["position"]["z"], center["x"], center["z"], degree_per_frame)
    pose["position"]["x"], pose["position"]["z"] = x, z

    direction_x = center["x"] - x
    direction_z = center["z"] - z
    pose["rotation"]["y"] = math.degrees(math.atan2(direction_x, direction_z))

    return pose


def initialize_side_camera_pose(scene_bound, pose, third_fov=60, slope_degree=45, down_angle=70, scale_factor=8):
    """
    down_angle: the x-axis rotation angle of the camera, represents the top view of the front view from top to bottom, which needs to be less than 90 degrees
    ensure the line vector between scene's center & camera 's angel equal down_angle
    scale_factor scale the camera's view, make it larger ensure camera can see the whole scene
    """
    fov_rad = np.radians(third_fov)
    pitch_rad = np.radians(down_angle)
    distance = (scene_bound["center"]["y"] / 2) / np.tan(fov_rad / 2)
    pose["position"]["y"] = scene_bound["center"]["y"] + distance * scale_factor * np.sin(pitch_rad)
    pose["position"]["z"] = scene_bound["center"]["z"] - distance * scale_factor * np.cos(pitch_rad)

    pose["rotation"]["x"] = down_angle

    pose["orthographic"] = False
    del pose["orthographicSize"]

    pose = compute_rotate_camera_pose(scene_bound["center"], pose, slope_degree)

    return pose


def compute_timespan(timespan_str: str, dt: float) -> int:
    from semistaticsim.groundtruth.schedule import TIME_SCALES_MAPPING

    num, unit = timespan_str.split()
    num = int(num)
    unit = TIME_SCALES_MAPPING[unit]
    timespan = num * unit * (1 / dt)
    return int(timespan)


def run_keyboard_simulator(
    cfg: DictConfig,
    scene="FloorPlan205_physics",
    im_width: int = 640,
    im_height: int = 480,
    fov: int = 90,
    mindist_to_walls: float = 0.3,
    mindist_to_obj: float = 0.01,
    timespan: str = "1 week",
    start_at: str = "0 hour",
    cleanup_previous_data: bool = False,
    generate_video: bool = False,
    generate_gif: bool = False,
    save_topdown: bool = True,
    batch_size: int = 128,
    **kwargs,
):

    from semistaticsim.rendering.ai2thor_hippo_controller import get_sim
    import jax
    # Load groundtruth config
    gt_cfg = OmegaConf.load(os.path.join(scene, "config.yaml"))

    gt_timespan = compute_timespan(gt_cfg.timespan_to_collect, gt_cfg.dt)
    timespan = compute_timespan(timespan, gt_cfg.dt)
    start_at = compute_timespan(start_at, gt_cfg.dt)
    assert timespan <= (
        gt_timespan - start_at
    ), f"Requested timespan {timespan} exceeds collected timespan {gt_timespan} when starting at {start_at}"


    sim = get_sim(
        scene,
        renderInstanceSegmentation=True,
        renderDepthImage=True,
        im_width=im_width,
        im_height=im_height,
        fov=fov,
        save_topdown=save_topdown,
        mindist_to_walls=mindist_to_walls,
        mindist_to_obj=mindist_to_obj,
        apn_dist_thresh=float("inf") if "apn_dist_thresh" not in cfg.mode else cfg.mode.apn_dist_thresh,
    )
    sim.human_render = True
    controller = sim.controller
    # Replace cfg with job one
    if sim.sss_data is not None:
        sim.sss_data = sim.sss_data.replace(config=cfg)

    # Tick the clock to the start time
    for n_ticks in range(start_at):
        sim.sss_data = sim.sss_data.step()
        sim.privileged_apn = None  # resets the accumulator
    sim.StepSemiStaticObjects(tick=False)  # render=False)
    sim.render()

    ## use keyboard control agent
    keyboard_play(
        controller,
        sim,
    )

    res_path = os.path.join(os.path.dirname(scene), f"privileged")
    save_sim_results(sim, res_path, batch_size, cleanup_previous_data, generate_video, generate_gif)


def run_simulator(
    cfg: DictConfig,
    scene="FloorPlan205_physics",
    im_width: int = 640,
    im_height: int = 480,
    fov: int = 90,
    mindist_to_walls: float = 0.3,
    mindist_to_obj: float = 0.01,
    timespan: str = "1 week",
    start_at: str = "0 hour",
    cleanup_previous_data: bool = False,
    generate_video: bool = False,
    generate_gif: bool = False,
    save_topdown: bool = True,
    batch_size: int = 128,
    get_simulator_instance=False,
    **kwargs,
):

    # Load groundtruth config
    gt_cfg = OmegaConf.load(os.path.join(scene, "config.yaml"))

    gt_timespan = compute_timespan(gt_cfg.timespan_to_collect, gt_cfg.dt)
    timespan = compute_timespan(timespan, gt_cfg.dt)
    start_at = compute_timespan(start_at, gt_cfg.dt)
    assert timespan <= (
        gt_timespan - start_at
    ), f"Requested timespan {timespan} exceeds collected timespan {gt_timespan} when starting at {start_at}"

    from semistaticsim.rendering.ai2thor_hippo_controller import get_sim, random_teleport
    import jax

    sim = get_sim(
        scene,
        renderInstanceSegmentation=True,
        renderDepthImage=True,
        im_width=im_width,
        im_height=im_height,
        fov=fov,
        save_topdown=save_topdown,
        mindist_to_walls=mindist_to_walls,
        mindist_to_obj=mindist_to_obj,
        apn_dist_thresh=float("inf") if "apn_dist_thresh" not in cfg.mode else cfg.mode.apn_dist_thresh,
    )
    # Automatically navigate to all receptacles
    sim.kill_sim_on_condition_failure = False
    sim.raise_exception_on_condition_failure = False
    # Replace cfg with job one
    if sim.sss_data is not None:
        sim.sss_data = sim.sss_data.replace(config=cfg)
    # Get key from simulator seeding
    key, _ = jax.random.split(sim.key)

    # Tick the clock to the start time
    for n_ticks in range(start_at):
        key, _ = jax.random.split(key)
        sim.sss_data = sim.sss_data.step()
        sim.privileged_apn = None  # resets the accumulator
    sim.StepSemiStaticObjects(tick=False)  # render=False)
    sim.render()

    print("**************************************")
    print(f"Starting data collection at major tick {start_at}")
    print("**************************************")

    if get_simulator_instance:
        print("Returning simulator instance without running simulation...")
        return sim

    try:
        for i in range(timespan):
            print(f"Navigating sequence at time step {i + 1} / {timespan}")
            sim.GoToAllInstances(ROBOTS[0])
            sim.reset_nav_metrics()  # Reset nav metrics to avoid OOM
            sim.privileged_apn = sim.privileged_apn.backprop_majors()
            sim.privileged_apn = sim.privileged_apn.dump_to_parquet(
                sim.tmpdir, dump_leftover=False, verbose=True, batch_size=batch_size
            )
            # Once done navigating to all receptacles, step semi-static objects and teleport
            key, rng = jax.random.split(key)
            random_teleport(rng, sim.controller, sim.full_reachability_graph)
            # sets up next timestep
            sim.StepSemiStaticObjects()
            sim.render()
            sim.privileged_apn = sim.privileged_apn.remove_nan_sentinel()

        #accuracies = compute_run_accuracy(sim, start_at, timespan)
        print("**************************************")
        print("Finished navigating to all receptacles")
        print("**************************************")
    except KeyboardInterrupt:
        print("\n!!! User interrupted simulation (Ctrl+C). Saving partial data... !!!")
    except Exception as e:
        raise e
        print(f"\n!!! Simulation encountered an error: {e}. Saving partial data... !!!")
    finally:
        print("Saving simulation results...")
        res_path = os.path.join(os.path.dirname(scene), f"privileged")
        save_sim_results(sim, res_path, batch_size, cleanup_previous_data, generate_video, generate_gif)


def _main_impl(cfg: DictConfig):
    import os

    os.environ["JAX_PLATFORM_NAME"] = "cpu"
    import jax

    jax.config.update("jax_platform_name", "cpu")

    mode_to_func = {"auto": run_simulator, "keyboard": run_keyboard_simulator, "rollout": run_simulator}

    return mode_to_func[cfg.mode.runfunc](cfg, **cfg.mode)


@hydra.main(version_base=None, config_path="config", config_name="config")
def cli_main(cfg):
    maybe_spoof_hydra("semistaticsim.keyboardcontrol.main_skillsim")

    return _main_impl(cfg)


def main(version_base=None, config_path=None, config_name="config", overrides=None):
    # Use absolute path to config directory for package compatibility
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config")
    from hydra import initialize_config_dir, compose
    from hydra.core.hydra_config import HydraConfig

    if overrides is None:
        overrides = []

    with initialize_config_dir(
        config_dir=config_path,
        version_base=None,
    ):
        cfg = compose(config_name=config_name, overrides=overrides, return_hydra_config=True)
        HydraConfig.instance().set_config(cfg)
    return _main_impl(cfg)


if __name__ == "__main__":
    cli_main()
