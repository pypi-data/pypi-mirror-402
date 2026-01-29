import functools
from typing_extensions import Self

import jax
from flax import struct
import jax.numpy as jnp

from semistaticsim.rendering.floor import split_key
from semistaticsim.groundtruth.schedule_generation import full_pattern
from semistaticsim.groundtruth.spoof_vmap import spoof_vmap

from semistaticsim.groundtruth.transmat_utils import get_scc

TIME_SCALES_MAPPING = {
    "year": 365 * 24,
    "month": 30 * 24,
    "week": 7 * 24,
    "day": 24,
    "hour": 1,
}

EPS = 0.001

@struct.dataclass
class ScheduleDistribution:
    means: jnp.array
    stds: jnp.array

    def sample_duration(self, key, i: int):
        key, rngs = split_key(key, len(self))

        def sample(k, m, s):
            # sigma2 = jnp.log(1 + (s ** 2) / (m ** 2 + 1e-8))
            # sigma = jnp.sqrt(sigma2)
            # mu = jnp.log(m + 1e-8) - sigma2 / 2
            # # Sample lognormal
            # return jnp.exp(jax.random.normal(k) * sigma + mu)
            x = jax.random.normal(key=k) * s + m
            # Skews the distribution to be non-negative
            return jnp.maximum(x, 0.0)

        # note: in "instant" mode, the returned sample will be negative
        samples = jax.vmap(sample)(rngs, self.means, self.stds)
        return jnp.take(samples, jnp.astype(i, int))

    def __len__(self):
        return self.stds.shape[0]

@struct.dataclass
class ScheduleTransition:
    mat: jnp.ndarray

    @property
    def possible_states(self):
        return jnp.arange(self.mat.shape[0])

    def transit(self, key, current: jnp.ndarray):
        current = jnp.atleast_1d(current)
        curvec = jnp.take(self.mat, jnp.astype(current, int), axis=0).squeeze()

        next_state = jax.random.choice(key, self.possible_states, shape=(1,), p=curvec)
        return next_state

    def largest_scc(self):
        return get_scc(self.mat)


@struct.dataclass
class Schedule:
    time_scale: float
    distribution: ScheduleDistribution
    transition_mat: ScheduleTransition
    subpatterns: Self
    current_pattern: int
    locations: jnp.array
    time_left_for_mode: float
    dt: float
    scales: list = struct.field(pytree_node=False)

    force_next_state: int
    safe_first_state: int

    def __len__(self):
        return len(self.distribution)

    @property
    def get_static_full_depth(self):
        return tuple([None] * len(self.scales))

    @classmethod
    def create(cls, key, dico, scales, locations, dt=1): # default dt is one hour
        time_scale_name = list(dico.keys())[0]
        time_scale = TIME_SCALES_MAPPING[time_scale_name]
        description = dico[time_scale_name]

        distribution = ScheduleDistribution(description["distribution"]["means"], description["distribution"]["stds"])
        transition_mat = ScheduleTransition(description["distribution"]["transition_mat"])
        if "locations" in description:
            subpatterns = []
        else:
            subpatterns = []
            for s in description["subpatterns"]:
                key, rng = jax.random.split(key)
                subpatterns.append(Schedule.create(rng, s, scales[1:], locations))
            if len(subpatterns) > 0:
                subpatterns = spoof_vmap(subpatterns)

        nodes_of_largest_cycle = list(transition_mat.largest_scc())

        safe_first_state = jnp.ones(1, dtype=float) * nodes_of_largest_cycle[0]

        return cls(
            time_scale=time_scale,
            distribution=distribution,
            transition_mat=transition_mat,
            subpatterns=subpatterns,
            scales=scales,
            current_pattern=-1.,
            locations=jnp.array(locations),
            time_left_for_mode=dt-EPS, # the next time we tick, we will for sure cause a transition
            dt=dt,
            force_next_state=safe_first_state,
            safe_first_state=safe_first_state,
        ).tick(key)

    def reset_subpatterns(self, depth=None):
        new_subpatterns = jax.vmap(functools.partial(Schedule.reset, depth=depth))(self=self.subpatterns)
        return new_subpatterns

    def reset(self, depth=None):
        if depth is None:
            depth = self.get_static_full_depth

        self = self.replace(force_next_state=self.safe_first_state, time_left_for_mode=-1., current_pattern=-1.)

        if len(depth) == 1:
            return self

        return self.replace(subpatterns=self.reset_subpatterns(depth=depth[1:]))


    #@jax.jit
    def tick(self, key, depth=None):
        if depth is None:
            depth = self.get_static_full_depth

        new_time_left = self.time_left_for_mode - self.dt
        time_over = jnp.astype(new_time_left <= 0, int)
        stolen_time = jnp.abs(new_time_left) * time_over

        # IF THE TIME IS OVER, COMPUTE WHAT THE NEXT MODE IS (LOOK AT THE TRANSITION MATRIX)
        key, rng = jax.random.split(key)
        DO_FORCE_NEXT_MODE = jnp.astype(self.force_next_state > -1, int) # this happens at creation, and also when a higher pattern exits (see reset)
        new_current_mode_IF_FORCE_NEXT_MODE = self.force_next_state
        self = self.replace(force_next_state=jnp.ones(1) * -1)    # no matter what, only force next state the first time
        new_current_mode_IFNOT_FORCE_NEXT_MODE = self.transition_mat.transit(rng, self.current_pattern)
        new_current_mode = new_current_mode_IFNOT_FORCE_NEXT_MODE * (1-DO_FORCE_NEXT_MODE) + new_current_mode_IF_FORCE_NEXT_MODE * DO_FORCE_NEXT_MODE
        new_current_mode = new_current_mode.squeeze()

        new_time_left = new_time_left * (1-time_over) + time_over * (self.distribution.sample_duration(key, new_current_mode) * self.time_scale - stolen_time)
        ret_current_mode = self.current_pattern * (1-time_over) + time_over * new_current_mode
        self = self.replace(current_pattern=ret_current_mode,time_left_for_mode=new_time_left)

        if len(depth) == 1:
            return self

        self_subpatterns = jax.lax.cond(time_over, lambda: self.reset_subpatterns(depth[1:]), lambda: self.subpatterns)

        key, rngs = split_key(key, len(self_subpatterns))
        new_subpatterns = jax.vmap(lambda key, x: x.tick(key, depth[1:]))(rngs, self_subpatterns)
        return self.replace(subpatterns=new_subpatterns)

    @jax.jit
    def get_current_mode(self, depth=None):
        if jnp.atleast_1d(self.dt).shape[0] != 1:
            ret = jax.vmap(lambda x:x.get_current_mode(depth))(self)
            if len(ret.shape) == 1:
                ret = ret[:,None]
            return ret

        if depth is None:
            depth = self.get_static_full_depth

        if len(depth) == 1:
            return jnp.take(self.locations, jnp.astype(self.current_pattern, int))

        ret = jax.vmap(lambda x: x.get_current_mode(depth=depth[1:]))(self.subpatterns)

        subpattern = jnp.atleast_1d(jnp.take(ret, jnp.astype(self.current_pattern, int), axis=0).squeeze())
        return jnp.concatenate([jnp.atleast_1d(self.current_pattern), subpattern]) #ret[self.current_pattern]

    @property
    def current_location(self):
        ret = jnp.atleast_2d(self.get_current_mode())
        return ret[:,-1]

    def step(self, key):
        old_self = self # noqa debug
        self = self.tick(key)
        mode = self.get_current_mode()
        return self, mode

    def make_step_func(self, scan_size=1000):
        def thunk(key, schedule):
            return jax.lax.scan(f=Schedule.step, init=schedule, xs=split_key(key, scan_size)[-1])

        print(f"Each scan will produce {scan_size} increments of {self.dt} days, which is {scan_size * self.dt} days long.")
        return thunk

if __name__ == "__main__":
    scales = ["day"]
    locations = [0,1]

    pattern = full_pattern(
        key=jax.random.PRNGKey(0),
        scales=scales, locations=locations,
        min_time_buckets=2,
        max_time_buckets=2,
        #dt=1/60
       # transition_model_mode="uniform_no_diag"
    )
    key = jax.random.PRNGKey(0)
    schedule = Schedule.create(key, pattern, scales, locations, dt=1/60)

    for i in range(1000000):
        print(schedule.current_location)
        print(schedule.time_left_for_mode)
        schedule = schedule.tick(key)
    #scan_func = schedule.make_step_func()
    #schedule, results = scan_func(key, schedule)
    # Results are the arrows of the tree
    #print(results)
