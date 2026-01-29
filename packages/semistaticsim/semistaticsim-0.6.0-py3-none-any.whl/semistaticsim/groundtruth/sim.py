import functools

import jax
from flax import struct
from jax import numpy as jnp

from semistaticsim.groundtruth.objects import ObjectCollection
from semistaticsim.groundtruth.schedule import Schedule
from semistaticsim.rendering.floor import split_key


@struct.dataclass
class Simulator:
    object_collection: ObjectCollection
    schedule: Schedule # one per pickupable
    current_positions: jnp.ndarray
    current_rotations: jnp.ndarray

    @property
    def num_pickupables(self) -> int:
        return self.object_collection.pickupables.position.shape[0]

    @property
    def num_receptacles(self) -> int:
        return self.object_collection.receptacles.position.shape[0]

    @property
    def pickupables(self):
        return self.object_collection.pickupables

    @property
    def receptacles(self):
        return self.object_collection.receptacles

    @property
    def receptacle_names(self):
        return [self.object_collection.receptacle_index_to_id(i) for i in range(self.num_receptacles)]

    @property
    def pickupable_names(self):
        return [self.object_collection.pickupable_index_to_id(i) for i in range(self.num_pickupables)]

    @property
    def current_assignment(self):
        return self.schedule.current_location

    #@property
    #@jax.jit
    def get_current_receptacles(self):#:, current_assignment=None):
        #if current_assignment is None:
        #    current_assignment = self.current_assignment
        current_assignment = self.current_assignment

        ret = jax.vmap(self.object_collection.receptacles.take)(current_assignment)
        return ret

    #@property
    #@jax.jit
    def get_receptacle_to_pickupable_mask(self):
        # which receptacle contains which pickupable?
        def collect(current_assignment, one_receptacle):
            return current_assignment == one_receptacle # mask of pickupables
        ret = jax.vmap(functools.partial(collect, self.current_assignment))(jnp.arange(self.num_receptacles))
        # ret.sum(axis=0) should be equal to np.ones(self.num_pickupables)
        return ret

    #def sample_positions(self, key):
    #    key, rngs = split_key(key, self.num_pickupables)
    #    ret = jax.vmap(ProcThorObject. lambda x,k: x.sample_from_surface(k))(self.current_receptacles, rngs)
    #    return ret.squeeze()

    #@jax.jit
    def get_positions_for_receptacle(self, receptacle_id):
        def thunk(r_id, pos, assignment):
            mask = r_id == assignment
            return jax.lax.cond(mask, lambda:pos, lambda:jnp.ones(3)*-jnp.inf)
        bound = functools.partial(thunk, receptacle_id)
        return jax.vmap(bound)(self.current_positions, self.current_assignment)

    #@property
    #@jax.jit
    def get_positions_mat(self):
        ret = jax.vmap(self.get_positions_for_receptacle)(jnp.arange(self.num_receptacles))
        return ret

    def sample_y_axis_rotations(self, key):
        return jax.random.uniform(key, minval=0, maxval=2*jnp.pi, shape=(self.num_pickupables,))

    #@jax.jit
    def sample_position_potential_field(self, key, old_self, spoof_assignment_changes=False):
        # the spoof argument is only useful when creating the simulator; we spoof a change to force a resample of all positions

        @functools.partial(jax.jit, static_argnums=0)
        def handle_one_receptacle(spoof_assignment_changes: bool, key, receptacle, old_this_r_to_all_p, new_this_r_to_all_p, old_positions_for_this_r):
            assignment_change_mask = old_this_r_to_all_p != new_this_r_to_all_p if not spoof_assignment_changes else jnp.ones_like(new_this_r_to_all_p)
            def get_static_positions_for_this_r(p,assignment_change_mask):
                # if no change happened, keep old position
                return jax.lax.cond(assignment_change_mask, lambda:jnp.ones(3) * -jnp.inf, lambda:p)
            static_positions_for_this_r = jax.vmap(get_static_positions_for_this_r)(old_positions_for_this_r, assignment_change_mask)

            new_positions = static_positions_for_this_r
            for i in jnp.arange(self.num_pickupables):
                def noop(k, potential_field, static_position_for_this_p):
                    return static_position_for_this_p

                def sample(k, potential_field, static_position_for_this_p):
                    potential_field = receptacle.make_potential_field(potential_field)
                    return receptacle.sample_from_surface_with_potential_field(k,potential_field).squeeze()

                key, rng = jax.random.split(key)
                newpos = jax.lax.cond(
                    jnp.logical_and(new_this_r_to_all_p.take(i), assignment_change_mask.take(i)), # must be assigned to this receptacle AND have just changed (meaning that we dont currently have the obj inside current_positions
                    sample,
                    noop,
                    rng, new_positions, new_positions.take(i, axis=0)
                )
                new_positions = new_positions.at[i].set(newpos)
            return new_positions


        # assert (jnp.nan_to_num(positions_mat, neginf=0).sum(axis=0) == self.current_positions).all()

        if old_self.current_positions is None:
            old_self = old_self.replace(current_positions=jnp.ones((self.num_pickupables , 3)) * -jnp.inf)
        if self.current_positions is None:
            self = self.replace(current_positions=jnp.ones((self.num_pickupables , 3)) * -jnp.inf)

        #handle_one_receptacle(key, self.receptacles.take(5), old_self.receptacle_to_pickupable_mask()[5],
        #                      self.receptacle_to_pickupable_mask()[5], old_self.get_positions_mat()[5])

        key, rngs = split_key(key, self.num_receptacles)
        new_positions = jax.vmap(functools.partial(handle_one_receptacle, spoof_assignment_changes))(rngs, self.receptacles, old_self.get_receptacle_to_pickupable_mask(), self.get_receptacle_to_pickupable_mask(), self.get_positions_mat())

        # noqa this is useful for non-jit debugging
        #gathered = []
        #for tm in new_positions:
        #    for i, p in enumerate(tm):
        #        if not (p == -jnp.inf).any():
        #            gathered.append(i)
        #assert len(set(gathered)) == self.num_pickupables

        #return handle_one_receptacle(key, self.receptacles.take(5), old_self.receptacle_to_pickupable_mask[5], self.receptacle_to_pickupable_mask[5], old_self.get_positions_for_receptacle(5))
        return jnp.nan_to_num(new_positions, neginf=0).sum(axis=0)


    @classmethod
    def create(cls, key, object_collection: ObjectCollection, schedule: Schedule):
        schedule = jax.tree.map(jnp.squeeze, schedule)
        self = cls(object_collection, schedule, current_positions=None, current_rotations=None)

        key, rng = jax.random.split(key)
        initial_positions = self.sample_position_potential_field(key, self, spoof_assignment_changes=True)
        self = self.replace(current_positions=initial_positions, current_rotations=self.sample_y_axis_rotations(key))
        return self

    #@jax.jit
    def step(self, key):
        key, rngs = split_key(key, self.num_pickupables)
        new_schedules = jax.vmap(lambda s,k: s.tick(k))(self.schedule, rngs)
        new_schedules = jax.tree.map(jnp.squeeze, new_schedules)
        new_self = self.replace(schedule=new_schedules)
        new_assignment = new_self.current_assignment

        assignment_changed_mask = jnp.astype(new_assignment != self.current_assignment, float)
        key, rng = jax.random.split(key)
        # if assignment changed, the object moved, and we need to resample a y axis rotation
        new_rotations = self.current_rotations * (1-assignment_changed_mask) + self.sample_y_axis_rotations(rng) * assignment_changed_mask

        key, rng = jax.random.split(key)
        maybe_new_positions = new_self.sample_position_potential_field(rng, self)
        #new_positions = jax.vmap(lambda old, new, mask: old * (1-mask) + new * mask)(self.current_positions, maybe_new_positions, assignment_changed_mask) # not actually necessary because this is handled in the sample_potential_field function; left for readability only

        new_self = new_self.replace(current_positions = maybe_new_positions, current_rotations = new_rotations)
        return new_self

    #@jax.jit
    def diff(self, old_self):
        assignment_change = self.current_assignment != old_self.current_assignment
        position_before_and_after = jnp.concatenate((old_self.current_positions[None], self.current_positions[None]))
        # could also get the duratin left from the schedules etc if necessary
        return assignment_change, position_before_and_after


    def make_scan_thunk(self, scansize, scanunroll=10):
        #@jax.jit
        def thunk(self, key):
            old_self = self
            self = self.step(key)
            return self, (self.current_assignment, self.current_positions, self.current_rotations)#, *old_self.diff(self))

        def scan_it(key, self):
            self, data = jax.lax.scan(thunk, self, split_key(key, scansize)[-1], unroll=min(scanunroll, scansize))
            ret = {k:d for k,d in zip(["assignment", "position", "rotation"], data)}
            return self, ret

        return jax.jit(scan_it)

        #return jax.jit(lambda key, simulator: jax.lax.scan(thunk, simulator, split_key(key, scansize)[-1], unroll=min(scanunroll, scansize)))
        #return thunk
