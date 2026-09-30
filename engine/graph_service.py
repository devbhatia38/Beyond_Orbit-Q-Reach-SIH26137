"""
QuantumRoute Engine - Real Road Graph Model
Uses OSMnx and NetworkX to model and route on the real road network of Central Delhi.
Features:
- Automatic caching of the Central Delhi road network graph.
- Travel speeds and travel times on all edge attributes.
- High-performance nearest-node spatial snapping via SciPy cKDTree.
- Dynamic traffic shock congestion injection.
- Matrix calculation endpoint logic for road network distance and travel times.
"""

import os
import math
from typing import List, Tuple, Dict, Any, Optional
import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

try:
    import osmnx as ox
except ImportError:
    ox = None


EARTH_RADIUS_METERS = 6371000.0
DEFAULT_SPEED_MPS = 8.333  # ~30 km/h in urban Delhi


def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Computes great-circle distance between two (lat, lon) coordinates in meters."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_METERS * c


class RealRoadGraph:
    """Manages the OSMnx Central Delhi road network graph and distance/time matrices."""

    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            # Anchor to engine/cache or parent directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
            cache_dir = os.path.join(base_dir, "cache")
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

        self.cache_file = os.path.join(self.cache_dir, "central_delhi.graphml")
        self.fallback_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "osm_network.graphml")

        self.graph: Optional[nx.MultiDiGraph] = None
        self.undirected_graph: Optional[nx.Graph] = None
        self.node_ids: List[Any] = []
        self.node_coords: np.ndarray = np.empty((0, 2))
        self.kdtree: Optional[cKDTree] = None
        self.loaded_source = "uninitialized"

        self._initialize_graph()

    def _initialize_graph(self):
        """Loads cached graph or downloads Central Delhi road network via OSMnx."""
        if ox is None:
            print("[RoadGraph] OSMnx not available. Falling back to synthetic/haversine.")
            return

        hwy_speeds = {
            "motorway": 80.0,
            "trunk": 60.0,
            "primary": 50.0,
            "secondary": 40.0,
            "tertiary": 30.0,
            "residential": 25.0,
            "unclassified": 25.0,
            "service": 20.0,
        }

        # 1. Try primary cache file
        if os.path.exists(self.cache_file):
            try:
                print(f"[RoadGraph] Loading cached graph from {self.cache_file}...")
                self.graph = ox.load_graphml(self.cache_file)
                self.loaded_source = "cache:central_delhi.graphml"
            except Exception as e:
                print(f"[RoadGraph] Error loading primary cache: {e}")

        # 2. Try online download if not loaded
        if self.graph is None:
            try:
                print("[RoadGraph] Downloading road network for 'Central Delhi, New Delhi, India'...")
                self.graph = ox.graph_from_place("Central Delhi, New Delhi, India", network_type="drive")
                ox.save_graphml(self.graph, self.cache_file)
                self.loaded_source = "osmnx:download_central_delhi"
                print(f"[RoadGraph] Successfully downloaded and cached {len(self.graph.nodes)} nodes.")
            except Exception as e:
                print(f"[RoadGraph] Download failed: {e}")

        # 3. Fallback to repository osm_network.graphml
        if self.graph is None and os.path.exists(self.fallback_file):
            try:
                print(f"[RoadGraph] Loading fallback graph from {self.fallback_file}...")
                self.graph = ox.load_graphml(self.fallback_file)
                self.loaded_source = "fallback:osm_network.graphml"
            except Exception as e:
                print(f"[RoadGraph] Error loading fallback graph: {e}")

        if self.graph is not None:
            try:
                self.graph = ox.add_edge_speeds(self.graph, hwy_speeds=hwy_speeds, fallback=30.0)
                self.graph = ox.add_edge_travel_times(self.graph)
            except Exception as e:
                print(f"[RoadGraph] Warning adding speeds/travel_times: {e}")

            # Build KDTree for sub-millisecond node snapping
            self._build_spatial_index()

            # Create an undirected view for resilient fallback routing if one-ways block connectivity
            try:
                self.undirected_graph = self.graph.to_undirected()
            except Exception:
                self.undirected_graph = nx.Graph(self.graph)

    def _build_spatial_index(self):
        """Builds a 2D KDTree of (lat, lon) coordinates for rapid snapping."""
        if not self.graph:
            return

        self.node_ids = list(self.graph.nodes)
        coords = []
        for n in self.node_ids:
            data = self.graph.nodes[n]
            lat = float(data.get("lat", data.get("y", 0.0)))
            lon = float(data.get("lon", data.get("x", 0.0)))
            coords.append([lat, lon])

        self.node_coords = np.array(coords)
        if len(self.node_coords) > 0:
            self.kdtree = cKDTree(self.node_coords)
            print(f"[RoadGraph] Built KDTree with {len(self.node_coords)} nodes.")

    def snap_coordinate(self, lat: float, lng: float) -> Tuple[Any, float]:
        """Snaps a (lat, lng) to the nearest network node. Returns (node_id, snap_distance_m)."""
        if self.kdtree is None or len(self.node_ids) == 0:
            return 0, 0.0

        dist, idx = self.kdtree.query([lat, lng])
        node_id = self.node_ids[idx]
        node_lat, node_lon = self.node_coords[idx]
        phys_dist = haversine_distance((lat, lng), (node_lat, node_lon))
        return node_id, phys_dist

    def compute_matrix(
        self,
        coords: List[List[float]],
        traffic_shock: bool = False
    ) -> Dict[str, Any]:
        """
        Computes the distance and duration matrix for an array of [lat, lng] coordinates.
        Applies edge congestion multiplier when traffic_shock=True.
        """
        n = len(coords)
        if n == 0:
            return {
                "distance_matrix": [],
                "duration_matrix": [],
                "nodes": [],
                "source": self.loaded_source,
                "traffic_shock": traffic_shock,
            }

        # 1. Snap each coordinate to nearest graph node
        snapped_nodes = []
        for point in coords:
            lat, lng = point[0], point[1]
            node_id, _ = self.snap_coordinate(lat, lng)
            snapped_nodes.append(node_id)

        # 2. Prepare empty matrices
        distance_matrix = [[0.0] * n for _ in range(n)]
        duration_matrix = [[0.0] * n for _ in range(n)]

        # Determine congestion penalty multiplier
        shock_multiplier = 2.5 if traffic_shock else 1.0

        # If graph is unavailable, use pure Haversine
        if self.graph is None:
            return self._compute_haversine_matrix(coords, traffic_shock)

        # 3. Calculate all-pairs shortest paths
        for i in range(n):
            for j in range(n):
                if i == j:
                    distance_matrix[i][j] = 0.0
                    duration_matrix[i][j] = 0.0
                    continue

                u, v = snapped_nodes[i], snapped_nodes[j]
                if u == v:
                    # Snapped to same node, compute direct distance
                    dist = haversine_distance((coords[i][0], coords[i][1]), (coords[j][0], coords[j][1]))
                    distance_matrix[i][j] = round(dist, 2)
                    duration_matrix[i][j] = round((dist / DEFAULT_SPEED_MPS) * shock_multiplier, 2)
                    continue

                try:
                    # Attempt directed graph shortest path
                    dist = nx.shortest_path_length(self.graph, source=u, target=v, weight="length")
                    dur = nx.shortest_path_length(self.graph, source=u, target=v, weight="travel_time")
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    # Try undirected graph if directed has one-way restriction
                    try:
                        dist = nx.shortest_path_length(self.undirected_graph, source=u, target=v, weight="length")
                        dur = nx.shortest_path_length(self.undirected_graph, source=u, target=v, weight="travel_time")
                    except (nx.NetworkXNoPath, nx.NodeNotFound, Exception):
                        # Graceful Euclidean/Haversine fallback for unroutable components
                        dist = haversine_distance((coords[i][0], coords[i][1]), (coords[j][0], coords[j][1]))
                        dur = dist / DEFAULT_SPEED_MPS

                distance_matrix[i][j] = round(float(dist), 2)
                duration_matrix[i][j] = round(float(dur) * shock_multiplier, 2)

        return {
            "distance_matrix": distance_matrix,
            "duration_matrix": duration_matrix,
            "nodes": [int(sn) if isinstance(sn, (int, np.integer)) else str(sn) for sn in snapped_nodes],
            "source": f"osmnx_central_delhi_{self.loaded_source}",
            "traffic_shock": traffic_shock,
            "multiplier": shock_multiplier
        }

    def _compute_haversine_matrix(
        self,
        coords: List[List[float]],
        traffic_shock: bool = False
    ) -> Dict[str, Any]:
        """Pure Haversine distance and duration calculation as a guaranteed fallback."""
        n = len(coords)
        distance_matrix = [[0.0] * n for _ in range(n)]
        duration_matrix = [[0.0] * n for _ in range(n)]
        shock_multiplier = 2.5 if traffic_shock else 1.0

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                dist = haversine_distance((coords[i][0], coords[i][1]), (coords[j][0], coords[j][1]))
                distance_matrix[i][j] = round(dist, 2)
                duration_matrix[i][j] = round((dist / DEFAULT_SPEED_MPS) * shock_multiplier, 2)

        return {
            "distance_matrix": distance_matrix,
            "duration_matrix": duration_matrix,
            "nodes": list(range(n)),
            "source": "haversine_fallback",
            "traffic_shock": traffic_shock,
            "multiplier": shock_multiplier
        }


# Singleton graph manager instance for reusability across API requests
road_graph_service = RealRoadGraph()
