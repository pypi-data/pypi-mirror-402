import json
import os
import random
import sys
import time
from typing import Dict
from tqdm import trange
from ai2thor.controller import Controller
from ai2thor.platform import CloudRendering
from traitlets import Any
import jax
import jax.numpy as jnp

from semistaticsim.datawrangling.sssd import load_sssd, path_2_parts
from semistaticsim.groundtruth.utils import seed_everything
from semistaticsim.rendering.floor import ReachabilityGraph

from semistaticsim.rendering.simulation.skill_simulator import Simulator

DEFAULT_ROBOT_HEIGHT = 1.0
DEFAULT_ROBOT_ROT = 90


def _get_self_install_dir():
    filepath = __file__
    return "/".join(filepath.split("/")[:-2])


def _get_ai2thor_install_dir():
    return _get_self_install_dir() + "/ai2thor"


def _get_ai2thor_install_build_dir():
    return _get_ai2thor_install_dir() + "/unity/builds"


def _get_ai2thorbuilds_dir(which="fixed"):
    return _get_self_install_dir() + f"/ai2thorbuilds/{which}"


def get_hippo_controller(scene, target_dir=None, **kwargs):
    # if isinstance(scene, str):
    #    if scene.endswith(".json"):
    #        with open(scene, "r") as f:
    #            scene = json.load(f)
    #    elif "procthor" in scene.lower():
    #        num = int(scene.replace("procthor", "")) #
    #        from procthorprocessing.procthor_utils import get_procthor10k
    #        scene = get_procthor10k()[num]

    # try:
    #    os.unlink( _get_ai2thor_install_build_dir())
    # except Exception as e:
    #    pass
    # assert not os.path.exists(_get_ai2thor_install_build_dir())
    # os.symlink(_get_ai2thorbuilds_dir(), _get_ai2thor_install_build_dir(), target_is_directory=True)

    cuda_visible_devices = list(
        map(
            int,
            filter(
                lambda y: y.isdigit(),
                map(
                    lambda x: x.strip(),
                    os.environ.get("CUDA_VISIBLE_DEVICES", "").split(","),
                ),
            ),
        )
    )

    print("\n\n~~~AI2THOR GPU NOTICE~~~\n\n")
    if len(cuda_visible_devices) > 0:
        print("AI2Thor controller will use GPU(s):", cuda_visible_devices)
        print("If this occurs on a cluster without a monitor, you need to set up a virtual display.")
        print("You can also diagnose this when facing a `vulkaninfo` error. Remove access to the GPU!")
    else:
        print("AI2Thor controller will use CPU only.")
    print("\n\n~~~~~~~~~~~~~~~~~~~~~~~\n\n")

    if os.environ.get("APPEND_CONDA_TO_LD_LIBRARY_PATH", "False") == "True":
        os.environ["LD_LIBRARY_PATH"] = f"{os.environ["CONDA_PREFIX"]}/lib:{os.environ["LD_LIBRARY_PATH"]}"
        os.environ["LD_LIBRARY_PATH"] = f"{os.environ["LD_LIBRARY_PATH"]}:{os.environ["CONDA_PREFIX"]}/lib"
        #print(os.environ["LD_LIBRARY_PATH"])
        #exit()

    # Setup Platform Config
    if sys.platform != "darwin":
        ai2_platform = CloudRendering
    else:
        ai2_platform = None

    # Force controller to initially when random wait occurs
    controller = None
    max_retries = 5
    for attempt in range(max_retries):
        try:
            def find_free_port_in_range(start=1024, end=65535):
                import socket

                sock = socket.socket()
                sock.bind(("", 0))
                return sock.getsockname()[-1]

            ai2thor_port = find_free_port_in_range()
            print("Free port found for AI2Thor controller:", ai2thor_port)

            # os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = "/home/mila/c/charlie.gauthier/Holodeck/venv/lib/python3.10/site-packages/cv2/qt/plugins"
            # os.environ["QT_QPA_PLATFORM"] = "/home/mila/c/charlie.gauthier/Holodeck/venv/lib/python3.10/site-packages/cv2/qt/fonts"  # use offscreen rendering to avoid X11 issues
            # os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
            # os.environ["TCM_ENABLE"] = "1"
            # os.environ["KMP_INIT_AT_FORK"] = "FALSE"
            # os.environ["TF_CPP_MIN_LOG_LEVEL"] = "1"  # suppress TensorFlow warnings
            # os.environ["TOKENIZERS_PARALLELISM"] = "false"
            os.environ["XDF_RUNTIME_DIR"] = "/tmp"  # fix for X11 issues in some environments

            # if "ENVIRONMENT" in os.environ:
            #    os.environ.pop("ENVIRONMENT")
            # print("Unsetting slurm variables...")
            # yay jank :)
            # UNSET_SLURM = []
            # for k, v in os.environ.items():
            #    if k.startswith("SLURM"):
            #        os.environ.pop(k)
            #        #UNSET_SLURM.append(f"{k}")
            # if len(UNSET_SLURM) > 0:
            #    UNSET_SLURM = "env -u " + " -u ".join(UNSET_SLURM)
            # else:
            #    UNSET_SLURM = ""
            # print("WILL UNSET SLURM ENV VARS:", UNSET_SLURM)

            print(
                "Local executable path for AI2Thor controller:",
                f"{_get_ai2thor_install_build_dir()}/thor-Linux64-local/thor-Linux64-local",
            )

            print(
                "Attempting to create AI2Thor controller... this might time out. If so, you need to allocate more cpu or ram or figure something else out."
            )
            # Random start delay to prevent simultaneous port binding (parallel runs)
            if attempt > 0: 
                time.sleep(random.uniform(0.5, 1.5))

            print(f"Attempt {attempt + 1}/{max_retries}: init AI2Thor on port {ai2thor_port}...")

            controller = Controller(
                port=ai2thor_port,
                platform=ai2_platform,
                agentMode="default",
                makeAgentsVisible=False,
                scene=scene,
                server_start_timeout=30,
                **kwargs,
            )
            print(f"Success: AI2Thor Controller active on port {ai2thor_port}.")
            return controller
        
        except Exception as e:
            print(f"Warning: Controller init failed on port {ai2thor_port}. Error: {e}")

            # Check if this was the last attempt
            if attempt == max_retries - 1:
                print("CRITICAL: Failed to initialize AI2-THOR after max retries.")
                print("Exiting...")
                os._exit(1)

            # Exponential backoff: Wait 2s, 4s, 8s...
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"Retrying in {wait_time:.2f}s...")
            time.sleep(wait_time)


def get_list_of_objects(scene):
    with open(scene, "r") as f:
        scene_txt = f.read()
    runtime_container = get_runtime_container(scene, scene_txt)
    # return runtime_container.get_object_list_with_children_as_string()
    ret = runtime_container.as_llmjson()
    del ret["robot0"]
    return ret


def get_runtime_container(scene, scene_txt_for_memoization):
    print("CACHE MISS: getting runtime container...")

    runtime_container = get_sim(scene, just_runtime_container=True)

    return runtime_container


def resolve_scene_id(floor_name):
    split, house, _ = path_2_parts(floor_name)
    import prior

    dataset = prior.load_dataset("procthor-10k")
    floor_name = dataset[split][house]

    if isinstance(floor_name, dict):
        return floor_name

    if isinstance(floor_name, int) or floor_name.startswith("FloorPlan"):
        floor_name = str(floor_name)
        return f"FloorPlan{floor_name.replace('FloorPlan', '')}"

    if isinstance(floor_name, str) and "procthor" in floor_name:
        return floor_name

    if not floor_name.endswith(".json"):
        if os.path.exists(floor_name + "/scene.json"):
            floor_name += "/scene.json"

    assert floor_name.endswith(".json")

    return floor_name

    with open(floor_name, "r") as f:
        scene = json.load(f)
    return scene


def remove_repeated_pickupables(controller, pickupables) -> Dict[str, Any]:
    objects_id = [obj["objectId"] for obj in controller.last_event.metadata["objects"]]
    pickupable_name = [p_name.split("|")[0] for p_name in pickupables]
    for obj_id in objects_id:
        # Check if the prefix is in the list of pickupable
        if obj_id.split("|")[0] in pickupable_name and obj_id not in pickupables:
            print(f"Disabling repeated pickupable: {obj_id}")
            controller.step(action="DisableObject", objectId=obj_id)
            # README: for some reason this line hangs...
            # controller.step(action="RemoveFromScene", objectId=obj_id)


def removed_pickupables(controller, target_pickupables) -> Dict[str, Any]:
    for obj in controller.last_event.metadata["objects"]:
        obj_id = obj["objectId"]
        is_pickupable = obj["pickupable"]
        # Disable objects that are big and take valuable space of receptacles
        if obj_id.split('|')[0] in {"HousePlant", 'Television', 'Toaster', 'Ottoman'} and not is_pickupable:
            print(f"Disabling miscellaneous: {obj_id}")
            controller.step(action="DisableObject", objectId=obj_id)
        if is_pickupable and obj_id not in target_pickupables:
            print(f"Disabling non-pickupable: {obj_id}")
            controller.step(action="DisableObject", objectId=obj_id)


def random_teleport(key: jax.random.PRNGKey, controller: Controller, full_reachability_graph: ReachabilityGraph):
    possible_start_nodes = list(full_reachability_graph.nodes)
    possible_start_nodes = list(sorted(possible_start_nodes))
    random_pos = jax.random.choice(key, jnp.array(possible_start_nodes), shape=()).tolist()
    print(f"Teleporting to random position: {random_pos}")
    controller.step(
        action="TeleportFull",
        position={
            "x": random_pos[0],
            "y": DEFAULT_ROBOT_HEIGHT,
            "z": random_pos[2],
        },
        rotation=DEFAULT_ROBOT_ROT,
        standing=True,
        horizon=30,
        forceAction=True,
    )


def get_sim(
    floor_no,
    just_controller=False,
    just_controller_no_setup=False,
    humanviewing_params={},
    renderInstanceSegmentation=False,
    renderDepthImage=False,
    im_width: int = 1250,
    im_height: int = 1250,
    fov: int = 90,
    grid_size: float = 0.25,
    save_topdown: bool = True,
    mindist_to_walls: float = 0.3,
    mindist_to_obj: float = 0.01,
    apn_dist_thresh: float = float("inf")
):
    try:
        generated_sss_data = load_sssd(floor_no)
        # Seed scene
        _, procthor_index, scene_seed = path_2_parts(floor_no)
        seed = scene_seed + procthor_index
        key = seed_everything(seed)
    except Exception as e:
        print("Error while loading SSD:", e)
        generated_sss_data = None
        seed = 0
        key = seed_everything(seed)

    if not isinstance(floor_no, dict):
        scene = resolve_scene_id(floor_no)
        assert sum(list(map(int, (just_controller, just_controller_no_setup)))) <= 1
    else:
        scene = floor_no

    controller = get_hippo_controller(
        scene,
        width=im_width,
        height=im_height,
        snapGrid=False,
        snapToGrid=False,
        visibilityDistance=1,
        fieldOfView=fov,
        gridSize=grid_size,
        rotateStepDegrees=20,
    )

    if just_controller_no_setup:
        return controller

    # Remove repeated pickupables so they are unique
    # remove_repeated_pickupables(controller, generated_sss_data.pickupable_names)
    if generated_sss_data is not None:
        removed_pickupables(controller, generated_sss_data.pickupable_names)
    all_initial_objects = controller.last_event.metadata["objects"]
    NO_ROBOTS = 1

    CEILING_HEIGHT = controller.last_event.metadata["sceneBounds"]["size"]["y"]

    from semistaticsim.rendering.floor import FloorPolygon

    floor_polygon = FloorPolygon.create(scene, grid_size)

    reachable_positions = controller.step("GetReachablePositions").metadata["actionReturn"]
    reachable_positions = [(p["x"], p["y"], p["z"]) for p in reachable_positions]
    # floor_polygon.plot_self(samples=reachable_positions)

    full_reachability_graph = floor_polygon.rechability_graph(
        pre_selected_points=reachable_positions,
        mindist_to_walls=mindist_to_walls,
        DEFAULT_ROBOT_HEIGHT=DEFAULT_ROBOT_HEIGHT,
        set_mindist_to_obj=mindist_to_obj,
    )

    # initialize n agents into the scene
    controller.step(
        dict(
            action="Initialize",
            agentMode="default",
            snapGrid=False,
            snapToGrid=False,
            gridSize=grid_size,
            rotateStepDegrees=90,
            visibilityDistance=1,
            fieldOfView=90,
            agentCount=NO_ROBOTS,
            renderInstanceSegmentation=renderInstanceSegmentation,
            renderDepthImage=renderDepthImage,
        ),
        raise_for_failure=True,
    )
    
    key, rng = jax.random.split(key)
    random_teleport(rng, controller, full_reachability_graph)

    # run a few physics steps to make bad objects fall through floor...
    for _ in trange(10):
        controller.step(
            action="MoveAhead",
            moveMagnitude=0.01,
        )
    for obj in controller.last_event.metadata["objects"]:
        if obj["position"]["y"] < -1:
            controller.step(action="SetMassProperties", objectId=obj["objectId"], mass=0.0, drag=1500, angularDrag=1500)
            y = None
            for otherobj in all_initial_objects:
                if otherobj["objectId"] == obj["objectId"]:
                    y = otherobj["position"]["y"]
                    break
            assert y is not None
            controller.step(
                action="PlaceObjectAtPoint",
                objectId=obj["objectId"],
                position={
                    "x": obj["position"]["x"],
                    "y": y,
                    "z": obj["position"]["z"],
                },
            )

    key, rng = jax.random.split(key)
    random_teleport(rng, controller, full_reachability_graph)

    # setting up tools for human viewing
    from semistaticsim.rendering.simulation.humanviewing import HumanViewing

    controller.humanviewing = HumanViewing(controller, None, **humanviewing_params)

    if just_controller:
        return controller

    simulator = Simulator(
        controller=controller,
        full_reachability_graph=full_reachability_graph,
        floor=floor_polygon,
        sss_data=generated_sss_data,
        save_topdown=save_topdown,
        seed=seed,
        apn_dist_thresh=apn_dist_thresh,
    )

    hu = HumanViewing(controller, simulator, **humanviewing_params)
    controller.humanviewing = hu
    simulator.humanviewing = hu

    print("Done building simulator")
    return simulator
