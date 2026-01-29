from typing import Union

import networkx as nx
from concurrent.futures import ThreadPoolExecutor, as_completed
import math

import numpy as np

from semistaticsim.rendering.floor import ReachabilityGraph
from semistaticsim.rendering.utils.dict2xyztup import dict2xyztuple


def cleanup_request(requested_node):
    if isinstance(requested_node, dict) and all([x in requested_node for x in ['x', 'y', 'z']]):
        requested_node = dict2xyztuple(requested_node)
    if isinstance(requested_node, tuple):
        requested_node = list(requested_node)
    return requested_node

def astar(requested_start_node, requested_end_node, requested_end_size, filtered_rg: ReachabilityGraph):
    requested_start_node = cleanup_request(requested_start_node)
    requested_end_node = cleanup_request(requested_end_node)

    # filtered_rg = full_reachability_graph.filter_(controller.last_event.metadata["objects"], mindist_to_obj=0.5)

    # filtered_rg.parent_floor.plot_self(reachability_graph=filtered_rg)
    # filtered_rg.parent_floor.plot_self(reachability_graph=filtered_rg)
    # filtered_rg.parent_floor.plot_self(samples=jnp.array(path))

    start_nodes, start_distances = filtered_rg.shunt_to_bbox(requested_start_node, None)
    end_nodes, end_distances = filtered_rg.shunt_to_bbox(requested_end_node, requested_end_size)

    for n in start_nodes + end_nodes:
        assert n in filtered_rg.full_graph

    start_node = start_nodes[start_distances.argmin()]

    # 5. Define the worker function for the thread pool
    def get_path_safe(target_node):
        try:
            # We use weight='weight' if your edges have weights, otherwise it defaults to 1
            # You can also pass a heuristic function here if you have one
            path = nx.astar_path(filtered_rg.full_graph, start_node, target_node)

            # Return slice [1:] as requested (excluding the start node)
            return path[1:]
        except nx.NetworkXNoPath:
            return None

    valid_paths = []

    # 6. Execute pathfinding in parallel
    # Using ThreadPoolExecutor is usually best for graph traversals as they release the GIL
    # and we avoid the overhead of pickling the whole graph for ProcessPoolExecutor.
    with ThreadPoolExecutor() as executor:
        # Submit all tasks
        future_to_node = {executor.submit(get_path_safe, node): node for node in end_nodes}

        for future in as_completed(future_to_node):
            path = future.result()
            if path is not None:
                valid_paths.append(path)

    if not valid_paths:
        # Handle the case where no path could be found to ANY end node
        raise ValueError(f"No path found from {start_node} to any of the {len(end_nodes)} candidate end nodes.")

    # 7. Select the best path
    # Currently selecting the path with the fewest hops/lowest weight.
    # If you want to account for 'end_distances', you would zip those values in earlier.
    best_path = min(valid_paths, key=lambda x: len(x))

    return best_path

def geodesic_distance_on_path_nodes(path_nodes, grid_size: Union[ReachabilityGraph, float, int]):
    if isinstance(grid_size, int) or isinstance(grid_size, float):
        pass
    else:
        grid_size = grid_size.grid_size
    if not isinstance(path_nodes, list):
        path_nodes = list(path_nodes)

    if len(path_nodes) == 0:
        return 0

    if len(path_nodes) == 1:
        return grid_size

    euclidean_distance = sum(
        np.linalg.norm(np.array(a) - np.array(b))
        for a, b in zip(path_nodes[:-1], path_nodes[1:])
    ) + grid_size
    return euclidean_distance

def geodesic_distance(requested_start_node, requested_end_node, requested_end_size, filtered_rg: ReachabilityGraph):
    return geodesic_distance_on_path_nodes(astar(requested_start_node, requested_end_node, requested_end_size, filtered_rg), filtered_rg.grid_size)