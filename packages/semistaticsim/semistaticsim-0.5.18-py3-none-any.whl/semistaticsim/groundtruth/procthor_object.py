import functools
import itertools
from functools import singledispatchmethod
from typing import Dict, Any, List, Union

import jax
from flax import struct
from jax import numpy as jnp

from semistaticsim.groundtruth.constants import AFFORDANCE_NAMES
from semistaticsim.groundtruth.spoof_vmap import spoof_vmap
from semistaticsim.rendering.utils.dict2xyztup import dict2xyztuple, xyztuple2dict


def trim_spawn_coordinates(coords):
    # 1. Define how much to trim (5% from each side = 10% total removed)
    margin_percent = 0.1

    # Calculate bounds only for X and Z (indices 0 and 2)
    # We calculate full bounds, but only apply the mask to X and Z
    x_min, y_min, z_min = coords.min(axis=0)
    x_max, y_max, z_max = coords.max(axis=0)

    x_margin = (x_max - x_min) * margin_percent
    z_margin = (z_max - z_min) * margin_percent

    # Mask: Only filter based on X and Z borders
    mask = (
            (coords[:, 0] > x_min + x_margin) & (coords[:, 0] < x_max - x_margin) &
            (coords[:, 2] > z_min + z_margin) & (coords[:, 2] < z_max - z_margin)
    )

    inner_coords = coords[mask]
    return inner_coords

def oobb_to_aabb(oobb_cornerPoints: Union[tuple, list, jnp.array]):
    if isinstance(oobb_cornerPoints, jnp.ndarray):
        pass
    else:
        oobb_cornerPoints = jnp.array(oobb_cornerPoints)

    mins = jnp.min(oobb_cornerPoints, axis=0)  # (3,)
    maxs = jnp.max(oobb_cornerPoints, axis=0)  # (3,)
    bounds = jnp.stack([mins, maxs])
    rotated_aabb = jnp.array(
        [bounds[choice, jnp.arange(3)] for choice in itertools.product([0, 1], repeat=3)],
        dtype=jnp.float32,
    )

    # fifth, compute new AABB size (doesnt matter that it got translated)
    sizes = maxs - mins

    # sixth, compute new AABB center
    new_center = rotated_aabb.mean(axis=0)

    return {"center": xyztuple2dict(new_center), "size": xyztuple2dict(sizes), "cornerPoints": oobb_cornerPoints}



@struct.dataclass
class ProcThorObject:
    # id: str = struct.field(pytree_node=False)  # str bytes
    affordances: jnp.ndarray
    position: jnp.ndarray
    rotation: jnp.ndarray
    aabb_center: jnp.ndarray
    aabb_size: jnp.ndarray
    aabb_cornerPoints: jnp.ndarray
    oobb_cornerPoints: jnp.ndarray
    spawn_coordinates_above_receptacle: jnp.ndarray

    @property
    def is_pickupable(self):
        # FIXME: if self.affordances is 2D array, this will break
        return self.affordances[AFFORDANCE_NAMES.index("pickupable")]

    @property
    def is_receptacle(self):
        # FIXME: if self.affordances is 2D array, this will break
        return self.affordances[AFFORDANCE_NAMES.index("receptacle")]

    def take(self, i: int):
        values, tree_def = jax.tree.flatten(self)
        values = [jnp.take(v, jnp.astype(i, int), axis=0) for v in values]
        return jax.tree.unflatten(tree_def, values)

    @singledispatchmethod
    @classmethod
    def create(cls, arg):
        raise NotImplementedError()

    @classmethod
    def create_from_spawncoords_only(cls, spawn_coords):
        return cls(None,None,None,None,None,None,None,spawn_coords)

    @create.register(dict)
    @classmethod
    def _(cls, dict: Dict[str, Any]):
        # id = dict["id"]
        position = dict["position"]
        rotation = dict["rotation"]
        aabb = dict["aabb"]
        oobb = dict["oobb"]

        if oobb is None:
            oobb = aabb["cornerPoints"]

        affordances = []
        for name in AFFORDANCE_NAMES:
            val = dict["affordances"][name]
            affordances.append(bool(val))
        affordances = jnp.array(affordances)

        position = jnp.array(dict2xyztuple(position))
        rotation = jnp.array(dict2xyztuple(rotation))

        spawn_coordinates_above_receptacle = jnp.array(dict["spawn_coordinates_above_receptacle"])

        return cls(
            affordances,
            position,
            rotation,
            jnp.array(dict2xyztuple(aabb["center"])),
            jnp.array(dict2xyztuple(aabb["size"])),
            jnp.array(aabb["cornerPoints"]),
            jnp.array(oobb["cornerPoints"]),
            spawn_coordinates_above_receptacle
        )

    @create.register(list)
    @classmethod
    def _(cls, list: List[Dict]):
        return spoof_vmap([ProcThorObject.create(dico) for dico in list])

    # @jax.jit
    def sample_from_surface(self, key, num_samples=1):
        return jax.random.choice(key, self.spawn_coordinates_above_receptacle, shape=(num_samples,), replace=False)

    #@jax.jit
    def make_potential_field_OLD(self, current_positions):
        if len(current_positions) == 0:
            return jnp.ones((len(self.spawn_coordinates_above_receptacle),)) / len(self.spawn_coordinates_above_receptacle)

        # potential field input is a vector of positions. The ones at -jnp.inf are to be ignored. The others are to repulse the spawn coords
        def foreach_spawn(pots, spawn_coord):
            def foreach_pot(s, p):
                return jnp.linalg.norm(s - p)

            return jax.vmap(functools.partial(foreach_pot, spawn_coord))(pots)

        dists = jax.vmap(functools.partial(foreach_spawn, current_positions))(self.spawn_coordinates_above_receptacle)
        dists = jnp.nan_to_num(dists, posinf=0).sum(axis=1)

        remove_0_mask = dists == 0
        temp = dists.max() * remove_0_mask + dists * (1 - remove_0_mask)
        dists = dists.clip(
            temp.min(), max=jnp.inf
        )  # removes already selected points (they were 0's which made for a very spiky field)

        weights = dists * 10 ** 2  # makes it VERY likely to select the furthest point
        weights = weights / weights.sum()
        return weights

    import jax
    import functools

    def make_potential_field(self, current_positions, object_radius=0.1):
        """
        Args:
            current_positions: (M, 3) array of existing object positions.
            object_radius: Float radius to define a "hard collision".
        """
        num_spawns = len(self.spawn_coordinates_above_receptacle)

        # 1. Handle empty scene
        if len(current_positions) == 0:
            return jnp.ones((num_spawns,)) / num_spawns

        # 2. Calculate Distance Matrix (N_spawn x M_current)
        # We create a mask for valid objects (ignoring those at -inf)
        # Assuming objects at -inf are padding/invalid
        valid_obj_mask = jnp.all(jnp.isfinite(current_positions), axis=1)  # Shape (M,)

        def dist_fn(spawn, curr_pos):
            return jnp.linalg.norm(spawn - curr_pos)

        # Vectorize over spawns, then over current_positions
        # resulting shape: (N_spawns, M_current_positions)
        all_dists = jax.vmap(
            lambda s: jax.vmap(lambda c: dist_fn(s, c))(current_positions)
        )(self.spawn_coordinates_above_receptacle)

        # 3. Apply Safety Mask (The "Min" Step)
        # If an object is invalid (-inf), we set its distance to infinity so it doesn't affect the min()
        safe_dists = jnp.where(valid_obj_mask, all_dists, jnp.inf)

        # Find the distance to the *nearest* object for each spawn point
        min_dists = jnp.min(safe_dists, axis=1)  # Shape (N_spawns,)

        # 4. Filter Collisions (Hard Constraint)
        # Any point closer than object_radius is strictly invalid (weight 0)
        valid_spawn_mask = min_dists > object_radius

        # 5. Convert to Probabilities (Softmax-like scaling)
        # We want larger distances -> Higher probability
        # We use a temperature factor to sharpen the peak (greedy selection)

        # Mask out invalid spots by setting them to -inf before softmax
        # or simply zeroing them out after linear scaling. Let's do linear scaling for stability.

        weights = min_dists * valid_spawn_mask

        # Power scaling makes the field "spiky" (favoring the absolute furthest point)
        # increasing the power (e.g., **4) makes it more greedy.
        weights = weights ** 4

        # Normalize
        weight_sum = weights.sum()

        # Safety check: if all points are invalid (weight_sum is 0), return uniform distribution
        return jax.lax.cond(
            weight_sum > 0,
            lambda: weights / weight_sum,
            lambda: jnp.ones((num_spawns,)) / num_spawns
        )

    @functools.partial(jax.jit, static_argnums=(3,))
    def sample_from_surface_with_potential_field(self, key, potential_field, num_samples=1):
        # weights = self.make_potential_field(potential_field)
        ret = jax.random.choice(
            key, self.spawn_coordinates_above_receptacle, shape=(num_samples,), replace=False, p=potential_field
        )
        return ret

    @property
    def height(self):
        return jnp.atleast_1d(self.aabb_size[1]).squeeze()

    @property
    def width(self):
        return jnp.atleast_1d(self.aabb_size[0]).squeeze()

    @property
    def depth(self):
        return jnp.atleast_1d(self.aabb_size[2]).squeeze()

    def get_aabb(self):
        return {"center": xyztuple2dict(self.aabb_center), "size": xyztuple2dict(self.aabb_size),
         "cornerPoints": self.aabb_cornerPoints.tolist()}

    def get_oobb(self):
        return {"cornerPoints": self.oobb_cornerPoints.tolist()}

    @jax.jit
    def resolve_bboxes(self, new_bottom_pos, new_y_axis_rotation):
        if len(new_bottom_pos.squeeze().shape) == 2:
            return jax.vmap(functools.partial(ProcThorObject.resolve_bboxes, self))(new_bottom_pos, new_y_axis_rotation)

        # first, center the object
        current_oobb_center = jnp.mean(self.oobb_cornerPoints, axis=0)
        centered_oobb = self.oobb_cornerPoints - current_oobb_center

        # second, rotate the object around the origin
        cos_t, sin_t = jnp.cos(new_y_axis_rotation), jnp.sin(new_y_axis_rotation)
        rot_mat = jnp.array([[cos_t, 0.0, sin_t], [0.0, 1.0, 0.0], [-sin_t, 0.0, cos_t]], dtype=jnp.float32)  # (3, 3)
        rotated_oobb = centered_oobb @ rot_mat.T  # (8, 3)

        # fourth, translate by bottom_pos (NOT by center!)
        rotated_oobb = rotated_oobb + new_bottom_pos

        aabb = oobb_to_aabb(rotated_oobb)
        aabb["center"] = jnp.array(dict2xyztuple(aabb["center"]))
        aabb["size"] = jnp.array(dict2xyztuple(aabb["size"]))
        aabb["cornerPoints"] = jnp.array(aabb["cornerPoints"])
        oobb = {"cornerPoints": rotated_oobb}
        return aabb, oobb
