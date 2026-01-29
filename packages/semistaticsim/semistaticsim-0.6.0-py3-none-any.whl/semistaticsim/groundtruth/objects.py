import itertools
import json
import os
from typing import List, Dict, Optional, Any
import math

import numpy as np
from semistaticsim.groundtruth.utils import seed_everything
from tqdm import tqdm

from flax import struct
import jax.numpy as jnp

from semistaticsim.groundtruth.constants import AFFORDANCE_NAMES
from semistaticsim.groundtruth.procthor_object import ProcThorObject
from semistaticsim.groundtruth.utils import is_sublevel
from semistaticsim.rendering.simulation.spatialutils.proximity_spatial_funcs import bbox_dist

# os.environ["JAX_PLATFORM_NAME"] = "cpu"
import jax

# jax.config.update('jax_platform_name', "cpu")
import prior

from semistaticsim.rendering.ai2thor_hippo_controller import get_sim
from semistaticsim.rendering.floor import ReachabilityGraph
from semistaticsim.rendering.utils.dict2xyztup import dict2xyztuple


def str2int(str):
    # Convert string to bytes
    b = str.encode("utf-8")  # or "ascii" if you know it's ASCII

    # Convert bytes to integer
    i = int.from_bytes(b, byteorder="big")  # use "little" for little-endian
    return i


def int2str(i):
    b_back = i.to_bytes((i.bit_length() + 7) // 8, byteorder="big")
    s_back = b_back.decode("utf-8")
    return s_back


def add_receptacle(receptacles: Dict[str, Dict[str, float]], new_receptacle, new_p):
    # Scale down all existing probabilities to make space for new_p
    for _, v in receptacles.items():
        v["p"] *= 1 - new_p

    # Add new object
    receptacles[new_receptacle] = {"p": new_p}

    # Optionally recompute counts if they should stay proportional
    total_count = sum(v["count"] for v in receptacles.values() if "count" in v)
    new_count = int(round(total_count * new_p))  # scale by total count
    receptacles[new_receptacle]["count"] = new_count

    # Renormalize counts to keep integer consistency
    total_count_new = total_count + new_count
    for v in receptacles.values():
        v["p"] = v["count"] / total_count_new

    return receptacles


def specific_id_to_generic(id: str) -> str:
    return id.split("|")[0]


@struct.dataclass
class ObjectCollection:
    pickupables: ProcThorObject  # vmapped
    receptacles: ProcThorObject  # vmapped
    mat_pickupable_to_receptacles: jnp.ndarray

    pickupable_ids: List[str] = struct.field(pytree_node=False)
    receptacle_ids: List[str] = struct.field(pytree_node=False)
    pickupable_to_receptacles: Dict[str, List[str]] = struct.field(pytree_node=False)

    @staticmethod
    def _sample_unique_pickupables(key, valid_pickupables, limit_num_pickupables, p_pickupables):
        """
        Sample pickupables ensuring no two pickupables have the exact same name.
        """
        seen_names = set()
        pickupables_to_keep = []

        # Create a list of available indices
        available_indices = list(range(len(valid_pickupables)))
        p_available = p_pickupables.copy()

        while len(pickupables_to_keep) < limit_num_pickupables and len(available_indices) > 0:
            # Renormalize probabilities
            p_normalized = p_available / p_available.sum()

            # Sample one index
            key, rng = jax.random.split(key)
            sampled_idx = jax.random.choice(rng, len(available_indices), replace=False, p=p_normalized).item()

            actual_idx = available_indices[sampled_idx]
            pickupable_name = specific_id_to_generic(valid_pickupables[actual_idx]["id"])

            # Check if we've already seen this name
            if pickupable_name not in seen_names:
                seen_names.add(pickupable_name)
                pickupables_to_keep.append(actual_idx)

            # Remove this index from available options
            available_indices.pop(sampled_idx)
            p_available = jnp.delete(p_available, sampled_idx)

        return pickupables_to_keep

    @classmethod
    def create(
        cls,
        path: str,
        key: jax.random.PRNGKey,
        do_surface_receptacles_only: bool = True,
        limit_num_pickupables: int = 2,
        limit_num_receptacles_per_pickupable: int = 3,
        max_pickupable_per_receptacle: int = 3,
        bias_sampling: bool = True,
        oob_receptacle_prob: float = 0.0,
    ):
        if not do_surface_receptacles_only:
            raise NotImplementedError()

        print("Creating ObjectCollection from path:", path)

        if not os.path.exists(path):
            #raise NotImplementedError()
            tmp_dir = path.split("/object_data")[0]
            write_object_affordances_for_procthor(
                tmp_dir, unique_receptacles=False, num_scenes_to_do=1, env_indices=[int(path.split("/")[-1])]
            )
            assert os.path.exists(path), f"Failed to create object data at {path}"

        with open(f"{path}/receptacles.json", "r") as f:
            receptacles = json.load(f)

        with open(f"{path}/all_objects.json", "r") as f:
            all_objects = json.load(f)

        with open(f"{path}/pickupables.json", "r") as f:
            pickupables = json.load(f)

        with open(f"{path}/movables.json", "r") as f:
            moveables = json.load(f)

        curdir = "/".join(__file__.split("/")[:-1])
        with open(f"{curdir}/receptacles_prior.json") as f:
            receptacle_prior = json.load(f)
        with open(f"{curdir}/pickupables_prior.json") as f:
            pickupable_prior = json.load(f)

        # only consider non-openable receptacles
        INVALID_RECEPTACLES = jnp.nonzero(jnp.array([r["affordances"]["openable"] for r in receptacles]))[0].tolist()
        VALID_RECEPTACLES = jnp.nonzero(jnp.array([not r["affordances"]["openable"] for r in receptacles]))[0].tolist()

        # 1. Remove Pickupables with no available receptacles
        INVALID_PICKUPABLES = []
        VALID_PICKUPABLES = []
        for p in pickupables:
            for i, r_index in enumerate(p["valid_receptacles"]):
                if r_index not in VALID_RECEPTACLES:  # marks the bad receptacles as invalid
                    p["valid_receptacles"][i] = -1
            if (jnp.array(p["valid_receptacles"]) == -1).sum() < 2:
                INVALID_PICKUPABLES.append(p)
            else:
                VALID_PICKUPABLES.append(p)
        del pickupables

        # 2. Select some pickuables, mark the others as static
        if bias_sampling:
            p_pickupables = jnp.array(
                [pickupable_prior[specific_id_to_generic(p["id"])]["count"] for p in VALID_PICKUPABLES]
            )
            p_pickupables = p_pickupables / p_pickupables.sum()
        else:  # uniform sampling
            p_pickupables = jnp.ones((len(VALID_PICKUPABLES),)) / len(VALID_PICKUPABLES)
        key, rng = jax.random.split(key)
        limit_num_pickupables = len(VALID_PICKUPABLES) if limit_num_pickupables == -1 else limit_num_pickupables

        # Sample pickupables ensuring no duplicate names
        pickupables_to_keep = cls._sample_unique_pickupables(
            rng, VALID_PICKUPABLES, limit_num_pickupables, p_pickupables
        )
        for p_id in range(len(VALID_PICKUPABLES)):
            if p_id not in pickupables_to_keep:
                INVALID_PICKUPABLES.append(VALID_PICKUPABLES[p_id])
                VALID_PICKUPABLES[p_id] = None
        VALID_PICKUPABLES = list(filter(lambda x: x is not None, VALID_PICKUPABLES))

        # 3. Select some receptacles for each pickupable
        RECEPTACLES_FOR_THESE_PICKUPABLES = dict()
        receptacle_pickupable_count = {}  # Maps receptacle_id -> count of assigned pickupables

        # Scarcity-first ordering: process pickupables that have the FEWEST available receptacles first
        pickupable_order = sorted(
            range(len(VALID_PICKUPABLES)),
            key=lambda pid: sum(1 for r in VALID_PICKUPABLES[pid]["valid_receptacles"] if r != -1),
        )
        for p_id in pickupable_order:
            p = VALID_PICKUPABLES[p_id]

            receptacle_ids_for_this_p = [r for r in p["valid_receptacles"] if r != -1]

            # Filter out receptacles that have reached max_pickupable_per_receptacle
            available_receptacles = [
                r
                for r in receptacle_ids_for_this_p
                if max_pickupable_per_receptacle == -1
                or receptacle_pickupable_count.get(r, 0) < max_pickupable_per_receptacle
            ]

            # If no receptacles are available (all are full), trigger error and cry
            if len(available_receptacles) == 0:
                raise RuntimeError(
                    f"All receptacles for pickupable {p['id']} have reached max capacity. Consider changing the seed or the scene."
                )

            if bias_sampling:
                r_names = [specific_id_to_generic(receptacles[i]["id"]) for i in available_receptacles]
                p_receptacles = jnp.array([receptacle_prior[specific_id_to_generic(name)]["count"] for name in r_names])
                p_receptacles = p_receptacles / p_receptacles.sum()
            else:
                p_receptacles = jnp.ones((len(available_receptacles),)) / len(available_receptacles)

            key, rng = jax.random.split(key)
            lim_receptacles = (
                len(available_receptacles)
                if limit_num_receptacles_per_pickupable == -1
                else limit_num_receptacles_per_pickupable
            )
            max_receptacles = jax.random.randint(rng, (), 1, lim_receptacles + 1)
            key, rng = jax.random.split(key)
            valid_receptacles_to_keep = jnp.sort(
                jax.random.choice(
                    rng,
                    jnp.array(available_receptacles),
                    (min(max_receptacles, len(available_receptacles)),),
                    replace=False,
                    p=p_receptacles,
                )
            ).tolist()
            RECEPTACLES_FOR_THESE_PICKUPABLES[p_id] = valid_receptacles_to_keep

            # Update the count for each assigned receptacle
            for r_id in valid_receptacles_to_keep:
                receptacle_pickupable_count[r_id] = receptacle_pickupable_count.get(r_id, 0) + 1
        ALL_RECEPTACLES_FOR_THESE_PICKUPABLES = list(
            set(itertools.chain.from_iterable(RECEPTACLES_FOR_THESE_PICKUPABLES.values()))
        )
        for p_id, p in enumerate(VALID_PICKUPABLES):
            for i in range(len(p["valid_receptacles"])):
                r_index = p["valid_receptacles"][i]
                if r_index not in RECEPTACLES_FOR_THESE_PICKUPABLES[p_id]:
                    p["valid_receptacles"][i] = -1
        for i in range(len(VALID_RECEPTACLES)):
            r = VALID_RECEPTACLES[i]
            if r not in ALL_RECEPTACLES_FOR_THESE_PICKUPABLES:
                VALID_RECEPTACLES[i] = None
                INVALID_RECEPTACLES.append(r)
        VALID_RECEPTACLES = list(filter(lambda x: x is not None, VALID_RECEPTACLES))

        # 4. Go and get the actual receptacles from their IDs
        VALID_RECEPTACLES = [receptacles[i] for i in VALID_RECEPTACLES]
        INVALID_RECEPTACLES = [receptacles[i] for i in INVALID_RECEPTACLES]

        # 4.5 todo rematerialize the indices to make all this faster (we only actually need VALID_RECEPTACLES, not all of them, but currently the indices in pickupables do consider all receptacles)
        if oob_receptacle_prob > 0:
            # Flip a coin for each pickupable to add the oob receptacle
            for p_id, data in RECEPTACLES_FOR_THESE_PICKUPABLES.items():
                key, rng = jax.random.split(key)
                coin = jax.random.uniform(rng, ())
                # Add OOB with 0.5 prob only if we have more than 1 receptacle already
                if len(data) > 1 and coin >= 0.5:
                    data.append(len(receptacles))
                    VALID_PICKUPABLES[p_id]["valid_receptacles"].append(len(receptacles))
                    print(f"Added OOB receptacle to pickupable {VALID_PICKUPABLES[p_id]['id']}")
                else:
                    VALID_PICKUPABLES[p_id]["valid_receptacles"].append(-1)
            SPAWN_COORD_FOR_OOB = VALID_RECEPTACLES[-1]["spawn_coordinates_above_receptacle"]
            SPAWN_COORD_FOR_OOB = [[x, -10, z] for (x, _, z) in SPAWN_COORD_FOR_OOB]
            OOB_FAKE_RECEPTACLE = {
                "id": "OOB_FAKE_RECEPTACLE",
                "position": {"x": 0, "y": -20, "z": 0},
                "rotation": {"x": 0, "y": 0, "z": 0},
                "aabb": VALID_RECEPTACLES[-1]["aabb"],
                "oobb": VALID_RECEPTACLES[-1]["oobb"],
                "affordances": VALID_RECEPTACLES[-1]["affordances"],
                "spawn_coordinates_above_receptacle": SPAWN_COORD_FOR_OOB,
                "valid_receptacles": [],
            }
            VALID_RECEPTACLES += [OOB_FAKE_RECEPTACLE]
            ALL_RECEPTACLES_FOR_THESE_PICKUPABLES.append(len(receptacles))
            receptacles += [OOB_FAKE_RECEPTACLE]

        # 4.5 rematerialize receptacles to remove inactive indices
        MAP_FULLRECEPTACLE_TO_VALIDRECEPTACLE_IDS = {j: i for i, j in enumerate(ALL_RECEPTACLES_FOR_THESE_PICKUPABLES)}
        VALID_RECEPTACLES = [receptacles[i] for i in ALL_RECEPTACLES_FOR_THESE_PICKUPABLES]

        # 5. save everything
        with open(f"{curdir}/pickupables.json") as f:
            pickupable_to_receptacle_weights = json.load(f)

        if oob_receptacle_prob > 0:
            for k in pickupable_to_receptacle_weights.keys():
                # Add obb receptacle prob to all pickupables so that the prob and counts match
                pickupable_to_receptacle_weights[k] = add_receptacle(
                    pickupable_to_receptacle_weights[k], "OOB_FAKE_RECEPTACLE", oob_receptacle_prob
                )

        mat_p_to_r = jnp.ones((len(VALID_PICKUPABLES), len(VALID_RECEPTACLES))) * -1
        p_name_to_r_names = {}
        # For each pickupable, get the valid receptacles and their weights
        for i, p in enumerate(VALID_PICKUPABLES):
            id = p["id"]
            valid_r_indices = p["valid_receptacles"]

            valid_r_names = [receptacles[i]["id"] for i in valid_r_indices if i != -1]
            valid_r_weights = np.array(
                [
                    pickupable_to_receptacle_weights[specific_id_to_generic(id)][specific_id_to_generic(r_id)]["p"]
                    for r_id in valid_r_names
                ]
            )
            valid_r_weights = (valid_r_weights / valid_r_weights.sum()).tolist()

            p_name_to_r_names[id] = valid_r_names
            for valid_r in valid_r_indices:
                if valid_r == -1:
                    continue
                mat_p_to_r = mat_p_to_r.at[i, MAP_FULLRECEPTACLE_TO_VALIDRECEPTACLE_IDS[valid_r]].set(
                    valid_r_weights.pop(0)
                )

        pickupable_names = [p["id"] for p in VALID_PICKUPABLES]
        receptacle_names = [r["id"] for r in VALID_RECEPTACLES]

        receptacle_instances = ProcThorObject.create(VALID_RECEPTACLES)
        pickupable_instances = ProcThorObject.create(VALID_PICKUPABLES)

        self = cls(
            pickupables=pickupable_instances,
            pickupable_ids=pickupable_names,
            receptacles=receptacle_instances,
            receptacle_ids=receptacle_names,
            pickupable_to_receptacles=p_name_to_r_names,
            mat_pickupable_to_receptacles=mat_p_to_r,
        )  # , moveable_instances)

        print("Object collection contains following mappings:")
        print(self.pickupable_to_receptacles)
        return self

    @staticmethod
    def _is_this_p_on_this_r(p, r):
        spawn_poses = r["spawn_coordinates_above_receptacle"]
        spawn_bbox = jnp.array(spawn_poses)
        min_xz, max_xz = jnp.min(spawn_bbox, axis=0)[0::2], jnp.max(spawn_bbox, axis=0)[0::2]

        p_pos_xz = jnp.array(dict2xyztuple(p["position"]))[0::2]  # gets first and last of the 3 (xyz)

        xz_is_ok = jnp.all((p_pos_xz >= min_xz) & (p_pos_xz <= max_xz))

        y_is_ok = jnp.array(dict2xyztuple(p["position"]))[1] > jnp.max(spawn_bbox, axis=0)[1]
        return jnp.logical_and(xz_is_ok, y_is_ok)
        # todo test if p_pos is on r
        # p_xy = jnp.array([p_pos[0], p_pos[2]])

    def valid_receptacle_indices_for_pickupable_index(self, p_i: int) -> jnp.ndarray:
        r_ids = self.mat_pickupable_to_receptacles[p_i]
        r_ids = r_ids > -1
        r_ids = jnp.nonzero(r_ids)[0]
        return r_ids

    def get_receptacle_by_index(self, index: int) -> ProcThorObject:
        return self.receptacles.take(index)

    def get_pickupable_by_index(self, index: int) -> ProcThorObject:
        return self.pickupables.take(index)

    def pickupable_id_to_index(self, id: str) -> int | None:
        for i, p in enumerate(self.pickupable_ids):
            if p == id:
                return i
        return None

    def receptacle_id_to_index(self, id: str) -> int | None:
        for i, r in enumerate(self.receptacle_ids):
            if r == id:
                return i
        return None

    def receptacle_index_to_id(self, i: int) -> str:
        return self.receptacle_ids[i]

    def pickupable_index_to_id(self, i: int) -> str:
        return self.pickupable_ids[i]

    def get_pickupable_by_id(self, i: int) -> str:
        return self.pickupable_ids[i]


def distance_to_box(point_pos, box_center, box_size):
    """
    Calculates the shortest distance from a point to an Axis-Aligned Bounding Box (AABB).



    Args:
        point_pos (tuple): (x, y, z) position of the point.
        box_center (tuple): (x, y, z) center of the box.
        box_size (tuple): (x, y, z) dimensions of the box (width, height, depth).

    Returns:
        float: The shortest Euclidean distance.
    """
    # Calculate the distance to the box on each axis.
    # The half_size is the distance from the center to the face of the box.
    half_size_x = box_size[0] / 2
    half_size_y = box_size[1] / 2
    half_size_z = box_size[2] / 2

    # The absolute distance from the point to the box center on each axis
    abs_dist_x = abs(point_pos[0] - box_center[0])
    abs_dist_y = abs(point_pos[1] - box_center[1])
    abs_dist_z = abs(point_pos[2] - box_center[2])

    # dx, dy, dz are the distances *outside* the box's extent on each axis.
    # If the point is inside or on the boundary on an axis, this value is 0.
    dx = max(0, abs_dist_x - half_size_x)
    dy = max(0, abs_dist_y - half_size_y)
    dz = max(0, abs_dist_z - half_size_z)

    # The total shortest distance is the Euclidean distance of (dx, dy, dz).
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def write_object_affordances_for_scene(
    path: str,
    scene: Dict,
    receptacle_mappings: Dict,
    pickupable_mappings: Dict,
    pickupables_blacklist: list = None,
    unique_receptacles: bool = False,
) -> None:
    sim = get_sim(
        scene,
        renderInstanceSegmentation=True,
        renderDepthImage=True,
        im_width=10,
        im_height=10,
        fov=90,
        save_topdown=False,
        mindist_to_walls=0.0,
        mindist_to_obj=0.0,
    )
    c = sim.controller  # Controller(scene=scene)
    reachability_graph: ReachabilityGraph = sim.full_reachability_graph
    reachability_graph = reachability_graph.filter_(
        c.last_event.metadata["objects"],
        mindist_to_obj=0.5,
    )

    objects = c.last_event.metadata["objects"]
    receptacles = []
    pickupables = []
    movables = []
    uninterestings = []

    def is_object_reachable(objId_or_obj):
        if isinstance(objId_or_obj, str):
            obj = [obj for obj in objects if obj["objectId"] == objId_or_obj][0]
        else:
            obj = objId_or_obj

        object_center = dict2xyztuple(obj["position"])
        object_size = dict2xyztuple(obj["axisAlignedBoundingBox"]["size"])
        node_position, distances = reachability_graph.shunt_to_bbox(object_center, object_size)
        #node_size = np.array([0.6, 0.95, 0.6])

        GRID_SIZE = reachability_graph.grid_size * 2
        return (distances < GRID_SIZE * 2).any()

    MAX_SIZE_SPAWN_COORDINATES = -np.inf

    for i, object in enumerate(objects):

        SKIP_THIS_OBJ = False
        for exclude in ["room", "door", "wall", "floor"]:
            if exclude in object["name"]:
                SKIP_THIS_OBJ = True
                break
        if SKIP_THIS_OBJ:
            continue

        id = object["objectId"]

        affordances = {affordance: object[affordance] for affordance in AFFORDANCE_NAMES}
        position = object["position"]
        rotation = object["rotation"]
        aabb = object["axisAlignedBoundingBox"]
        oobb = object["objectOrientedBoundingBox"]
        if oobb is None:
            oobb = {"cornerPoints": object["axisAlignedBoundingBox"]["cornerPoints"]}

        if id.split("|")[0] in receptacle_mappings and affordances["receptacle"]:
            spawnCoordinatesAboveReceptacle = c.step(
                action="GetSpawnCoordinatesAboveReceptacle", objectId=id, anywhere=True
            ).metadata["actionReturn"]
            spawnCoordinatesAboveReceptacle = [dict2xyztuple(p) for p in spawnCoordinatesAboveReceptacle]
        else:
            spawnCoordinatesAboveReceptacle = []

        MAX_SIZE_SPAWN_COORDINATES = max(MAX_SIZE_SPAWN_COORDINATES, len(spawnCoordinatesAboveReceptacle))

        ret = {
            "id": id,
            "position": position,
            "rotation": rotation,
            "aabb": aabb,
            "affordances": affordances,
            "oobb": oobb,
            "spawn_coordinates_above_receptacle": spawnCoordinatesAboveReceptacle,
        }

        obj_type = id.split("|")[0]
        if (
            obj_type in receptacle_mappings
            and affordances["receptacle"]
            and not affordances["pickupable"]
            and is_object_reachable(id)
        ):
            if unique_receptacles:
                if not is_sublevel(id):
                    receptacles.append(ret)
                else:
                    uninterestings.append(ret)
            else:
                receptacles.append(ret)
        elif (
            obj_type in pickupable_mappings
            and not affordances["receptacle"]
            and affordances["pickupable"]
            and obj_type not in pickupables_blacklist
            and is_object_reachable(id)
        ):
            pickupables.append(ret)
        elif affordances["moveable"]:
            movables.append(ret)
        else:
            uninterestings.append(ret)
    c.stop()

    receptacles = [r for r in receptacles if "___" not in r["id"]]
    for r in receptacles:
        assert len(r["spawn_coordinates_above_receptacle"]) > 0
        MISSING = MAX_SIZE_SPAWN_COORDINATES - len(r["spawn_coordinates_above_receptacle"])
        if MISSING > 0:
            arg_to_add = np.random.choice(len(r["spawn_coordinates_above_receptacle"]), MISSING, replace=True)
            to_add = np.array(r["spawn_coordinates_above_receptacle"])[arg_to_add]
            r["spawn_coordinates_above_receptacle"] = r["spawn_coordinates_above_receptacle"] + to_add.tolist()

    def find_receptacles_for_pickupable(clean_p_id: str, receptacle_list: List, mapping: Dict) -> List[int]:
        ret = []
        for receptacle_index, receptacle in enumerate(receptacle_list):
            clean_receptacle_id = receptacle["id"].split("|")[0]
            if clean_receptacle_id in mapping[clean_p_id]:
                ret.append(receptacle_index)
        MISSING = len(receptacles) - len(ret)
        ret += [-1] * MISSING
        return ret

    for p in pickupables:
        p_id = p["id"].split("|")[0]
        # Find the valid receptacles for this pickupable
        p["valid_receptacles"] = find_receptacles_for_pickupable(p_id, receptacles, pickupable_mappings)

    # for r in receptacles:
    # r_id = r["id"].split("|")[0]
    # Find the valid pickupables for this receptacle
    # r["valid_pickupables"] = find_receptacles_for_pickupable(r_id, pickupables, receptacle_mappings)

    def set_empty_receptacles(o: List[Dict[str, Any]]) -> None:
        if isinstance(o, list):
            return [set_empty_receptacles(o) for o in o]
        o["valid_receptacles"] = []

    def set_empty_pickupables(o: List[Dict[str, Any]]) -> None:
        if isinstance(o, list):
            return [set_empty_pickupables(o) for o in o]
        o["valid_pickupables"] = []

    set_empty_receptacles(receptacles)
    set_empty_pickupables(pickupables)
    set_empty_receptacles(uninterestings)
    set_empty_pickupables(uninterestings)
    set_empty_pickupables(movables)
    set_empty_receptacles(movables)

    os.makedirs(path, exist_ok=True)

    def save_objects(list, name):
        with open(path + f"/{name}.json", "w") as f:
            json.dump(list, f)

    save_objects(pickupables, "pickupables")
    save_objects(receptacles, "receptacles")
    save_objects(uninterestings, "uninterestings")
    save_objects(movables, "movables")
    save_objects(pickupables + receptacles + uninterestings + movables, "all_objects")


def write_object_affordances_for_procthor(
    path: str, unique_receptacles: bool = False, num_scenes_to_do: Optional[int] = None, env_indices: List[int] = None, splits_to_do: List[str]= ["test"]
) -> None:
    dataset = prior.load_dataset("procthor-10k")
    dataset = {
        "test": dataset.test,
        "train": dataset.train,
        "val": dataset.val,
    }

    with open("/".join(__file__.split("/")[:-1]) + "/receptacles.json", "r") as f:
        receptacle_mappings = json.load(f)

    def pickupable_to_receptacle_prob(receptacles_dict: Dict) -> None:
        """
        Compute P(receptacle | pickupables) from counts in receptacles.json
        """
        pickupable_counts = {}  # object: total_count
        pickupable_to_receptacle = {}

        for receptacle, contained in receptacles_dict.items():
            for obj, stats in contained.items():
                count = stats["count"]
                pickupable_counts[obj] = pickupable_counts.get(obj, 0) + count

                if obj not in pickupable_to_receptacle:
                    pickupable_to_receptacle[obj] = {}
                pickupable_to_receptacle[obj][receptacle] = {"count": count}

        # Compute probabilities
        for obj, receptacle_map in pickupable_to_receptacle.items():
            total = pickupable_counts[obj]
            for receptacle, stats in receptacle_map.items():
                stats["p"] = stats["count"] / total if total > 0 else 0.0

        with open("/".join(__file__.split("/")[:-1]) + "/pickupables.json", "w") as f:
            json.dump(pickupable_to_receptacle, f, indent=4)

    def compute_prior_prob(receptacles_dict: Dict, f_name: str) -> None:
        """
        Compute P(receptacle) or P(pickupable) from counts in receptacles.json or pickupables.json
        """
        prior = {}
        total_count = 0

        for receptacle, contained in receptacles_dict.items():
            item_total = sum(stats["count"] for stats in contained.values())
            prior[receptacle] = {"count": item_total}
            total_count += item_total

        for _, stats in prior.items():
            stats["p"] = stats["count"] / total_count if total_count > 0 else 0.0

        with open(os.path.join("/".join(__file__.split("/")[:-1]), f_name), "w") as f:
            json.dump(prior, f, indent=4)

    # pickupable_to_receptacle_prob(receptacle_mappings)
    with open("/".join(__file__.split("/")[:-1]) + "/pickupables.json", "r") as f:
        pickupable_mappings = json.load(f)

    # Read pickupables blacklist
    with open("/".join(__file__.split("/")[:-1]) + "/pickupables_blacklist.json", "r") as f:
        blacklist = json.load(f)
    # compute_prior_prob(receptacle_mappings, "receptacles_prior.json")
    # compute_prior_prob(pickupable_mappings, "pickupables_prior.json")

    if env_indices is not None:
        num_scenes_to_do = len(env_indices)

    NUM_SCENES_DONE = 0
    for split, data in dataset.items():
        if splits_to_do is not None and split not in splits_to_do:
            continue

        for i, scene in enumerate(tqdm(data)):
            if num_scenes_to_do is not None and NUM_SCENES_DONE >= num_scenes_to_do:
                return
            if env_indices is not None and i not in env_indices:
                continue
            print(f"Processing scene {i} in split {split}...")
            write_object_affordances_for_scene(
                path + f"/object_data/{split}/{i}",
                scene,
                receptacle_mappings,
                pickupable_mappings,
                pickupables_blacklist=blacklist,
                unique_receptacles=unique_receptacles,
            )
            NUM_SCENES_DONE += 1


if __name__ == "__main__":
    curdir = "/".join(__file__.split("/")[:-1])
    key = seed_everything(12345)
    env_indices = [10, 26, 153, 208, 253, 310, 336, 390, 431, 701]
    write_object_affordances_for_procthor(
        curdir, unique_receptacles=False, num_scenes_to_do=10, env_indices=env_indices
    )
    ObjectCollection.create(
        curdir + "/object_data/test/0",
        key,
        limit_num_pickupables=20,
        limit_num_receptacles_per_pickupable=2,
        max_pickupable_per_receptacle=3,  # Set to -1 if no limit
        oob_receptacle_prob=0.1,
        bias_sampling=False,
    )
