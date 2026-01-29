import copy
import math
import re
import sys
import tempfile
import time
from typing import Dict, Tuple, Union, List
import cv2
import jax.numpy as jnp
import os
import json
import random
import networkx as nx

import jax.random

from semistaticsim.datawrangling.sssd import GeneratedSemiStaticData, path_2_parts
from semistaticsim.groundtruth.procthor_object import ProcThorObject, trim_spawn_coordinates, oobb_to_aabb
from semistaticsim.rendering.floor import FloorPolygon
from semistaticsim.rendering.simulation.ai2thor_metadata_reader import (
    get_robot_inventory,
    get_object_position_from_controller,
    get_robot_position_from_controller,
    get_object_size_from_controller,
    get_object_from_controller,
    compute_aabb_distance,
)
from semistaticsim.rendering.simulation.spatialutils.proximity_spatial_funcs import bbox_dist
from semistaticsim.rendering.utils.dict2xyztup import dict2xyztuple, xyztuple2dict
from semistaticsim.rendering.simulation.spatialutils.motion_planning import astar, geodesic_distance_on_path_nodes

DELAY_FOR_DISPLAY = 10 if sys.platform == "darwin" else 50


class PutObjectNoPosition(Exception):
    pass


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def save_json(data, path: str):
    ensure_dir(os.path.dirname(path))
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def save_images(frame, idx, path: str, color=True, depth=False):
    """Save a list of frames (RGB or depth) to disk."""
    ensure_dir(path)
    if depth:
        # Make this uint16 image and save as png
        depth_m_to_mm = frame * 1000.0
        depth_mm_uint16 = depth_m_to_mm.astype(np.uint16)
        cv2.imwrite(os.path.join(path, f"{idx:05d}.png"), depth_mm_uint16)
    else:
        img = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        if color:
            cv2.imwrite(os.path.join(path, f"{idx:05d}.jpg"), img)
        else:
            cv2.imwrite(os.path.join(path, f"{idx:05d}.png"), img)


class Simulator:
    def __init__(
        self,
        controller,
        full_reachability_graph,
        floor: FloorPolygon,
        sss_data: GeneratedSemiStaticData,
        save_topdown: bool = True,
        seed: int = 42,
        human_render=False,
        apn_dist_thresh=float("inf"),
    ):
        self.apn_dist_thresh = apn_dist_thresh
        self.human_render = human_render
        self.controller = controller
        self.full_reachability_graph = full_reachability_graph
        self.floor = floor
        self.sss_data = sss_data

        self.goal_thresh = 1.0  # Make this a class argument
        self.keyframes = set()

        self.kill_thread = False

        self.action_queue = []
        self.action_listener = None

        self.done_actions = []

        self.message_queue = []
        self.roblock = {}

        # Nav metrics
        self.nav_metrics = {}
        self.reset_nav_metrics()

        self.key = jax.random.PRNGKey(seed)
        self.save_topdown = save_topdown
        self.last_metadata: Dict[str, jnp.array] = {}
        self.privileged_apn: GeneratedSemiStaticData = None
        # Temp dict to dump all images and save RAM
        procthor_split, procthor_index, procthor_seed = (
            path_2_parts(sss_data.parquet_paths[0]) if sss_data is not None else ("test", 0, 0)
        )
        base_tmpdir = tempfile.mkdtemp(dir="/tmp")
        self.tmpdir = f"{base_tmpdir}/{procthor_split}/{procthor_index}/{procthor_seed}"
        ensure_dir(os.path.join(self.tmpdir))
        self._step = 0

        self.id_to_color = self.controller.humanviewing.get_mapping_id_to_color()
        self.camera_intrinsics = self.controller.humanviewing.get_camera_intrinsics()
        self.print_number_receptacles_per_pickupable()
        self.first_sssd_step_done = False
        self.StepSemiStaticObjects(tick=False)  # , render=False)
        # self.render()

    def set_apn_dist_thresh(self, new_apn_dist_thresh):
        self.apn_dist_thresh = new_apn_dist_thresh

    def reset_nav_metrics(self):
        self.nav_metrics = {"steps": 0, "move_steps": [], "rot_steps": []}

    def save_step(self):
        img_dir = os.path.join(self.tmpdir, "images")
        for frame_name, frame in self.last_metadata.items():
            if "depth" in frame_name:
                save_images(frame, self._step, os.path.join(img_dir, "depth"), color=False, depth=True)
            elif "semantics" in frame_name:
                save_images(frame, self._step, os.path.join(img_dir, "semantics"), color=False)
            elif "rgb" in frame_name:
                if ("top_down" in frame_name) and (not self.save_topdown):
                    continue
                save_images(frame, self._step, os.path.join(img_dir, frame_name))
            elif "pose" in frame_name:
                save_json(frame, os.path.join(self.tmpdir, "poses", f"{self._step:05d}.json"))
            else:
                pass
        if self.keyframes:
            # Append current observations to running keyframe list
            with open(os.path.join(self.tmpdir, "keyframes.txt"), "a") as f:
                f.writelines(f"{step:05d}\n" for step in self.keyframes)
            self.keyframes = set()
        self._step += 1

    def print_number_receptacles_per_pickupable(self):
        if self.sss_data is None:
            return

        semi_static = list()
        static = list()

        print(f"\n{'='*80}")
        print(f"{'PICKUPABLE TO RECEPTACLE MAPPING':^80}")
        print(f"{'='*80}\n")

        # Collect data
        for pickupable, receptacles in self.sss_data.pickupable_to_receptacle.items():
            if len(receptacles) > 1:
                semi_static.append((pickupable, receptacles))
            else:
                static.append((pickupable, receptacles))

        # Print semi-static pickupables
        if semi_static:
            print(f"{'SEMI-STATIC PICKUPABLES':-^80}")
            for pickupable, receptacles in sorted(semi_static, key=lambda x: len(x[1]), reverse=True):
                receptacle_str = ", ".join(receptacles)
                print(f"  • {pickupable[:40]:<40} → {len(receptacles)} receptacles")
                print(f"    {receptacle_str}")
            print()

        # Print static pickupables
        if static:
            print(f"{'STATIC PICKUPABLES':-^80}")
            for pickupable, receptacles in sorted(static):
                receptacle_str = receptacles[0] if receptacles else "None"
                print(f"  • {pickupable[:40]:<40} → {receptacle_str}")
            print()

        # Summary
        total = len(semi_static) + len(static)
        print(f"{'='*80}")
        print(f"  Summary: {total} total pickupables  |  {len(semi_static)} semi-static  |  {len(static)} static")
        print(f"{'='*80}\n")

    def Get_StepSemiStaticObjects_Descriptor(self, tick=True, force_sss_none=False):
        if self.sss_data is None:
            return

        if not force_sss_none:
            old_sss_data = self.sss_data
            if tick:
                self.sss_data = self.sss_data.step()

        def mk_obj_posrot(obj_name, obj_pos, obj_rot, receptacle: Union[str, None]):
            def todict(arr):
                if not isinstance(arr, dict):
                    arr = {k: np.array(arr[i]).item() for i, k in enumerate(["x", "y", "z"])}
                return arr

            try:
                obj_rot = float(obj_rot)
                obj_rot = todict([0, obj_rot, 0])
            except:
                obj_rot = todict(obj_rot)

            return {
                "objectName": obj_name,
                "rotation": obj_rot,
                "position": todict(obj_pos),
                "receptacle": receptacle,
            }

        OBJ_METADATA = self.controller.last_event.metadata["objects"]
        OBJ_METADATA = {o["objectId"]: o for o in OBJ_METADATA}

        COLLECT_POSROT = {}
        if not force_sss_none:
            for objId, pickupable_sss in self.sss_data.pickupable_selves_at_current_time.items():
                # for objId, values in self.sss_data.pickupables_at_current_time.items():
                assert objId in OBJ_METADATA
                COLLECT_POSROT[objId] = mk_obj_posrot(
                    objId,
                    pickupable_sss._position,
                    pickupable_sss._rotation,
                    receptacle=pickupable_sss.current_receptacle_for_this_pickupable(objId),
                )

        for objId, o in OBJ_METADATA.items():
            if objId in COLLECT_POSROT:
                assert objId in self.sss_data.pickupable_names
                continue

            COLLECT_POSROT[objId] = mk_obj_posrot(objId, o["position"], o["rotation"], receptacle=None)

        COLLECT_POSROT = list(COLLECT_POSROT.values())

        if not force_sss_none:
            MESSAGE = f"""The old assignment was: 
    {[f'{objId}: {old_sss_data.current_receptacle_for_this_pickupable(objId)}' for objId in self.sss_data.pickupable_names]}
    The new assignment is:
    {[f'{objId}: {self.sss_data.current_receptacle_for_this_pickupable(objId)}' for objId in self.sss_data.pickupable_names]}
    """
            MESSAGE = f"~~~~~\n{MESSAGE}\n~~~~~"
            print(MESSAGE)

        pickupables_that_moved = []
        if not force_sss_none:
            if tick:
                pickupables_that_moved = [
                    objId
                    for objId in self.sss_data.pickupable_names
                    if old_sss_data.current_receptacle_for_this_pickupable(objId)
                    != self.sss_data.current_receptacle_for_this_pickupable(objId)
                ]
            else:
                pickupables_that_moved = self.sss_data.pickupable_names

        return COLLECT_POSROT, pickupables_that_moved
        # self.SetObjectPositions(COLLECT_POSROT, pickupables_that_moved, use_SetObjectPoses=use_SetObjectPoses)

    def StepSemiStaticObjects(self, tick=True):
        if self.sss_data is None:
            return

        object_position_list, moved_pickupable_objIds = self.Get_StepSemiStaticObjects_Descriptor(
            tick=tick, force_sss_none=False
        )

        # first, teleport moving objects to the void
        object_position_dict = {obj["objectName"]: obj for obj in object_position_list}
        object_metadata_dict = {obj["objectId"]: obj for obj in self.controller.last_event.metadata["objects"]}

        # begin by putting all the objects that will move around on the floor for safely computing on-receptacle object
        # collisions in the case where PutObject fails (see the Except block)
        for obj in moved_pickupable_objIds:
            self.PickupObject(robot={"name": "robot1"}, pick_obj=obj, render_after=False, telekinesis=True)
            find_floor = {k: v for k, v in object_metadata_dict.items() if "floor" in k.lower()}
            self.PutObject(
                robot={"name": "robot1"},
                put_obj=obj,
                recp=list(find_floor.keys())[0],
                render_after=False,
                telekinesis=True,
            )
            self.controller.step(  # also make their mass 0 to prevent breakables from breaking
                action="SetMassProperties", objectId=obj, mass=0.0, drag=0, angularDrag=0
            )

        # if we dont use SetObjectPoses, we spoof teleportation using PickUp and Put
        moved_pickupable_objIds = set(moved_pickupable_objIds)
        done_moved = set()
        todo_OOB_FAKE_RECEPTACLE = []
        couldnt_place = []
        for obj in object_position_list:
            if done_moved.union({t["objectName"] for t in todo_OOB_FAKE_RECEPTACLE}) == moved_pickupable_objIds:
                break

            if obj["objectName"] in done_moved:
                raise AssertionError(f"Object {obj['objectName']} already done?!")

            if obj["objectName"] in moved_pickupable_objIds:
                assert obj["receptacle"] is not None

                if obj["receptacle"] == "OOB_FAKE_RECEPTACLE":
                    todo_OOB_FAKE_RECEPTACLE.append(obj)
                    continue

                self.PickupObject(
                    robot={"name": "robot1"}, pick_obj=obj["objectName"], render_after=False, telekinesis=True
                )
                try:
                    self.PutObject(
                        robot={"name": "robot1"},
                        put_obj=obj["objectName"],
                        recp=obj["receptacle"],
                        render_after=False,
                        telekinesis=True,
                    )
                except PutObjectNoPosition as e:
                    print("PutObject failed during StepSemiStaticObjects, falling back to spawn coords")
                    coords = self.controller.step(
                        action="GetSpawnCoordinatesAboveReceptacle", objectId=obj["receptacle"], anywhere=True
                    ).metadata["actionReturn"]
                    coords = np.array([dict2xyztuple(x) for x in coords])
                    coords = trim_spawn_coordinates(coords)

                    # In this step, we look at the objects that WERE on the receptacle
                    OLD_SSSD = self.sss_data.unstep() if self.first_sssd_step_done else self.sss_data
                    if OLD_SSSD is None:
                        other_objects_on_receptacle = []
                    else:
                        receptacle_id = OLD_SSSD.receptacles_in_scene.index(obj["receptacle"])
                        other_objects_on_receptacle = list(
                            map(int, (OLD_SSSD.self_at_current_time._assignment[:, receptacle_id] == 1).nonzero()[0])
                        )
                        other_objects_on_receptacle = [
                            x
                            for x in other_objects_on_receptacle
                            if x != OLD_SSSD.pickupables_in_scene.index(obj["objectName"])
                        ]
                        # In this step, we remove the objects that will no longer be on the receptacle after this step
                        if self.first_sssd_step_done:
                            objects_that_are_still_there = list(
                                map(
                                    int,
                                    (self.sss_data.self_at_current_time._assignment[:, receptacle_id] == 1).nonzero()[0],
                                )
                            )
                            objects_that_are_still_there = [
                                x
                                for x in objects_that_are_still_there
                                if x != OLD_SSSD.pickupables_in_scene.index(obj["objectName"])
                            ]
                            other_objects_on_receptacle = list(
                                set(other_objects_on_receptacle).intersection(set(objects_that_are_still_there))
                            )
                    if OLD_SSSD is not None:
                        other_objects_on_receptacle = [
                            OLD_SSSD.pickupables_in_scene[i] for i in other_objects_on_receptacle
                        ]
                    if (
                        not self.first_sssd_step_done or OLD_SSSD is None
                    ):  # edge case: at timestep 0, actually nothing should be on the receptacle right now (except if another loop iter placed it there)
                        other_objects_on_receptacle = []
                    # Add the objects that we moved at this step that are now on the receptacle (should actually coincide with the intersection step!)
                    for other_obj in done_moved:
                        if object_position_dict[other_obj]["receptacle"] == obj["receptacle"]:
                            other_objects_on_receptacle.append(other_obj)

                    positions_of_other_objects_on_receptacle = []
                    for i in range(len(other_objects_on_receptacle)):
                        other_obj = other_objects_on_receptacle[i]
                        for x in couldnt_place:
                            if x["objectName"] == other_obj:
                                positions_of_other_objects_on_receptacle.append(x["position"])
                                other_objects_on_receptacle[i] = None
                                break
                    positions_of_other_objects_on_receptacle += [
                        obj["position"]
                        for obj in self.controller.last_event.metadata["objects"]
                        if obj["objectId"] in other_objects_on_receptacle
                    ]

                    positions_of_other_objects_on_receptacle = jnp.array(
                        list(map(dict2xyztuple, positions_of_other_objects_on_receptacle))
                    )
                    sampler = ProcThorObject.create_from_spawncoords_only(coords)

                    sampler_potential = sampler.make_potential_field(positions_of_other_objects_on_receptacle)
                    self.key, subkey = jax.random.split(self.key)
                    samples = sampler.sample_from_surface_with_potential_field(
                        subkey, sampler_potential, num_samples=10
                    )
                    sample = samples[0]

                    find_floor = {k: v for k, v in object_metadata_dict.items() if "floor" in k.lower()}
                    self.PutObject(
                        robot={"name": "robot1"},
                        put_obj=obj["objectName"],
                        recp=list(find_floor.keys())[0],
                        render_after=False,
                        telekinesis=True,
                    )
                    assert self.controller.last_event.metadata["errorMessage"] == ""

                    todo_obj = copy.deepcopy(obj)
                    todo_obj["position"] = {k: float(v) for k, v in xyztuple2dict(sample).items()}
                    couldnt_place.append(todo_obj)

                done_moved.add(obj["objectName"])

        self.first_sssd_step_done = True
        # if len(todo_OOB_FAKE_RECEPTACLE) == 0 and len(couldnt_place) == 0:
        #    if render:
        #        return self.render()

        todos = todo_OOB_FAKE_RECEPTACLE + couldnt_place

        todo_object_position_list, _ = self.Get_StepSemiStaticObjects_Descriptor(tick=False, force_sss_none=True)
        todo_object_position_list = copy.deepcopy(todo_object_position_list)
        TEMP = {obj["objectName"]: obj for obj in todo_object_position_list}
        for o in todos:
            TEMP[o["objectName"]] = o
        todo_object_position_list = list(TEMP.values())
        self.controller.step(action="SetObjectPoses", objectPoses=todo_object_position_list)

        final_collection_phase = []
        for i, obj in enumerate(couldnt_place):
            self.PickupObject(
                robot={"name": "robot1"}, pick_obj=obj["objectName"], render_after=False, telekinesis=True
            )
            old_pos = None
            for i in range(50):
                time.sleep(0.001)
                self.controller.step(action="MoveHeldObject", ahead=0, right=0, up=-0.01, forceVisible=False)
                if copy.deepcopy({obj["objectId"]: obj for obj in self.controller.last_event.metadata["objects"]})[
                    obj["objectName"]
                ]["breakable"]:
                    assert not copy.deepcopy(
                        {obj["objectId"]: obj for obj in self.controller.last_event.metadata["objects"]}
                    )[obj["objectName"]]["isBroken"]
                objects = copy.deepcopy(
                    {obj["objectId"]: obj for obj in self.controller.last_event.metadata["objects"]}
                )
                if old_pos is not None:
                    if abs(old_pos["y"] - objects[obj["objectName"]]["position"]["y"]) < 0.01:
                        break
                old_pos = objects[obj["objectName"]]["position"]
            time.sleep(0.01)
            self.controller.step(action="DropHandObject", forceAction=True)

            tmp = copy.deepcopy(obj)
            tmp["position"] = old_pos
            final_collection_phase.append(tmp)
            if copy.deepcopy({obj["objectId"]: obj for obj in self.controller.last_event.metadata["objects"]})[
                obj["objectName"]
            ]["breakable"]:
                assert not copy.deepcopy(
                    {obj["objectId"]: obj for obj in self.controller.last_event.metadata["objects"]}
                )[obj["objectName"]]["isBroken"]

        current_obj_positions = copy.deepcopy(
            {obj["objectId"]: obj for obj in self.controller.last_event.metadata["objects"]}
        )
        for obj in couldnt_place:
            if current_obj_positions[obj["objectName"]]["position"]["y"] <= 0.1:
                print(f"Object {obj['objectName']} was left on the floor! Next to the correct receptacle.")

        """
        couldnt_place_again = []
        for obj in couldnt_place:
            if current_obj_positions[obj["objectName"]]["position"]["y"] <= 0.1:
                couldnt_place_again.append(obj)
                #raise AssertionError("An object we couldn't place was left on the floor.")

        if len(couldnt_place_again) > 0:
            todo_object_position_list, _ = self.Get_StepSemiStaticObjects_Descriptor(tick=False, force_sss_none=True)
            todo_object_position_list = copy.deepcopy(todo_object_position_list)
            TEMP = {obj["objectName"]: obj for obj in todo_object_position_list}
            for o in couldnt_place_again:
                TEMP[o["objectName"]] = o
            todo_object_position_list = list(TEMP.values())
            self.controller.step(action="SetObjectPoses", objectPoses=todo_object_position_list)
            """

        # if render:
        #    return self.render()

    @property
    def last_action(self):
        return self.done_actions[-1]

    def get_diff_history(self):
        first = self.object_containers[0].as_llmjson()
        return first + "\n\n" + "\n\n".join(self.past_diffs)

    def set_task_description(self, task_description):
        self.task_description = task_description

    def _get_robot_name(self, robot):
        return robot["name"]

    def _get_robot_id(self, robot):
        return int(self._get_robot_name(robot)[-1]) - 1

    def _get_object_id(self, target_obj):
        if target_obj is None:
            return ""

        objs = list(set([obj["objectId"] for obj in self.controller.last_event.metadata["objects"]]))

        for obj in objs:
            if obj == target_obj:
                return target_obj

        for obj in objs:
            if target_obj.lower() in obj.lower():
                return obj

        sw_obj_id = target_obj

        for obj in objs:
            match = re.match(target_obj, obj)
            if match is not None:
                sw_obj_id = obj
                break  # find the first instance

        if obj == "robot1" or obj == "robot0":
            return ""

        return sw_obj_id

    def _get_robot_location_dict(self, robot):
        pos = get_robot_position_from_controller(self.controller, robot)
        metadata = self.controller.last_event.events[self._get_robot_id(robot)].metadata
        robot_location = {
            "x": pos[0],
            "y": pos[1],
            "z": pos[2],
            "rotation": metadata["agent"]["rotation"]["y"],
            "horizon": metadata["agent"]["cameraHorizon"],
        }
        return robot_location

    def _get_object_aabb(self, object_id):
        return {
            obj["objectId"]: obj["axisAlignedBoundingBox"] for obj in self.controller.last_event.metadata["objects"]
        }.get(object_id, {})

    # ========= SKILLS =========

    def MoveAhead(self, robot, magnitude, render_after=True):
        self.controller.step(dict(action="MoveAhead", moveMagnitude=magnitude, agentId=self._get_robot_id(robot)))
        if render_after:
            self.render()

    def MoveBack(self, robot, magnitude, render_after=True):
        self.controller.step(dict(action="MoveBack", moveMagnitude=magnitude, agentId=self._get_robot_id(robot)))
        if render_after:
            self.render()

    def MoveLeft(self, robot, magnitude, render_after=True):
        self.controller.step(dict(action="MoveLeft", moveMagnitude=magnitude, agentId=self._get_robot_id(robot)))
        if render_after:
            self.render()

    def MoveRight(self, robot, magnitude, render_after=True):
        self.controller.step(dict(action="MoveRight", moveMagnitude=magnitude, agentId=self._get_robot_id(robot)))
        if render_after:
            self.render()

    def RotateLeft(self, robot, degrees, render_after=True):
        self.controller.step(dict(action="RotateLeft", degrees=degrees, agentId=self._get_robot_id(robot)))
        if render_after:
            self.render()

    def RotateRight(self, robot, degrees, render_after=True):
        self.controller.step(dict(action="RotateRight", degrees=degrees, agentId=self._get_robot_id(robot)))
        if render_after:
            self.render()

    def LookUp(self, robot, render_after=True):
        self.controller.step(action="LookUp", agentId=self._get_robot_id(robot))
        if render_after:
            self.render()

    def LookDown(self, robot, render_after=True):
        self.controller.step(action="LookDown", agentId=self._get_robot_id(robot))
        if render_after:
            self.render()

    def imshow(self, first_view_frame, top_down_frame):
        cv2.imshow("first_view", cv2.cvtColor(first_view_frame, cv2.COLOR_RGB2BGR))
        cv2.imshow("top_view", cv2.cvtColor(top_down_frame, cv2.COLOR_RGB2BGR))

    def get_privileged_apn(self):
        visible_objects = self.controller.humanviewing.get_latest_visible_instances(
            self.sss_data.receptacle_names + self.sss_data.pickupable_names
        )

        def get_aabb(obj, OBJECT_METADATA, force_aabb_none=False):
            nominal_aabb = OBJECT_METADATA[obj]["axisAlignedBoundingBox"]

            aabb_size = dict2xyztuple(nominal_aabb["size"])
            aabb_center = dict2xyztuple(nominal_aabb["center"])
            aabb_cornerPoints = nominal_aabb["cornerPoints"]

            if aabb_cornerPoints is None or force_aabb_none:
                ret = oobb_to_aabb(OBJECT_METADATA[obj]["objectOrientedBoundingBox"]["cornerPoints"])

                aabb_size = dict2xyztuple(ret["size"])
                aabb_center = dict2xyztuple(ret["center"])
                aabb_cornerPoints = ret["cornerPoints"].tolist()

            return aabb_center, aabb_size, aabb_cornerPoints

        import jax.numpy as jnp
        import numpy as np  # Import standard numpy
        import jax

        def filter_visible_objects_by_apn_dist_thresh(visible_objects):
            # 1. Handle empty input edge case immediately
            if not visible_objects:
                return []

            agent_pos = jnp.array(
                get_robot_position_from_controller(self.controller, None)
            )

            OBJECT_METADATA = {
                o["objectId"]: o
                for o in self.controller.last_event.metadata["objects"]
            }

            centers = []
            sizes = []

            for obj in visible_objects:
                center, size, _ = get_aabb(obj, OBJECT_METADATA)
                centers.append(center)
                sizes.append(size)

            AABB_CENTERS = jnp.asarray(centers)
            AABB_SIZES = jnp.asarray(sizes)

            # 2. Vectorized Distance Calculation (Ideally, keep this logic pure)
            def point_to_aabb_distance(center, size, point):
                half_size = size * 0.5
                min_corner = center - half_size
                max_corner = center + half_size

                delta = jnp.maximum(min_corner - point, 0.0) + \
                        jnp.maximum(point - max_corner, 0.0)

                return jnp.linalg.norm(delta)

            # Note: Explicitly passing agent_pos avoids closure issues if JIT-ing later
            distances = jax.vmap(point_to_aabb_distance, in_axes=(0, 0, None))(
                AABB_CENTERS,
                AABB_SIZES,
                agent_pos
            )

            mask = distances < self.apn_dist_thresh

            # 3. Optimization: Move mask to CPU once as a standard boolean numpy array
            # This prevents slow item-by-item device transfers during the zip
            mask_np = np.array(mask)

            return [v for m, v in zip(mask_np, visible_objects) if m]
        if self.apn_dist_thresh < float("inf"):
            visible_objects = filter_visible_objects_by_apn_dist_thresh(visible_objects)
       # import jax.numpy as jnp

        PROTOTYPE: GeneratedSemiStaticData = self.sss_data.get_singletimestamp_prototype()

        # ['assignment', 'position', 'rotation', 'timestamp', 'aabb_center', 'aabb_cornerPoints', 'aabb_size', 'oobb_cornerPoints']
        def write_in_proto(key, p_index, r_index, value):
            if isinstance(value, tuple) or isinstance(value, list):
                value = jnp.array(value)
            if r_index is None:
                if p_index is None:
                    assert PROTOTYPE[key].shape == tuple()
                    return PROTOTYPE.replace(**{key: jnp.ones_like(PROTOTYPE[key]) * value})
                return PROTOTYPE.replace(**{key: PROTOTYPE[key].at[p_index].set(value)})
            return PROTOTYPE.replace(**{key: PROTOTYPE[key].at[p_index, r_index].set(value)})

        for pickupable_index, (pickupable, active_receptacles) in enumerate(
            self.sss_data.pickupable_to_receptacle.items()
        ):

            for receptacle in self.sss_data.receptacles_in_scene:
                if receptacle in active_receptacles:
                    continue
                else:
                    PROTOTYPE = write_in_proto(
                        "_assignment", pickupable_index, self.sss_data.receptacle_names.index(receptacle), -2
                    )

            visible_active_receptacles = []
            for receptacle in active_receptacles:
                if receptacle in visible_objects:
                    visible_active_receptacles.append(receptacle)
                else:
                    PROTOTYPE = write_in_proto(
                        "_assignment", pickupable_index, self.sss_data.receptacle_names.index(receptacle), -1
                    )

            if pickupable not in visible_objects:
                for receptacle in visible_active_receptacles:
                    PROTOTYPE = write_in_proto(
                        "_assignment", pickupable_index, self.sss_data.receptacle_names.index(receptacle), 0
                    )
                continue

            if len(visible_active_receptacles) == 0:
                # print("Edge case where the object placement made a pickupable fall down to the ground due to gravity.")
                # print("Should only happen when peeking into a room, and the pickupable is visible but not the receptacle")
                continue
            elif len(visible_active_receptacles) == 1:
                CLOSEST_RECEPTACLE = visible_active_receptacles[0]
            else:
                aabb_distance = np.array(
                    [
                        compute_aabb_distance(self.controller, pickupable, vis_active_receptacle)
                        for vis_active_receptacle in visible_active_receptacles
                    ]
                )
                CLOSEST_RECEPTACLE = visible_active_receptacles[np.argmin(aabb_distance)]

            for receptacle in visible_active_receptacles:
                if receptacle == CLOSEST_RECEPTACLE:
                    PROTOTYPE = write_in_proto(
                        "_assignment", pickupable_index, self.sss_data.receptacle_names.index(receptacle), 1
                    )
                else:
                    PROTOTYPE = write_in_proto(
                        "_assignment", pickupable_index, self.sss_data.receptacle_names.index(receptacle), 0
                    )

        OBJECT_METADATA = {o["objectId"]: o for o in self.controller.last_event.metadata["objects"]}

        for i, p in enumerate(self.sss_data.pickupable_names):
            PROTOTYPE = write_in_proto("_position", i, None, dict2xyztuple(OBJECT_METADATA[p]["position"]))
            PROTOTYPE = write_in_proto("_rotation", i, None, OBJECT_METADATA[p]["rotation"]["y"])



            oobb_cornerPoints = OBJECT_METADATA[p]["objectOrientedBoundingBox"]["cornerPoints"]
            aabb_center, aabb_size, aabb_cornerPoints = get_aabb(p, OBJECT_METADATA)

            PROTOTYPE = write_in_proto("_aabb_center", i, None, aabb_center)
            PROTOTYPE = write_in_proto("_aabb_size", i, None, aabb_size)
            PROTOTYPE = write_in_proto("_aabb_cornerPoints", i, None, aabb_cornerPoints)
            PROTOTYPE = write_in_proto("_oobb_cornerPoints", i, None, oobb_cornerPoints)

        PROTOTYPE = write_in_proto("_timestamp", None, None, self.sss_data.self_at_current_time._timestamp)
        for k, v in PROTOTYPE.TimeVaryingItems():
            assert not jnp.isnan(v).any(), f"This element was NaN: {k}: {v}"

        return PROTOTYPE

    def get_pickupable_poses(self):
        pickupable_poses = {}
        for p_id in self.sss_data.pickupable_names:
            for obj_data in self.controller.last_event.metadata["objects"]:
                if obj_data["objectId"] == p_id:
                    pos = obj_data["position"]
                    rot = obj_data["rotation"]
                    pickupable_poses[p_id] = {"position": pos, "rotation": rot}
        return pickupable_poses

    def get_receptacles_poses(self):
        receptacle_poses = {}
        for r_id in self.sss_data.receptacle_names:
            for obj_data in self.controller.last_event.metadata["objects"]:
                if obj_data["objectId"] == r_id:
                    pos = obj_data["position"]
                    rot = obj_data["rotation"]
                    receptacle_poses[r_id] = {"position": pos, "rotation": rot}
        return receptacle_poses

    def get_receptacles_aabbs(self):
        receptacle_aabb = {}
        for r_id in self.sss_data.receptacle_names:
            for obj_data in self.controller.last_event.metadata["objects"]:
                if obj_data["objectId"] == r_id:
                    aabb = obj_data["axisAlignedBoundingBox"]
                    receptacle_aabb[r_id] = aabb
        return receptacle_aabb

    def get_agent_pose(self):
        pose = self.controller.humanviewing.get_agent_pose()
        return pose

    def render(self):
        # todo
        def render_first_person():
            # if self.rendering_use_altered_first_person:
            #    frame = self.controller.humanviewing.get_latest_altered_robot_frame()
            # else:
            frame = self.controller.humanviewing.get_latest_robot_frame()
            # if self.rendering_augment_first_person:
            #    frame = self.controller.humanviewing.get_augmented_robot_frame(frame)
            # self.controller.humanviewing.display_frame(frame)
            return frame

        def render_depth_and_semantics():
            depth_frame = self.controller.humanviewing.get_latest_depth_robot_frame()
            semantics_frame = self.controller.humanviewing.get_latest_segmented_robot_frame()
            return depth_frame, semantics_frame

        def render_visible_instances():
            if self.sss_data is None:
                return []
            instance_ids = self.controller.humanviewing.get_latest_visible_instances(
                self.sss_data.receptacle_names + self.sss_data.pickupable_names
            )
            return instance_ids

        first_view_frame = render_first_person()
        depth_frame, semantics_frame = render_depth_and_semantics()
        visible_instances = render_visible_instances()
        agent_pose = self.get_agent_pose()

        # remove the ceiling
        top_down_frame = self.controller.humanviewing.get_latest_topdown_frame()

        self.last_metadata = {
            "rgb_first_view": first_view_frame,
            "rgb_top_down_view": top_down_frame,
            "semantics_view": semantics_frame,
            "depth_view": depth_frame,
            "agent_pose": agent_pose,
            "intrinsics": self.camera_intrinsics,
        }
        self.save_step()

        if self.sss_data is None:
            pass
        else:
            point_apn = self.get_privileged_apn()
            if self.privileged_apn is None:
                self.privileged_apn = point_apn
            else:
                self.privileged_apn = self.privileged_apn.concat(point_apn)
        # x = jnp.unique(jnp.arange(10), return_counts=True)
        # self.privileged_apn.convert_to_thin_assignment_tensor().convert_to_wide_assignment_tensor()

        if self.human_render:
            self.imshow(first_view_frame, top_down_frame)
            cv2.waitKey(1)

        ret = copy.deepcopy(self.last_metadata)
        if self.sss_data is not None:
            ret["point_apn"] = point_apn
        return ret

    def GoToAllInstances(self, robot, render_after=True):
        # Sort by geodesic distance (navigation distance accounting for walls)
        pickupable_position = {
            p_id: np.array(dict2xyztuple(data["position"]))
            for p_id, data in self.get_pickupable_poses().items()
            if not self.sss_data.is_this_pickupable_in_the_OOB_FAKE_RECEPTACLE(p_id)
        }
        receptacles_position = {
            r_id: np.array(dict2xyztuple(data["position"])) for r_id, data in self.get_receptacles_poses().items()
        }
        instances_position = {**pickupable_position, **receptacles_position}
        agent_pos = np.array(get_robot_position_from_controller(self.controller, self._get_robot_id(robot)))

        # Compute geodesic distances using the reachability graph via astar
        geodesic_distances = {}
        filtered_graph = self.full_reachability_graph.filter_(
            self.controller.last_event.metadata["objects"],
            mindist_to_obj=self.full_reachability_graph.set_mindist_to_obj,
        )

        for obj_id, obj_pos in instances_position.items():
            obj_size = np.array(get_object_size_from_controller(self.controller, obj_id))
            _, distances = filtered_graph.shunt_to_bbox(obj_pos, obj_size)

            # If objects are placed in objects that are big, like a bed, then they might be far from the nav graph
            # Yet, they may be observable! So we allow a threshold twice as big as usual here.
            if (distances > self.goal_thresh * 2).all():
                raise ValueError(
                    f"Object {obj_id} is too far from the navigation graph. Consider using other scene or increasing threshold! - "
                    f"Distance: {distances} > Threshold: {self.goal_thresh}m"
                )
            try:
                # Use astar to get path, then count its length for geodesic distance
                path = list(astar(agent_pos, obj_pos, obj_size, filtered_graph))
                geodesic_distances[obj_id] = len(path)
            except (nx.NetworkXNoPath, nx.NodeNotFound, AssertionError):
                # Fallback to infinity if no path exists (e.g., unreachable objects)
                geodesic_distances[obj_id] = float("inf")
                raise ValueError(f"No path found to object {obj_id} at position {obj_pos}")

        # Sort by geodesic distance
        sorted_instances = sorted(geodesic_distances.items(), key=lambda item: item[1])
        total_instances = len(sorted_instances)
        print(f"\n{'='*60}")
        print(f"GoToAllInstances: Visiting {total_instances} instances")
        print(f"{'='*60}")

        for idx, (r_id, _) in enumerate(sorted_instances, 1):
            percentage = (idx / total_instances) * 100
            bar_length = 40
            filled_length = int(bar_length * idx // total_instances)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            print(
                f"\rProgress: [{bar}] {idx}/{total_instances} ({percentage:.1f}%) - Current: {r_id[:30]:<30}",
                end="",
                flush=True,
            )
            self.GoToObject(robot, r_id, render_after=render_after, filtered_graph=filtered_graph)

        print(f"\n{'='*60}")
        print(f"Completed! Visited all {total_instances} instances")
        print(f"{'='*60}\n")

    def GoToNode(self, robot, waypoint: Tuple[float, float, float], size = None, render_after=True,  max_path_length=None, filtered_graph=None, precomputed_path_nodes=None) -> Tuple[bool, List[Tuple[float, float, float]], float, float]:
        node = self.full_reachability_graph.shunt(waypoint)
        waypoint_size = size if size is not None else (0.1, 0.1, 0.1)
        return self._GoTo(robot, node, waypoint_size, None, render_after, max_path_length=max_path_length, filtered_rg=filtered_graph, precomputed_path_nodes=precomputed_path_nodes)

    def GoToObject(self, robot, dest_obj, render_after=True, max_path_length=None, filtered_graph=None, precomputed_path_nodes=None) -> Tuple[bool, List[Tuple[float, float, float]], float, float]:
        #self.SPLMetadata(robot, dest_obj)

        dest_obj_id = self._get_object_id(dest_obj)
        dest_obj_pos = get_object_position_from_controller(self.controller, dest_obj_id)
        dest_obj_size = get_object_size_from_controller(self.controller, dest_obj_id)
        return self._GoTo(robot, dest_obj_pos, dest_obj_size, dest_obj_id, render_after, max_path_length=max_path_length, filtered_rg=filtered_graph, precomputed_path_nodes=precomputed_path_nodes)

    def get_optimal_path(self, robot, dest_obj, filtered_rg=None):
        dest_obj_id = self._get_object_id(dest_obj)
        dest_obj_pos = get_object_position_from_controller(self.controller, dest_obj_id)
        dest_obj_size = get_object_size_from_controller(self.controller, dest_obj_id)
        return self._GoTo(robot, dest_obj_pos, dest_obj_size, dest_obj_id, render_after=False, max_path_length=None, filtered_rg=filtered_rg, noop_return_path_nodes_instead=True)

    def DidObjectMove(self, target_pickupable: str, source_tick: int, target_tick: int) -> bool:
        assert target_tick >= source_tick, "Target tick must be greater than or equal to source tick."
        source_data = self.sss_data.take_by_global_timestep(source_tick, source_tick + 1)
        target_data = self.sss_data.take_by_global_timestep(target_tick, target_tick + 1)
        pickupable_index = self.sss_data.pickupable_names.index(target_pickupable)
        did_move = (source_data._assignment != target_data._assignment)[:, pickupable_index, :].any()
        return did_move

    def SPLMetadata(self, robot, target_pickupable):
        assert target_pickupable != "OOB_FAKE_RECEPTACLE"

        filtered_rg = self.full_reachability_graph.filter_(
            self.controller.last_event.metadata["objects"],
            mindist_to_obj=self.full_reachability_graph.set_mindist_to_obj,
        )

        optimal_path_considering_pickupable = self.get_optimal_path(robot, target_pickupable, filtered_rg)
        try:
            gt_receptacle = self.sss_data.pickupable_selves_at_current_time[target_pickupable].current_receptacle_for_this_pickupable(target_pickupable)
            IS_OUTSIDE_MAP = gt_receptacle == "OOB_FAKE_RECEPTACLE"
            if gt_receptacle == "OOB_FAKE_RECEPTACLE":
                raise KeyError()
            assert isinstance(gt_receptacle, str)
            optimal_path_considering_gt_receptacle = self.get_optimal_path(robot, gt_receptacle, filtered_rg)
        except KeyError as e:
            print("Agent tried to get the SPL metadata for an invalid query; forcing the target to `target_pickupable` instead.")
            optimal_path_considering_gt_receptacle = optimal_path_considering_pickupable
            gt_receptacle = target_pickupable

        def metrics(path):
            if IS_OUTSIDE_MAP:
                euclidean_distance = self.full_reachability_graph.grid_size
            else:
                euclidean_distance = geodesic_distance_on_path_nodes(path, self.full_reachability_graph.grid_size)

            return {
                "num_nodes": len(path) if not IS_OUTSIDE_MAP else 1,
                "euclidean_distance": euclidean_distance,
                "object_absent": IS_OUTSIDE_MAP,
            }
        return metrics(optimal_path_considering_pickupable), metrics(optimal_path_considering_gt_receptacle)

    def RotateToAngle(self, robot, angle: float, render_after=True):
        if angle < 0:
            return self.RotateLeft(robot, abs(angle), render_after=render_after)
        else:
            return self.RotateRight(robot, abs(angle), render_after=render_after)
        
    def RotateToNode(self, robot, node, robot_location=None, tolerance: float = 5.0):
        # align the robot once goal is reached
        # compute angle between robot heading and object
        if robot_location is None:
            robot_location = self._get_robot_location_dict(robot)

        robot_object_vec = [node[0] - robot_location["x"], node[2] - robot_location["z"]]
        y_axis = [0, 1]
        unit_y = y_axis / np.linalg.norm(y_axis)
        unit_vector = robot_object_vec / np.linalg.norm(robot_object_vec)

        angle = math.atan2(np.linalg.det([unit_vector, unit_y]), np.dot(unit_vector, unit_y))
        angle = 360 * angle / (2 * np.pi)
        angle = (angle + 360) % 360
        rot_angle = angle - robot_location["rotation"]
        rot_angle = ((rot_angle + 180) % 360) - 180

        # If rotation is too small, skip this rotation
        if abs(rot_angle) < tolerance:
            return 0.0

        if rot_angle > 0:
            self.RotateRight(robot, abs(rot_angle), render_after=True)
        else:
            self.RotateLeft(robot, abs(rot_angle), render_after=True)
        # Return magnitude of rotation
        return abs(rot_angle)

    def _get_distance_to_target(
            self,
            robot,
            target_pos: Tuple[float, float, float],
            target_size: Tuple[float, float, float]
    ) -> float:
        """Calculates distance from robot to the target bounding box."""
        robot_id = self._get_robot_id(robot)
        robot_pos = get_robot_position_from_controller(self.controller, robot_id)

        # [0.6, 0.95, 0.6] appears to be the hardcoded robot bbox size from the original code
        return bbox_dist(
            np.array(robot_pos),
            np.array([0.6, 0.95, 0.6]),
            np.array(target_pos),
            np.array(target_size),
        )

    def is_target_visible(self, target_id: str) -> bool:
        """Checks if the specific object ID is visible to the controller."""
        if target_id is None:
            return True
        return get_object_from_controller(self.controller, target_id)["visible"]

    def _perform_unstuck_maneuver(self, robot) -> Tuple[float, float]:
        """Executes a random action to dislodge the robot and returns movement metrics."""
        actions = ["action_1", "action_2", "action_3", "action_4"]
        act = random.choice(actions)
        angle = random.uniform(15, 90)
        mag = random.uniform(0.05, 0.25)

        print(f"Robot appears stuck; taking random action: {act}")

        dist_moved = 0.0
        rot_done = 0.0

        if act == "action_1":
            self.RotateLeft(robot, angle, render_after=True)
            self.MoveAhead(robot, mag, render_after=True)
            rot_done += angle
            dist_moved += mag
        elif act == "action_2":
            self.RotateRight(robot, angle, render_after=True)
            self.MoveAhead(robot, mag, render_after=True)
            rot_done += angle
            dist_moved += mag
        elif act == "action_3":
            self.MoveLeft(robot, mag, render_after=True)
            rot_done += angle
        elif act == "action_4":
            self.MoveRight(robot, mag, render_after=True)
            rot_done += angle

        return dist_moved, rot_done

    def _GoTo(
            self,
            robot,
            pos: Tuple[float, float, float],
            size: Tuple[float, float, float],
            id: str,
            render_after=True,
            noop_return_path_nodes_instead=False,
            max_path_length=None,
            filtered_rg=None,
            precomputed_path_nodes=None
    ) -> Tuple[bool, List[Tuple[float, float, float]], float, float, object]:
        if precomputed_path_nodes is None:
            if not noop_return_path_nodes_instead:
                self.LookUpDownAtNode(robot, None, reset_yaw_instead=True)

        target_name = f"Object: {id}" if id is not None else f"Node: {pos}"
        print(f"Going to {target_name}")

        # 1. Initialize Reachability Graph
        if filtered_rg is None and precomputed_path_nodes is None:
            filtered_rg = self.full_reachability_graph.filter_(
                self.controller.last_event.metadata["objects"],
                mindist_to_obj=self.full_reachability_graph.set_mindist_to_obj,
            )

        cur_rob_loc = self._get_robot_location_dict(robot)

        # 3. Pathfinding (Call A* exactly once)
        if precomputed_path_nodes is not None:
            path_nodes = precomputed_path_nodes
        else:
            path_nodes: List = astar(
                cur_rob_loc,
                pos,
                size,
                filtered_rg
            )

        # If requested, return nodes immediately without moving
        if noop_return_path_nodes_instead:
            return path_nodes

        # 2. Early Exit Check: Are we already there?
        is_done = len(path_nodes) <= 1 #self.__GoTo_check_if_navigation_done(robot, id, pos, size)
        #is_visible = self.is_target_visible(id)

        if is_done:# and is_visible:
            print(f"Was going to {target_name}, but already closeby. Adjusting camera only.")
        else:
            # 4. Execute Path
            unchanged_steps = 0
            MAX_STUCK_STEPS = 1
            STUCK_EPS = 1e-3
            num_nodes_used = 0

            while len(path_nodes) >= 1:
                node = path_nodes.pop(0)
                # Check max length constraint
                if max_path_length is not None and num_nodes_used >= max_path_length:
                    break

                self.nav_metrics["steps"] += 1
                num_nodes_used += 1

                # Determine movement requirements
                current_loc_tuple = dict2xyztuple(cur_rob_loc)
                move_magnitude = np.linalg.norm(np.array(current_loc_tuple) - np.array(node))

                # Rotate and Move
                rot_amount = self.RotateToNode(robot, node, cur_rob_loc, tolerance=5.0)
                self.nav_metrics["rot_steps"].append(rot_amount)

                self.MoveAhead(robot, move_magnitude, render_after=True)

                # Metric updates
                new_loc_dict = self._get_robot_location_dict(robot)
                new_loc_tuple = dict2xyztuple(new_loc_dict)

                dist_moved = np.linalg.norm(np.array(new_loc_tuple) - np.array(current_loc_tuple))
                self.nav_metrics["move_steps"].append(dist_moved)

                dist_to_goal_val = self._get_distance_to_target(robot, pos, size)
                print(f"Going to {target_name}, euclidean distance: {dist_to_goal_val}, geodesic distance: {geodesic_distance_on_path_nodes(path_nodes, self.full_reachability_graph.grid_size)}")

                # 5. Stuck Detection
                # Check if actual position changed significantly
                if np.linalg.norm(np.array(new_loc_tuple) - np.array(current_loc_tuple)) < STUCK_EPS:
                    unchanged_steps += 1
                else:
                    unchanged_steps = 0

                cur_rob_loc = new_loc_dict

                if unchanged_steps >= MAX_STUCK_STEPS:
                    print(f"Agent stuck for {unchanged_steps} steps. Attempting random maneuver.")
                    _, u_rot = self._perform_unstuck_maneuver(robot)

                    current_loc = self._get_robot_location_dict(robot)
                    dist_moved = np.linalg.norm(np.array(dict2xyztuple(cur_rob_loc)) - np.array(dict2xyztuple(current_loc)))
                    cur_rob_loc = current_loc
                    self.nav_metrics["move_steps"].append(dist_moved)

                    self.nav_metrics["rot_steps"].append(u_rot)
                    unchanged_steps = 0
                    path_nodes: List = astar(
                        cur_rob_loc,
                        pos,
                        size,
                        filtered_rg
                    )

        # 6. Final Adjustments
        if id is not None and max_path_length is None:
            self.LookAtObj(robot, id)
        elif not self.is_target_visible(id) and max_path_length is None:
            final_rot = self.RotateToNode(robot, pos, tolerance=0.0)
            self.nav_metrics["rot_steps"].append(final_rot)

        if len(path_nodes) <= 1:
            print(f"Reached: {target_name}")
        print(
            f"Iterations: {self.nav_metrics['steps']}, "
            f"Total Dist: {sum(self.nav_metrics['move_steps'])}, "
            f"Total Rot: {sum(self.nav_metrics['rot_steps'])}"
        )
        self.keyframes.add(self._step - 1)

        # Return graph in case we are in rollout mode
        return len(path_nodes) <= 1, path_nodes, self._get_distance_to_target(robot, pos, size), geodesic_distance_on_path_nodes(path_nodes, self.full_reachability_graph.grid_size), filtered_rg

    def LookUpDownAtNode(self, robot, pos, reset_yaw_instead=False):
        # todo make this its own function and call it after every object interaction...
        robot_location = self._get_robot_location_dict(robot)

        if reset_yaw_instead:
            for NUM_TIRES in range(10):
                robot_location = self._get_robot_location_dict(robot)
                current_horizon = robot_location["horizon"]
                if abs(current_horizon - 30) < 5:
                    return

                if current_horizon < 30:
                    self.LookDown(robot, render_after=True)
                else:
                    self.LookUp(robot, render_after=True)
            return

        dy = pos[1] - robot_location["y"]
        # Compute yaw rotation
        dx = pos[0] - robot_location["x"]
        dz = pos[2] - robot_location["z"]

        horizontal_dist = math.sqrt(dx ** 2 + dz ** 2)
        pitch = math.degrees(math.atan2(dy, horizontal_dist))

        # Adjust camera pitch
        current_horizon = robot_location["horizon"]

        # self._lock_robot(robot)
        if pitch > current_horizon:
            self.LookUp(robot, render_after=True)
        else:
            self.LookDown(robot, render_after=True)

    def LookAtObj(self, robot, dest_obj, lock_yaw=False):
        dest_obj_id = self._get_object_id(dest_obj)
        dest_obj_pos = get_object_position_from_controller(self.controller, dest_obj_id)
        dest_obj_size = get_object_size_from_controller(self.controller, dest_obj_id)

        final_rot = self.RotateToNode(robot, dest_obj_pos, tolerance=0.0)
        self.nav_metrics["rot_steps"].append(final_rot)

        if lock_yaw:
            return

        def is_dest_obj_visible():
            if dest_obj_id is None:
                return True
            else:
                return get_object_from_controller(self.controller, dest_obj_id)["visible"]

        NUM_TRIES = 0
        MAX_NUM_TRIES = 1
        while not is_dest_obj_visible() and NUM_TRIES < MAX_NUM_TRIES:
            self.LookUpDownAtNode(robot, dest_obj_pos)
            NUM_TRIES += 1
            if NUM_TRIES >= MAX_NUM_TRIES:
                break


    def PickupObject(self, robot, pick_obj, render_after=True, telekinesis=False):
        if not telekinesis:
            self.LookAtObj(robot, pick_obj)
        multi_agent_event = self.controller.step(
            action="PickupObject",
            objectId=self._get_object_id(pick_obj),
            agentId=self._get_robot_id(robot),
            forceAction=True,
            manualInteract=telekinesis,
        )
        if multi_agent_event.metadata["errorMessage"] != "":
            raise Exception(multi_agent_event.metadata["errorMessage"])
        if render_after:
            self.render()

    def PutObject(self, robot, put_obj, recp, render_after=True, telekinesis=False):
        if not telekinesis:
            self.LookAtObj(robot, recp)
        multi_agent_event = self.controller.step(
            action="PutObject", objectId=self._get_object_id(recp), agentId=self._get_robot_id(robot), forceAction=True
        )
        if multi_agent_event.metadata["errorMessage"] != "":
            print(f"The object {put_obj} could not be put into {recp}.")

            if multi_agent_event.metadata["errorMessage"] == "No valid positions to place object found":
                raise PutObjectNoPosition(multi_agent_event.metadata["errorMessage"])
            raise Exception(multi_agent_event.metadata["errorMessage"])

        if render_after:
            self.render()

    def SwitchOn(self, robot, sw_obj, render_after=True):
        self.LookAtObj(robot, sw_obj)
        multi_agent_event = self.controller.step(
            action="ToggleObjectOn",
            objectId=self._get_object_id(sw_obj),
            agentId=self._get_robot_id(robot),
            forceAction=True,
        )
        if multi_agent_event.metadata["errorMessage"] != "":
            raise Exception(multi_agent_event.metadata["errorMessage"])
        if render_after:
            self.render()

    def SwitchOff(self, robot, sw_obj, render_after=True):
        self.LookAtObj(robot, sw_obj)
        multi_agent_event = self.controller.step(
            action="ToggleObjectOff",
            objectId=self._get_object_id(sw_obj),
            agentId=self._get_robot_id(robot),
            forceAction=True,
        )
        if multi_agent_event.metadata["errorMessage"] != "":
            raise Exception(multi_agent_event.metadata["errorMessage"])
        if render_after:
            self.render()

    def OpenObject(self, robot, sw_obj, render_after=True):

        multi_agent_event = self.controller.step(
            action="OpenObject",
            objectId=self._get_object_id(sw_obj),
            agentId=self._get_robot_id(robot),
            forceAction=True,
        )
        if multi_agent_event.metadata["errorMessage"] != "":
            raise Exception(multi_agent_event.metadata["errorMessage"])
        if render_after:
            self.render()

    def CloseObject(self, robot, sw_obj, render_after=True):
        multi_agent_event = self.controller.step(
            action="CloseObject",
            objectId=self._get_object_id(sw_obj),
            agentId=self._get_robot_id(robot),
            forceAction=True,
        )
        if multi_agent_event.metadata["errorMessage"] != "":
            raise Exception(multi_agent_event.metadata["errorMessage"])
        if render_after:
            self.render()

    def BreakObject(self, robot, sw_obj, render_after=True):
        multi_agent_event = self.controller.step(
            action="BreakObject",
            objectId=self._get_object_id(sw_obj),
            agentId=self._get_robot_id(robot),
            forceAction=True,
        )
        if multi_agent_event.metadata["errorMessage"] != "":
            raise Exception(multi_agent_event.metadata["errorMessage"])
        if render_after:
            self.render()

    def SliceObject(self, robot, sw_obj, render_after=True):

        multi_agent_event = self.controller.step(
            action="SliceObject",
            objectId=self._get_object_id(sw_obj),
            agentId=self._get_robot_id(robot),
            forceAction=True,
        )
        if multi_agent_event.metadata["errorMessage"] != "":
            raise Exception(multi_agent_event.metadata["errorMessage"])
        if render_after:
            self.render()

    def CleanObject(self, robot, sw_obj, render_after=True):
        raise NotImplemented()
        self.push_action(
            {"action": "CleanObject", "objectId": self._get_object_id(sw_obj), "agent_id": self._get_robot_id(robot)}
        )

    def ThrowObject(self, robot, sw_obj, render_after=True):
        multi_agent_event = self.controller.step(
            action="ThrowObject", moveMagnitude=7, agentId=self._get_robot_id(robot), forceAction=True
        )
        if multi_agent_event.metadata["errorMessage"] != "":
            raise Exception(multi_agent_event.metadata["errorMessage"])
        if render_after:
            self.render()

    def Done(self):
        self.push_action({"action": "Done"})
        time.sleep(1)


import numpy as np
