import copy

from semistaticsim.rendering.utils.dict2xyztup import dict2xyztuple


def get_robot_inventory(controller, agent_id):
    inventory = controller.last_event.events[agent_id].metadata["inventoryObjects"]
    inventory = [o["objectId"] for o in inventory]

    return inventory

def get_object_from_controller(controller, object_id):
    OBJECT_METADATA = {
        o["objectId"]: o
        for o in controller.last_event.metadata["objects"]
    }

    if object_id not in OBJECT_METADATA:
        print("WARNING: Object ID {} not found in controller metadata. \nWARNING: The cause could be: 1. you loaded the wrong map. 2. you requested an non-existent object. 3. ???".format(object_id))
        raise AssertionError()

    return OBJECT_METADATA[object_id]

def get_object_aabb_from_controller(controller, object_id, return_as_TupOfXyzTuple=False):
    """

    Sometimes, AABB is None in AI2Thor, because its a janky simulator from 2017 :)

    Args:
        controller:
        obj: the obj whose aabb we want

    Returns: aabb

    """

    # todo replace the StepSSS function's get_aabb by this function

    try:
        OBJECT = get_object_from_controller(controller, object_id)
    except AssertionError:
        thunk_fix_robot_pos(controller)
        OBJECT = get_object_from_controller(controller, object_id)

    nominal_aabb = OBJECT["axisAlignedBoundingBox"]
    aabb_size = dict2xyztuple(nominal_aabb["size"])
    aabb_center = dict2xyztuple(nominal_aabb["center"])
    aabb_cornerPoints = nominal_aabb["cornerPoints"]

    if aabb_cornerPoints is None:
        from semistaticsim.groundtruth.procthor_object import oobb_to_aabb
        ret = oobb_to_aabb(OBJECT["objectOrientedBoundingBox"]["cornerPoints"])

        aabb_size = dict2xyztuple(ret["size"])
        aabb_center = dict2xyztuple(ret["center"])
        aabb_cornerPoints = ret["cornerPoints"].tolist()

        aabb = {
            "cornerPoints": aabb_cornerPoints,
            "size": aabb_size,
            "center": aabb_center,
        }
    else:
        aabb = nominal_aabb

    if return_as_TupOfXyzTuple:
        return aabb_center, aabb_size, aabb_cornerPoints

    return aabb


def get_object_size_from_controller(controller, object_id):
    aabb = get_object_aabb_from_controller(controller, object_id)['size']
    return (aabb['x'], aabb['y'], aabb['z'])

import numpy as np
def compute_aabb_distance(controller, pickupable_name, receptacle_name):
    OBJECT_METADATA = {o["objectId"]: o for o in controller.last_event.metadata["objects"]}

    aabb_p = OBJECT_METADATA[pickupable_name]["axisAlignedBoundingBox"]
    aabb_r = OBJECT_METADATA[receptacle_name]["axisAlignedBoundingBox"]

    # Extract centers and half-sizes
    c_p = np.array([aabb_p["center"]["x"], aabb_p["center"]["y"], aabb_p["center"]["z"]])
    s_p = np.array([aabb_p["size"]["x"], aabb_p["size"]["y"], aabb_p["size"]["z"]]) / 2.0

    c_r = np.array([aabb_r["center"]["x"], aabb_r["center"]["y"], aabb_r["center"]["z"]])
    s_r = np.array([aabb_r["size"]["x"], aabb_r["size"]["y"], aabb_r["size"]["z"]]) / 2.0

    # Compute per-axis distances
    delta = np.abs(c_p - c_r) - (s_p + s_r)
    delta = np.maximum(delta, 0.0)  # No negative distances (overlaps → 0)

    # Euclidean distance between the boxes
    distance = np.linalg.norm(delta)
    return distance

def get_object_position_from_controller(controller, object_id):
    aabb = get_object_aabb_from_controller(controller, object_id)
    pos = aabb["center"]
    return (pos['x'], pos['y'], pos['z'])

THUNK_DIR = 1
def thunk_fix_robot_pos(controller):
    #return
    global THUNK_DIR

    # print("Thunk Fix Robot Pos Called")
    act = {
        0: "MoveAhead",
        1: "MoveBack",
        2: "MoveLeft",
        3: "MoveRight",
    }
    #time.sleep(0.001)
    controller.step(
        dict(action=act[THUNK_DIR], moveMagnitude=0.000001,
             agentId=0))  # for some reason, non-move actions tend to alter the robot position in unexpected ways. To fix this, we spoof a fake movement to reset it
    THUNK_DIR += 1
    THUNK_DIR %= 4

def get_robot_position_from_controller(controller, robot_id):
    thunk_fix_robot_pos(controller)
    #metadata = controller.last_event.events[robot_id].metadata
    metadata = controller.last_event.metadata
    pos = [metadata["agent"]["position"]["x"],
        metadata["agent"]["position"]["y"],
        metadata["agent"]["position"]["z"]]
    return pos

def get_object_list_from_controller(controller):
    objects = controller.last_event.metadata["objects"]
    objects = copy.deepcopy(objects)

    held_objects = {} # id: robot
    for i, robot_event in enumerate(controller.last_event.events):
        robot_metadata = robot_event.metadata

        inventory = robot_metadata["inventoryObjects"]

        thunk_fix_robot_pos(controller)
        robotpos = robot_metadata["agent"]['position']
        SIZE = {'x': 0.4, 'y': 1.0, 'z': 0.4}
        robotpos["x"] = robotpos["x"] + SIZE["x"] / 2
        robotpos["y"] = robotpos["y"] - SIZE["y"] / 2
        robotpos["z"] = robotpos["z"] + SIZE["z"] / 2

        robot_dict = {
            "assetId": f"", # makes robot not considered as runtime object
            "objectId": f"robot{i+1}",
            "id": i,
            "position": robotpos,
            "rotation": robot_metadata["agent"]['rotation'],
            "size": SIZE,
            "inventory": inventory,
            "ISROBOT": True
        }
        for obj in inventory:
            held_objects[obj["objectId"]] = f"robot{i+1}"

        objects.append(robot_dict)

    for obj_dict in objects:
        if obj_dict["objectId"] in held_objects:
            obj_dict["heldBy"] = held_objects[obj_dict["objectId"]]
        else:
            obj_dict["heldBy"] = None

    return objects
