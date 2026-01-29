import copy
import functools
from functools import partial
from typing import List, Tuple, Set, Any

import jax
import jax.numpy as jnp
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import shapely
from shapely.strtree import STRtree
from flax import struct
from shapely.geometry import Polygon
from shapely.ops import triangulate
from typing_extensions import Self

from semistaticsim.rendering.utils.dict2xyztup import dict2xyztuple


@partial(jax.jit, static_argnums=(1,))
def split_key(key, num_keys):
    key, *rng = jax.random.split(key, num_keys + 1)
    rng = jnp.reshape(jnp.stack(rng), (num_keys, 2))
    return key, rng

def point_to_shapely(point):
    if len(point) == 3:
        def cast(p):
            return shapely.Point(p[0], p[2])
    else:
        def cast(p):
            return shapely.Point(p[0], p[1])
    return cast(point)


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



@struct.dataclass
class RoomPolygon:
    scene_room_id: int
    scene_room_floorPolygon: list[dict]
    triangles: jnp.ndarray
    triangle_areas: jnp.ndarray

    @classmethod
    def create(cls, id, room):
        self = RoomPolygon(id, room, None, None)

        polygon = Polygon(self.floor_polygon_coords)
        def polygon_to_triangles(polygon):
            """
            Triangulate a shapely polygon and return list of triangles.
            """
            tris = shapely.ops.triangulate(polygon)

            ret = []
            for tri in tris:
                centroid = tri.centroid
                if not polygon.contains(centroid):
                    continue
                ret.append(list(tri.exterior.coords)[:-1])

            return ret
        tris = jnp.array(polygon_to_triangles(polygon))

        def triangle_area(tri):
            x1, y1 = tri[0]
            x2, y2 = tri[1]
            x3, y3 = tri[2]
            return 0.5 * jnp.abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1))
        triangle_areas = jax.vmap(triangle_area)(tris)

        return self.replace(triangles=tris, triangle_areas=triangle_areas)

    @property
    def num_triangles(self):
        return self.triangles.shape[0]

    @property
    def room_bbox(self):
        coords = self.floor_polygon_coords

        min_x, min_y = jnp.inf, jnp.inf
        max_x, max_y = -jnp.inf, -jnp.inf

        for coord in coords:
            min_x = min(min_x, coord[0])
            min_y = min(min_y, coord[1])
            max_x = max(max_x, coord[0])
            max_y = max(max_y, coord[1])

        return min_x, min_y, max_x, max_y

    def containment_mask(self, points):
        return [self.shapely_floor_polygon.contains(point_to_shapely(point)) for point in points]

    def _points_distance_to_polygon_edge(self, points):
        polygon = self.shapely_floor_polygon
        return [point_to_shapely(point).distance(polygon.boundary) for point in points]

    def points_distance_to_polygon_edge_mask(self, points, mindist):
        dists = self._points_distance_to_polygon_edge(points)
        return [d > mindist for d in dists]

    #@property
    def networkx(self, grid_size=0.05):
        min_x, min_y, max_x, max_y = self.room_bbox

        x = np.arange(min_x + grid_size * 2, max_x - grid_size, grid_size)
        y = np.arange(min_y + grid_size * 2, max_y - grid_size, grid_size)

        DEFAULT_ROBOT_HEIGHT = 0.95

        # Create 2D grid
        xx, yy = np.meshgrid(x, y)
        grid_points = np.stack([xx.ravel(), yy.ravel()], axis=-1, dtype=np.float32)
        grid_points = [(x, DEFAULT_ROBOT_HEIGHT, z) for x, z in grid_points]

        mask = self.containment_mask(grid_points)
        grid_points = [p for i, p in enumerate(grid_points) if mask[i]]
        mask = self.points_distance_to_polygon_edge_mask(grid_points, 0.3)
        grid_points = [p for i, p in enumerate(grid_points) if mask[i]]
        grid_points = [(z,y,x) for (x,y,z) in grid_points]

        G = nx.Graph()
        points_set = set(grid_points)

        # Add all points as nodes
        for p in points_set:
            G.add_node(p)

        # Define neighbor directions (axis-aligned)
        DIM = 3
        directions = []
        for d in range(DIM):
            if d == 1:
                continue
            for offset in [-grid_size, grid_size]:
                dir_vector = [0] * DIM
                dir_vector[d] = offset
                directions.append(tuple(dir_vector))

        # Add edges between neighbors
        for p in points_set:
            for d in directions:
                neighbor = tuple(np.add(p, d))
                if neighbor in points_set:
                    G.add_edge(p, neighbor)

        return G

    @property
    def floor_polygon_coords(self):
        return list(map(lambda x: (x["x"], x["z"]), self.scene_room_floorPolygon))

    @property
    def shapely_floor_polygon(self):
        return Polygon(self.floor_polygon_coords)

    @property
    def shapely_triangles(self):
        ret = []
        for tri in self.triangles:
            ret.append(Polygon(tri))
        return ret

    def plot_self(self, samples=None, plot_triangles=False, reachability_graph=None, show=False):
        plt.plot(*self.shapely_floor_polygon.exterior.xy)
        if plot_triangles:
            for tri in self.shapely_triangles:
                x, y = tri.exterior.xy
                plt.fill(x, y, alpha=0.2)

        if reachability_graph is not None:

            def draw_grid_graph_2d(G, path=None, node_size=100, node_color='lightblue', edge_color='gray',
                                   show_labels=False):
                pos = {node: (node[2], node[0]) for node in G.nodes}  # node positions are their coordinates

                nx.draw(G, pos,
                        node_size=node_size,
                        node_color=node_color,
                        edge_color=edge_color,
                        with_labels=show_labels,
                        font_size=8)

                # If a path is provided, draw it in red
                if path:
                    # Draw path edges first (so nodes will be on top)
                    path_edges = list(zip(path[:-1], path[1:]))
                    nx.draw_networkx_edges(G, pos,
                                           edgelist=path_edges,
                                           edge_color='red',
                                           width=2)
                    # Draw path nodes
                    nx.draw_networkx_nodes(G, pos,
                                           nodelist=path,
                                           node_size=node_size,
                                           node_color='red')

            draw_grid_graph_2d(reachability_graph)

        if samples is not None:
            plt.scatter(samples[:,0], samples[:,1], c="orange", zorder=10)

        if show:
            plt.show()

    @functools.partial(jax.jit, static_argnums=2)
    def sample_from_room(self, key, num_samples=1):
        if num_samples > 1:
            _, keys = split_key(key, num_samples)
            return jax.vmap(self.sample_from_room)(keys).squeeze()

        probs = self.triangle_areas / self.triangle_areas.sum()

        key_tri, key_uv = jax.random.split(key)
        tri_indices = jax.random.choice(key_tri, self.triangles.shape[0], (1,), p=probs)
        chosen_tris = self.triangles[tri_indices]

        uvs = jax.random.uniform(key_uv, (1, 2))
        u = jnp.sqrt(uvs[:, 0])
        v = uvs[:, 1]
        w0 = 1 - u
        w1 = u * (1 - v)
        w2 = u * v
        weights = jnp.stack([w0, w1, w2], axis=-1)
        weights_expanded = weights[:, :, jnp.newaxis]

        sampled_points = jnp.sum(chosen_tris * weights_expanded, axis=1)
        return sampled_points  # Returns [1, 2] array

@struct.dataclass
class DoorWay:
    holePolygon: List[Tuple[float,float,float]]
    position_center: Tuple[float,float]
    waypoints: List[Tuple[float,float]]

    def __contains__(self, point_node):
        if len(point_node) == 3:
            point_node = (point_node[0], point_node[2])
        return point_node in self.waypoints

    @classmethod
    def create(cls, door, grid_size):
        holePolygon = door["holePolygon"]
        p1, p2 = holePolygon

        center = ((p1['x'] + p2['x']) / 2, (p1['z'] + p2['z']) / 2)
        center = (round(center[0],1), round(center[1],1))

        # doors are always axis-aligned
        if p1['x'] == p2['x']:
            waypoints = [
                (center[0], center[1] + grid_size),
                center,
                (center[0], center[1] - grid_size),
            ]
        elif p1['z'] == p2['z']:
            waypoints = [
                (center[0] + grid_size, center[1]),
                center,
                (center[0] - grid_size, center[1]),
            ]
        else:
            raise AssertionError("Non-axis aligned door detected, failing.")

        return DoorWay(holePolygon, center, waypoints)

@struct.dataclass
class FloorPolygon:
    room_polygons: List[RoomPolygon]
    #doorways: List[DoorWay]
    grid_size: float

    @property
    def room_areas(self):
        return jnp.array([jnp.sum(room.triangle_areas) for room in self.room_polygons])

    @property
    def room_polygon_coords(self):
        return [room.floor_polygon_coords for room in self.room_polygons]

    @property
    def doorway_waypoints(self):
        return [x.waypoints for x in self.doorways]

    @property
    def flat_room_polygon_coords(self):
        ret = []
        for room in self.room_polygon_coords:
            ret += room
        return ret

    @property
    def floor_bbox(self):
        coords = self.flat_room_polygon_coords

        min_x, min_y = jnp.inf, jnp.inf
        max_x, max_y = -jnp.inf, -jnp.inf

        for coord in coords:
            min_x = min(min_x, coord[0])
            min_y = min(min_y, coord[1])
            max_x = max(max_x, coord[0])
            max_y = max(max_y, coord[1])

        return min_x, min_y, max_x, max_y

    @property
    def triangles(self):
        return jnp.concatenate([room.triangles for room in self.room_polygons])

    @property
    def triangle_areas(self):
        return jnp.concatenate([room.triangle_areas for room in self.room_polygons])

    @functools.partial(jax.jit, static_argnums=2)
    def sample_from_floor(self, key, num_samples=1, triangles=None, triangle_areas=None):
        if triangles is None:
            triangles = self.triangles
        if triangle_areas is None:
            triangle_areas = self.triangle_areas

        # what is a collecton of rooms, but a big room? much to ponder.
        return self.room_polygons[0].replace(triangles=triangles, triangle_areas=triangle_areas).sample_from_room(key=key, num_samples=num_samples)

    @classmethod
    def create(cls, scene, grid_size=0.1):
        rooms = scene["rooms"]

        MAX_NUM_TRIANGLES = -jnp.inf
        selves = []
        for i, room in enumerate(rooms):
            self = RoomPolygon.create(i, room["floorPolygon"])
            MAX_NUM_TRIANGLES = max(MAX_NUM_TRIANGLES, self.num_triangles)
            selves.append(self)

        for i in range(len(selves)):
            self = selves[i]
            self = self.replace(triangles=pad_to_shape(self.triangles, (MAX_NUM_TRIANGLES, 3, 2)))
            self = self.replace(triangle_areas=pad_to_shape(self.triangle_areas, (MAX_NUM_TRIANGLES,)))
            selves[i] = self

        doorways = [DoorWay.create(door, grid_size) for door in scene["doors"]]

        return FloorPolygon(selves, grid_size)

    def containment_mask(self, points):
        room_masks = jnp.array([room.containment_mask(points) for room in self.room_polygons])
        floor_mask = jnp.sum(room_masks, axis=0) > 0
        assert floor_mask.shape[0] == len(points)
        return floor_mask

    def points_distance_to_polygon_edge_mask(self, points, mindist):
        room_masks = jnp.array([room.points_distance_to_polygon_edge_mask(points, mindist) for room in self.room_polygons])
        floor_mask = jnp.sum(room_masks, axis=0) == room_masks.shape[0]
        assert floor_mask.shape[0] == len(points)
        return floor_mask

    #@functools.lru_cache(maxsize=None)
    def rechability_graph(self, mindist_to_walls=0.4, DEFAULT_ROBOT_HEIGHT=0.95, set_mindist_to_obj=0.3, pre_selected_points=None):
        grid_size = self.grid_size

        if pre_selected_points is None:
            min_x, min_y, max_x, max_y = self.floor_bbox

            min_x = round(min_x - 1)
            min_y = round(min_y - 1)
            max_x = round(max_x + 1)
            max_y = round(max_y + 1)

            x = np.arange(min_x + grid_size * 2, max_x - grid_size, grid_size)
            y = np.arange(min_y + grid_size * 2, max_y - grid_size, grid_size)

            # Create 2D grid
            xx, yy = np.meshgrid(x, y)
            grid_points = np.stack([xx.ravel(), yy.ravel()], axis=-1, dtype=np.float32)
            grid_points = [(x, DEFAULT_ROBOT_HEIGHT, z) for x, z in grid_points]

            mask = self.containment_mask(grid_points)
            grid_points = [p for i, p in enumerate(grid_points) if mask[i]]
            mask = self.points_distance_to_polygon_edge_mask(grid_points, mindist_to_walls)
            grid_points = [p for i, p in enumerate(grid_points) if mask[i]]
            grid_points = [(float(z),float(y),float(x)) for (x,y,z) in grid_points]
            grid_points = [(z,y,x) for (x,y,z) in grid_points]
        else:
            assert isinstance(pre_selected_points, list) and isinstance(pre_selected_points[0], tuple)
            grid_points = pre_selected_points


        G = nx.Graph()
        points_set = set(grid_points)

        # Add all points as nodes
        for p in points_set:
            G.add_node(p)

        # Define neighbor directions (axis-aligned)
        DIM = 3
        directions = []
        for d in range(DIM):
            if d == 1:
                continue
            for offset in [-grid_size, grid_size]:
                dir_vector = [0] * DIM
                dir_vector[d] = offset
                directions.append(tuple(dir_vector))

        # Add edges between neighbors
        for p in points_set:
            for d in directions:
                neighbor = tuple(np.add(p, d))
                if neighbor in points_set:
                    G.add_edge(p, neighbor)

        ALL_OTHER_NODES = list(G.nodes())
        JNP_ALL_OTHER_NODES = jnp.array(ALL_OTHER_NODES)

        @jax.jit
        def dist(target, other):
            return jnp.linalg.norm(target - other)

        def add_default_robot_height(p):
            return (p[0], DEFAULT_ROBOT_HEIGHT, p[1])

        # doorways time
        if False:
            for (out1, center, out2) in self.doorway_waypoints:
                out1 = add_default_robot_height(out1)
                center = add_default_robot_height(center)
                out2 = add_default_robot_height(out2)

                G.add_node(out1)
                G.add_node(center)
                G.add_node(out2)

                G.add_edge(out1, center)
                G.add_edge(out2, center)

                dist_to_out1 = jax.vmap(functools.partial(dist, jnp.array(out1)))(JNP_ALL_OTHER_NODES)
                dist_to_out2 = jax.vmap(functools.partial(dist, jnp.array(out2)))(JNP_ALL_OTHER_NODES)

                closest_node_index_out1 = jnp.argmin(dist_to_out1)
                closest_node_index_out2 = jnp.argmin(dist_to_out2)

                closest_node_out1 = ALL_OTHER_NODES[closest_node_index_out1]
                closest_node_out2 = ALL_OTHER_NODES[closest_node_index_out2]

                G.add_edge(out1, closest_node_out1)
                G.add_edge(out2, closest_node_out2)

        return ReachabilityGraph(G, grid_size, points_set, jnp.array(list(points_set)), set_mindist_to_obj, self)._build_caches()

    def plot_self(self, samples=None, plot_triangles=True, reachability_graph=None, show=True):
        """
        Plot the entire scene composed of multiple RoomPolygon instances.
        """
        # Plot each room
        for room in self.room_polygons:  # assuming self.rooms is a list of RoomPolygon
            room.plot_self(
                samples=None,  # per-room samples are not typically meaningful
                plot_triangles=plot_triangles,
                reachability_graph=None,  # or you could pass per-room graphs if available
                show=False,  # don't show until the end
            )

        # Optionally overlay scene-level data
        if reachability_graph is not None:
            def draw_grid_graph_2d(G, path=None, node_size=100, node_color='lightblue', edge_color='gray',
                                   show_labels=False):
                #pos = {node: (node[2], node[0]) for node in G.nodes}
                pos = {node: (node[0], node[2]) for node in G.nodes()}
                nx.draw(G, pos,
                        node_size=node_size,
                        node_color=node_color,
                        edge_color=edge_color,
                        with_labels=show_labels,
                        font_size=8)
                if path:
                    path_edges = list(zip(path[:-1], path[1:]))
                    nx.draw_networkx_edges(G, pos,
                                           edgelist=path_edges,
                                           edge_color='red',
                                           width=2)
                    nx.draw_networkx_nodes(G, pos,
                                           nodelist=path,
                                           node_size=node_size,
                                           node_color='red')
            if isinstance(reachability_graph, ReachabilityGraph):
                reachability_graph = reachability_graph.full_graph
            draw_grid_graph_2d(reachability_graph)

        if samples is not None:
            if not hasattr(samples, "shape"):
                samples = np.atleast_2d(np.asarray(samples))
            if samples.shape[1] == 3:
                x = samples[:, 0]
                y = samples[:, 2]
            else:
                x = samples[:, 0]
                y = samples[:, 1]
            plt.scatter(x,y, c="orange", zorder=10)

        if show:
            plt.show()


@struct.dataclass
class ReachabilityGraph:
    full_graph: nx.Graph
    grid_size: float
    point_set: Set[Tuple[float, float, float]]
    points: jnp.ndarray
    set_mindist_to_obj: float
    parent_floor: FloorPolygon

    _room_tree: Any = None 
    _room_node_map: Any = None
    _all_nodes_np: Any = None

    def _build_caches(self):
        # 1. Build Room Spatial Index (R-Tree) for O(log N) lookup
        rooms = self.parent_floor.room_polygons
        room_polys = [r.shapely_floor_polygon for r in rooms]
        # We store the actual room objects in the tree for retrieval
        room_tree = STRtree(room_polys)
        
        # 2. Pre-convert all nodes to numpy for fast vectorized math
        # Assuming nodes are tuples (x, y, z)
        all_nodes_np = np.array(list(self.full_graph.nodes))

        # 3. Pre-map which nodes belong to which room
        # This prevents running "contains()" on every node during runtime
        
        # We map the index of the polygon in the STRtree to the list of nodes
        room_node_map = {}
        for i, poly in enumerate(room_polys):
            # Find nodes inside this polygon
            # Note: We use the helper point_to_shapely here
            nodes_in_room = [
                n for n in self.full_graph.nodes 
                if poly.contains(point_to_shapely(n))
            ]
            room_node_map[i] = np.array(nodes_in_room)
        return self.replace(
            _room_tree=room_tree,
            _room_node_map=room_node_map,
            _all_nodes_np=all_nodes_np
        )

    @property
    def doorways(self) -> List[DoorWay]:
        return self.parent_floor.doorways

    def doorway_nodes(self):
        return [x.position for x in self.doorways]

    # def shunt(self, point):
    #     assert len(point) == 3

    #     def dist(p1, p2):
    #         return jnp.linalg.norm(p1 - p2)

    #     in_room = None
    #     # Determine the room polygon the point is at
    #     for room in self.parent_floor.room_polygons:
    #         if room.shapely_floor_polygon.contains(point_to_shapely(point)):
    #             in_room = room
    #             break

    #     if in_room is None:
    #         print("I'm sorry, point is outside all known rooms.")
    #         raise AssertionError()
    #         # fallback: use all nodes if point is outside known rooms
    #         candidate_nodes = list(self.full_graph.nodes)
    #     else:
    #         # Filter graph nodes to only those within the same room
    #         # fixme this could be precomputed
    #         candidate_nodes = [
    #             n for n in self.full_graph.nodes
    #             if in_room.shapely_floor_polygon.contains(point_to_shapely(n))
    #         ]
    #         # If there are no nodes in that room, fallback to all nodes
    #         if len(candidate_nodes) == 0:
    #             candidate_nodes = list(self.full_graph.nodes)

    #     all_nodes = jnp.array(candidate_nodes)
    #     # all_nodes = jnp.array(list(self.full_graph.nodes))

    #     def shunt_fn(pos, universal_y):
    #         pos = jnp.array(pos)
    #         pos = pos.at[1].set(universal_y)

    #         dists = jnp.nan_to_num(jax.vmap(functools.partial(dist, p2=pos))(all_nodes), neginf=jnp.inf, nan=jnp.inf,
    #                                posinf=jnp.inf)
    #         return dists.argmin()
    #     argret = shunt_fn(point, universal_y=list(self.nodes)[0][1])
    #     return candidate_nodes[int(argret)]

    def which_room(self, point):
        assert len(point) == 3

        # Find the room using the R-Tree (Fast)
        p_shapely = point_to_shapely(point)
        candidate_indices = self._room_tree.query(p_shapely)

        in_room_idx = None

        # Refine check (STRtree query is approximate bounding box, we need exact polygon)
        for idx in candidate_indices:
            if self.parent_floor.room_polygons[idx].shapely_floor_polygon.contains(p_shapely):
                in_room_idx = idx
                break

        if in_room_idx is None:
            # Raise an error immediately instead of falling back to all nodes
            raise AssertionError(f"Point {point} is outside all known rooms.")
        return in_room_idx

    def is_same_room(self, p1, p2) -> bool:
        return self.which_room(p1) == self.which_room(p2)

    def shunt(self, point):
        assert len(point) == 3

        in_room_idx = self.which_room(point)

        candidate_nodes = self._room_node_map.get(in_room_idx)

        if candidate_nodes is None or len(candidate_nodes) == 0:
            candidate_nodes = self._all_nodes_np

        universal_y = self._all_nodes_np[0][1]
        target = np.array([point[0], universal_y, point[2]])
        dists = np.linalg.norm(candidate_nodes - target, axis=1)
        best_idx = np.argmin(dists)
        return tuple(map(float, candidate_nodes[best_idx]))


    def shunt_to_bbox(self, point, size=None):
        """
        Finds all graph nodes closest to the bounding box of a target object.

        Returns:
            List of tuples: [((x, y, z), distance), ...]
        """
        # 1. Standardize Size
        if size is None:
            size = (0.1, 0.1, 0.1)

        assert len(point) == 3



        point_np = np.array(point)
        size_np = np.array(size)

        in_room_idx = self.which_room(point)

        candidate_nodes = self._room_node_map.get(in_room_idx)
        if candidate_nodes is None or len(candidate_nodes) == 0:
            candidate_nodes = self._all_nodes_np

        # 3. Calculate Distance to Bounding Box (AABB)
        half_size = size_np / 2.0
        aabb_min = point_np - half_size
        aabb_max = point_np + half_size

        # Vectorized distance to box surface
        delta_min = aabb_min - candidate_nodes
        delta_max = candidate_nodes - aabb_max
        dist_vec = np.maximum(0, np.maximum(delta_min, delta_max))
        dists = np.linalg.norm(dist_vec, axis=1)

        # 4. Filter for "All Closest Nodes"
        min_dist_found = np.min(dists)
        mask = dists <= (min_dist_found + self.grid_size)

        # Apply mask to both nodes and distances
        closest_nodes = candidate_nodes[mask]
        closest_dists = dists[mask]

        # Return list of ((x,y,z), distance)
        return [tuple(map(float, node)) for node in closest_nodes], closest_dists

    @property
    def nodes(self):
        return self.full_graph.nodes

    def clean_convert(self, point):
        # fixes conversion errors between np, jnp, lists
        import jax.numpy as jnp
        if isinstance(point, jnp.ndarray):
            point = np.array(point)
        if isinstance(point, np.ndarray):
            point = point.tolist()
        rounded = [round(x / self.grid_size) * self.grid_size for x in point]
        return tuple(rounded)

    def filter_(self, objects_metadata, mindist_to_obj=None) -> Self:
        if mindist_to_obj is None:
            mindist_to_obj = self.set_mindist_to_obj

        def is_inside_aabb(obj_pos, obj_size, agent_pos):
            """
            Check if an agent at `agent_pos` is inside the AABB defined by `obj_pos` and `obj_size`.
            Returns True if inside, False if outside.
            """

            half_size = obj_size / 2
            x_inside = (obj_pos[0] - half_size[0] <= agent_pos[0]) & (agent_pos[0] <= obj_pos[0] + half_size[0])
            z_inside = (obj_pos[2] - half_size[2] <= agent_pos[2]) & (agent_pos[2] <= obj_pos[2] + half_size[2])

            return jnp.logical_and(x_inside, z_inside)

        @jax.jit
        def _filter_agent_positions(agent_positions, object_positions, object_sizes, margin=0.0):
            """
            Remove agent positions that are inside any object's AABB, considering a margin.
            """
            # Margin was removing just half mindist_to_obj, so we double it here
            # inflated_sizes = object_sizes + (2 * margin)
            inflated_sizes = object_sizes + margin

            def is_inside_any_object(single_agent_pos, all_object_poses, all_object_sizes):
                return jax.vmap(functools.partial(is_inside_aabb, agent_pos=single_agent_pos))(all_object_poses,
                                                                                               all_object_sizes).any()

            mask = jax.vmap(functools.partial(is_inside_any_object, all_object_poses=object_positions,
                                              all_object_sizes=inflated_sizes))(agent_positions)
            return jnp.logical_not(mask)

        reachable_positions = copy.deepcopy(self.full_graph)
        todo_positions = reachable_positions.nodes

        DO_NOT_CONSIDER = lambda x: any(y in x.lower() for y in ["door", "painting", "window", "wall", "room", "floor"])

        centers = [dict2xyztuple(o["position"]) for o in objects_metadata if not DO_NOT_CONSIDER(o["objectId"])]
        sizes = [dict2xyztuple(o["axisAlignedBoundingBox"]["size"]) for o in objects_metadata if not DO_NOT_CONSIDER(o["objectId"])]
        #centers = [obj.position for name, obj in runtime_container.objects_map.items() if not DO_NOT_CONSIDER(name)]
        #sizes = [obj.size for name, obj in runtime_container.objects_map.items() if not DO_NOT_CONSIDER(name)]

        todo_positions = jnp.array(todo_positions)
        centers = jnp.array(centers)
        sizes = jnp.array(sizes)

        mask = _filter_agent_positions(todo_positions.at[:, 1].set(0.95), centers.at[:, 1].set(0.95), sizes,
                                       margin=mindist_to_obj) # fixme maybe 0.4 should be an arg?

        print("Num positions to remove", jnp.sum(jnp.logical_not(mask)))

        mask = np.array(mask)
        todo_positions = np.array(todo_positions)

        def removing_node_breaks_connectivity(graph, node_to_remove):
            graph = copy.deepcopy(graph)
            NUM_COMPONENTS = len(list(nx.connected_components(graph)))

            graph.remove_node(node_to_remove)
            NEW_NUM_COMPONENTS = len(list(nx.connected_components(graph)))

            return NUM_COMPONENTS != NEW_NUM_COMPONENTS

        for position in todo_positions[jnp.logical_not(mask)]:
            for node in nx.nodes(reachable_positions):
                if np.all(np.allclose(node, position)):
                    if not removing_node_breaks_connectivity(reachable_positions, node):
                        reachable_positions.remove_node(node)
                        break

        # Step 2: Keep only the largest connected component
        if reachable_positions.number_of_nodes() > 0:
            largest_cc_nodes = max(nx.connected_components(reachable_positions), key=len)
            reachable_positions = reachable_positions.subgraph(largest_cc_nodes).copy()

        new_graph = self.replace(full_graph=reachable_positions)
        return new_graph._build_caches()