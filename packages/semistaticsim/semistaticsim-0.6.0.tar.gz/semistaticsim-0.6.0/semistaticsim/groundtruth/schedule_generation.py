import copy
import os
import sys
from typing import Union, Literal, List, Optional

from semistaticsim.groundtruth.jax_polygon import split_key
from semistaticsim.groundtruth.transmat_utils import get_scc

os.environ["JAX_PLATFORM_NAME"] = "cpu"
import jax

jax.config.update("jax_platform_name", "cpu")
from jax import numpy as jnp


TRANSITION_MODEL_LITERALS = Literal[
    "fixed_canonical",
    "fixed_0.1_0.9",
    "uniform_no_diag",
    "uniform_full",
    "location_weighted_uniform_no_diag",
    "location_weighted_uniform_full",
]
# Fixed canonical: Cycle down the list of receptacles
# Fixed 0.1 0.9: 90% to next, 10% stay
# Uniform no diag: Sample transition matrix from a uniform distribution, no self-transitions
# Uniform full: Sample transition matrix from a uniform distribution, self-transitions allowed
# Location weighted uniform no diag: Sample transition matrix from a uniform distribution weighted by location weights,
# location weighted uniform full: Sample transition matrix from a uniform distribution weighted by location weights, self-transitions allowed
MODE_DURATION_LITERALS = Literal["deterministic", "gaussian", "instant", "even"]
# This is for time:
# Deterministic: Always transition at the mean time
# Gaussian: Sample from a Gaussian with mean and std
# Instant: Always transition at the current timestamp
# Even: All modes have equal time
DT_HANDLING_STRATEGY = Literal["squash", "clip", "none"]

# Only add noise at the day level, make this more configurable
SCALE_TO_NOIS_STD = {
    "year": 0.0,     
    "month": 0.0,    
    "week": 0.0,     
    "day": 0.007,    
    "hour": 0.0,     
}

def normalize_vec(vec: jnp.ndarray) -> jnp.ndarray:
    return vec / vec.sum()


def weight_vec(vec: jnp.ndarray, w: jnp.ndarray) -> jnp.ndarray:
    return vec * w


def mk_normalized_vec_func(size):
    def gen_normalized_vec(key):
        key, rng = jax.random.split(key)
        weights = jax.random.uniform(rng, minval=0, maxval=1, shape=(size,))
        return normalize_vec(weights)

    return gen_normalized_vec


def generate_time_pattern(
    key,
    num_states: int,
    mode_duration_mode: MODE_DURATION_LITERALS,
    transition_model_mode: TRANSITION_MODEL_LITERALS,
    randomly_delete_transitions: Union[float, bool],
    locations_weights: Optional[jnp.ndarray],
    num_pad_locations: int = 0,
    scale: str = "hour"
):
    """
    Generate a normalized time pattern across a given number of states.
    The times are random but sum to 1.
    """
    key, rng = jax.random.split(key)
    weights = mk_normalized_vec_func(num_states)(rng)

    key, rngs = split_key(rng, num_states)
    transition_mat = jax.vmap(mk_normalized_vec_func(num_states))(rngs)
    if transition_model_mode in [
        "location_weighted_uniform_no_diag",
        "location_weighted_uniform_full",
    ]:  
        transition_mat = jax.vmap(lambda x, w: normalize_vec(weight_vec(x, w)))(
            jnp.ones_like(transition_mat), jnp.tile(locations_weights, num_states).reshape((num_states, num_states))
        )

    if randomly_delete_transitions:
        TO_DELETE = []
        for i in range(transition_mat.shape[0]):
            if transition_mat.shape[0] - len(TO_DELETE) == 2:
                break
            key, rng = jax.random.split(key)
            if jax.random.uniform(rng, minval=0, maxval=1, shape=(1,)).item() > randomly_delete_transitions:
                TO_DELETE.append(i)
    else:
        TO_DELETE = []

    for to_delete in TO_DELETE:
        for l in range(num_states):
            transition_mat = transition_mat.at[l, to_delete].set(0)

    # Deterministic transition
    if transition_model_mode == "fixed_canonical":
        transition_mat = transition_mat * 0
        for l1 in range(num_states):
            l2 = (l1 + 1) % num_states
            while l2 in TO_DELETE:
                l2 = (l2 + 1) % num_states
            transition_mat = transition_mat.at[l1, l2].set(1)

    # Fixed probabilistic transition: 90% to next, 10% stay
    elif transition_model_mode == "fixed_0.1_0.9":
        transition_mat = transition_mat * 0
        for l1 in range(num_states):
            l2 = (l1 + 1) % num_states
            while l2 in TO_DELETE:
                l2 = (l2 + 1) % num_states

            transition_mat = transition_mat.at[l1, l1].set(0.1)
            transition_mat = transition_mat.at[l1, l2].set(0.9)

    # Uniform transition but no self-transitions
    elif transition_model_mode in ["uniform_no_diag", "location_weighted_uniform_no_diag"]:
        for l1 in range(num_states):
            transition_mat = transition_mat.at[l1, l1].set(0)
            transition_mat = jax.vmap(normalize_vec)(transition_mat)

    # Uniform transition including self-transitions
    elif transition_model_mode in ["uniform_full", "location_weighted_uniform_full"]:
        pass
    else:
        raise NotImplementedError(f"Unknown transition model mode: {transition_model_mode}")

    padded_shape = num_pad_locations + num_states
    # if padded_shape != num_states:
    weights = pad_to_shape(weights, (padded_shape,))
    transition_mat = pad_to_shape(transition_mat, (padded_shape, padded_shape))

    if mode_duration_mode == "gaussian":
        key, rng = jax.random.split(key)
        # FIXME: make stds an argument?
        stds = jnp.array([SCALE_TO_NOIS_STD[scale]] * num_states)
        # stds = jax.random.uniform(rng, minval=0, maxval=0.1, shape=(num_states,))
        ret = {"means": weights, "stds": pad_to_shape(stds, (padded_shape,)), "transition_mat": transition_mat}
    elif mode_duration_mode == "deterministic":
        ret = {"means": weights, "stds": jnp.zeros_like(weights), "transition_mat": transition_mat}
    elif mode_duration_mode == "instant":
        ret = {"means": jnp.ones_like(weights) * -10, "stds": jnp.zeros_like(weights), "transition_mat": transition_mat}
    elif mode_duration_mode == "even":
        ret = {
            "means": normalize_vec(jnp.ones_like(weights)),
            "stds": jnp.zeros_like(weights),
            "transition_mat": transition_mat,
        }
    else:
        raise NotImplementedError(f"mode_duration_mode {mode_duration_mode} not implemented")

    return ret

def handle_dt(scale, duration_and_transition_dict, dt, dt_handling_strategy, recursion_depth=0):
    MAX_RECURSION_DEPTH = 1000
    if recursion_depth > MAX_RECURSION_DEPTH:
        # give up
        return handle_dt(scale, duration_and_transition_dict, dt, "squash")

    if dt is None:
        if dt_handling_strategy != "none":
            print(f"WARNING: DT handling strategy was {dt_handling_strategy} but dt was not specified; dt was not handled.", file=sys.stderr)
        return duration_and_transition_dict

    from semistaticsim.groundtruth.schedule import TIME_SCALES_MAPPING
    DT_AT_CURRENT_SCALE = dt / TIME_SCALES_MAPPING[scale]
    EPS = 0.0001
    means, transition_mat = duration_and_transition_dict["means"], duration_and_transition_dict["transition_mat"]

    locs_under_the_dt = jnp.nonzero(jnp.logical_and(means <= DT_AT_CURRENT_SCALE, means > 0))[0]
    if len(locs_under_the_dt) == 0:
        return duration_and_transition_dict

    if dt_handling_strategy == "squash":
        for loc_index in locs_under_the_dt:
            means = means.at[loc_index].set(0)
            transition_mat = transition_mat.at[:, loc_index].set(0)
            transition_mat = transition_mat.at[loc_index, :].set(0)

        scc = get_scc(transition_mat)
        assert len(scc) >= 2, "The squash dt handling strategy inside schedule_generation.py has resulted in a transition matrix without any cycles. Consider using a transition model that results in more connections, or using the clip dt handling strategy."

        return {"means": means, "stds": duration_and_transition_dict["stds"], "transition_mat": transition_mat}

    elif dt_handling_strategy == "clip":
        # note: this CAN be done analytically, but results in completely unreadable code

        indices_that_were_0 = means <= 0

        distance_to_DT = DT_AT_CURRENT_SCALE - means[locs_under_the_dt] # compute bump to do
        means = (means - distance_to_DT.min() / means.shape[0]).clip(0,1) # remove even weight from all indices
        means = means.at[locs_under_the_dt].set(means[locs_under_the_dt] + distance_to_DT + EPS)
        means = means.at[indices_that_were_0].set(0) # should be useless but better be safe than sorry
        means = normalize_vec(means)

        assert jnp.all(indices_that_were_0 == (means <= 0))

        if recursion_depth > 0:
            print(f"DT Handling: recursion depth {recursion_depth} out of {MAX_RECURSION_DEPTH}")

        # by renormalizing, we might have pushed some values under EPS again. We can just iteratively do this process again and again until convergence.
        return handle_dt(scale, {"means": means, "stds": duration_and_transition_dict["stds"], "transition_mat": transition_mat}, dt, dt_handling_strategy, recursion_depth=recursion_depth+1)


def full_pattern(
    key,
    scales: List[str],
    locations: List[int],
    min_time_buckets: List[int],
    max_time_buckets: List[int],
    # leaf_order_mode: Literal["fixed_canonical", "uniform"] = "uniform",
    mode_duration_mode: MODE_DURATION_LITERALS = "deterministic",
    transition_model_mode: TRANSITION_MODEL_LITERALS = "fixed_canonical",
    # leaf_randomness_mode: Literal["uniform", "fixed_canonical"] = "uniform",
    randomly_delete_transitions: bool = False,  # This kills leaf - not transitions
    locations_weights: Optional[jnp.ndarray] = None,
    num_pad_locations: int = 0,
    dt_handling_strategy: DT_HANDLING_STRATEGY = "squash",
    dt: float = None
):
    """
    Recursively generate a hierarchical time pattern.

    Args:
        scales (list[str]): List of scales, from largest to smallest.
            Example: ["year", "month", "day"]
        locations (list[str]): Physical locations (only at the leaf scale).
        min_time_buckets (int): Minimum number of splits for higher scales.
        max_time_buckets (int): Maximum number of splits for higher scales.
        seed (int, optional): Random seed for reproducibility.
        is_gaussian (bool): Is the distribution gaussian or deterministic?.

    Returns:
        dict: Nested dictionary representing the full pattern.
    """
    # fixme need to make all DFS branches alter the same global key (maybe unroll? or just use a local global)
    # because otherwise the same key pattern occurs!
    # or actually maybe just the forloop: unnest and split before each downcall
    # if leaf_randomness_mode == "weighted_canonical":
    #    assert canonical_location_weights is not None
    #    if not isinstance(canonical_location_weights, jnp.ndarray):
    #        canonical_location_weights = jnp.array(canonical_location_weights)
    assert isinstance(locations[0], int) or isinstance(locations[0], float)
    assert len(scales) == len(min_time_buckets) == len(max_time_buckets)

    current_scale = scales[0]

    def ensure_cfgs_length(cfg_var):
        if not isinstance(cfg_var, list):
            cfg_var = [cfg_var] * len(scales)
        return cfg_var

    mode_duration_mode = ensure_cfgs_length(mode_duration_mode)
    transition_model_mode = ensure_cfgs_length(transition_model_mode)
    if locations_weights is None:
        locations_weights = jnp.ones((len(locations),))
    elif not isinstance(locations_weights, jnp.ndarray):
        locations_weights = jnp.array(locations_weights)

    # Leaf scale: assign location distribution
    if len(scales) == 1:

        key, rng = jax.random.split(key)
        distribution = generate_time_pattern(
            rng,
            len(locations),
            mode_duration_mode[0],
            transition_model_mode[0],
            randomly_delete_transitions,
            locations_weights=locations_weights,
            num_pad_locations=num_pad_locations,
            scale=current_scale,
        )

        distribution = handle_dt(scales[0], distribution, dt, dt_handling_strategy)
        # print("LOCATIONS AT LEAF", locations) fixme need to look at resolvable locs

        return {current_scale: {"distribution": distribution, "locations": locations}}

    # Higher scales: split into random buckets
    key, rng = jax.random.split(key)
    num_buckets = jax.random.randint(
        rng, minval=min_time_buckets[0], maxval=max_time_buckets[0], shape=(1,)
    ).item()  # random.randint(min_time_buckets, max_time_buckets)
    key, rng = jax.random.split(key)
    distribution = generate_time_pattern(
        rng,
        num_buckets,
        mode_duration_mode[0],
        transition_model_mode[0],
        randomly_delete_transitions,
        locations_weights=jnp.ones(num_buckets),
        num_pad_locations=0,
        scale=current_scale,
    )

    distribution = handle_dt(scales[0], distribution, dt, dt_handling_strategy)

    subpatterns = []
    for _ in range(num_buckets):
        key, rng = jax.random.split(key)
        subpat = full_pattern(
            rng,
            scales[1:],
            locations,
            min_time_buckets[1:],
            max_time_buckets[1:],
            mode_duration_mode[1:],
            transition_model_mode[1:],
            randomly_delete_transitions=randomly_delete_transitions,
            locations_weights=locations_weights,
            num_pad_locations=num_pad_locations,
            dt_handling_strategy=dt_handling_strategy,
            dt=dt
        )
        subpatterns.append(subpat)

    MISSING_BUCKETS = max_time_buckets[0] - num_buckets
    if MISSING_BUCKETS > 0:

        def pad_missing(v):
            if len(v.shape) == 1:
                return pad_to_shape(v, (max_time_buckets[0],))
            elif len(v.shape) == 2:
                return pad_to_shape(v, (max_time_buckets[0], max_time_buckets[0]))
            raise AssertionError()

        distribution = {k: pad_missing(v) for k, v in distribution.items()}
        for _ in range(MISSING_BUCKETS):  # won't ever get resolved to because of 0 transitions
            subpatterns.append(copy.deepcopy(subpatterns[-1]))

    return {current_scale: {"distribution": distribution, "subpatterns": subpatterns}}


def pad_to_shape(x: jnp.ndarray, target_shape: tuple[int, ...]) -> jnp.ndarray:
    """
    Pads `x` with zeros until it reaches `target_shape`.

    Args:
        x: jnp.ndarray, the input tensor
        target_shape: tuple of ints, desired output shape (must be >= x.shape)

    Returns:
        Padded tensor of shape `target_shape`.
    """
    if len(target_shape) != x.ndim:
        raise ValueError(f"target_shape {target_shape} must have same rank as x.shape {x.shape}")

    pad_widths = []
    for dim_size, target_size in zip(x.shape, target_shape):
        if target_size < dim_size:
            raise ValueError(f"target size {target_size} is smaller than input size {dim_size}")
        pad_before = 0
        pad_after = target_size - dim_size
        pad_widths.append((pad_before, pad_after))

    return jnp.pad(x, pad_widths, mode="constant", constant_values=0)


def flatten_pattern_for_visualization(pattern):
    """
    Flatten pattern into a format optimized for visualization.

    Returns:
        dict: Contains 'nodes', 'edges', and 'levels' for easy visualization
    """
    nodes = []
    edges = []
    levels = {}
    node_id = 0

    def _traverse_for_viz(node, path=None, parent_id=None, level=0):
        nonlocal node_id

        if path is None:
            path = []

        for scale, content in node.items():
            current_id = node_id
            node_id += 1

            current_path = path + [scale]
            distribution = content["distribution"]

            # Create node entry
            node_entry = {
                "id": current_id,
                "path": "/".join(current_path),
                "scale": scale,
                "level": level,
                "means": (
                    distribution["means"].tolist()
                    if hasattr(distribution["means"], "tolist")
                    else distribution["means"]
                ),
                "transition_matrix": (
                    distribution["transition_mat"].tolist()
                    if hasattr(distribution["transition_mat"], "tolist")
                    else distribution["transition_mat"]
                ),
                "parent_id": parent_id,
            }

            # Add locations if this is a leaf
            if "locations" in content:
                node_entry["locations"] = content["locations"]
                node_entry["is_leaf"] = True
            else:
                node_entry["is_leaf"] = False

            nodes.append(node_entry)

            # Track level information
            if level not in levels:
                levels[level] = []
            levels[level].append(current_id)

            # Create edge to parent if exists
            if parent_id is not None:
                edges.append({"from": parent_id, "to": current_id, "level_from": level - 1, "level_to": level})

            # Process subpatterns
            if "subpatterns" in content:
                for i, subpattern in enumerate(content["subpatterns"]):
                    bucket_path = current_path + [f"bucket_{i}"]
                    _traverse_for_viz(subpattern, bucket_path, current_id, level + 1)

    _traverse_for_viz(pattern)

    return {"nodes": nodes, "edges": edges, "levels": levels, "max_level": max(levels.keys()) if levels else 0}


def export_pattern_for_graphviz(pattern, filename="pattern.dot"):
    """
    Export pattern to Graphviz DOT format for visualization.
    """
    viz_data = flatten_pattern_for_visualization(pattern)

    with open(filename, "w") as f:
        f.write("digraph PatternTree {\n")
        f.write("  rankdir=TB;\n")
        f.write("  node [shape=box];\n\n")

        # Write nodes
        for node in viz_data["nodes"]:
            label = f"{node['scale']}"
            if node["is_leaf"]:
                label += f"\\nLocs: {node['locations']}"

            # Add some distribution info - only show first three means for brevity
            means_str = ", ".join([f"{x:.3f}" for x in node["means"][:3]])
            label += f"\\nMeans: [{means_str}...]"

            f.write(f'  {node["id"]} [label="{label}"];\n')

        f.write("\n")

        # Write edges
        for edge in viz_data["edges"]:
            f.write(f'  {edge["from"]} -> {edge["to"]};\n')

        f.write("}\n")

    print(f"Pattern exported to {filename}")


if __name__ == "__main__":
    # Example usage
    scales = ["month", "week", "day"]
    locations = [0, 1, 2]  # ["home", "work", "key rack"]
    # locations_weights = [0.1, 0.05, 0.2]

    pattern = full_pattern(
        key=jax.random.PRNGKey(0),
        scales=scales,
        locations=locations,
        min_time_buckets=[2, 5, 4],
        max_time_buckets=[2, 5, 4],
        # locations_weights=locations_weights,
        transition_model_mode="fixed_canonical",
    )

    # Export for visualization
    export_pattern_for_graphviz(pattern, "pattern_tree.dot")

    # Get visualization-optimized format
    viz_data = flatten_pattern_for_visualization(pattern)
    print("Visualization data structure:")
    print(f"Number of nodes: {len(viz_data['nodes'])}")
    print(f"Number of edges: {len(viz_data['edges'])}")
    print(f"Number of levels: {viz_data['max_level'] + 1}")
    print(f"Nodes per level: {viz_data['levels']}")
