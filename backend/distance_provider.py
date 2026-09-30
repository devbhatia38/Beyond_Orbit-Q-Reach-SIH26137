import math
import requests
from typing import List, Tuple

class DistanceProvider:
    def get_cost_matrix(self, coords: List[Tuple[float, float]]) -> Tuple[List[List[float]], List[List[float]], str]:
        """
        Takes a list of (lat, lon) coordinates.
        Returns (duration_matrix, distance_matrix, source_name).
        duration_matrix is in seconds, distance_matrix is in meters.
        """
        raise NotImplementedError

class HaversineProvider(DistanceProvider):
    def get_cost_matrix(self, coords: List[Tuple[float, float]]) -> Tuple[List[List[float]], List[List[float]], str]:
        n = len(coords)
        duration_matrix = [[0.0] * n for _ in range(n)]
        distance_matrix = [[0.0] * n for _ in range(n)]
        
        # Average urban speed in m/s (e.g., 30 km/h -> ~8.33 m/s)
        avg_speed_mps = 8.33 

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                lat1, lon1 = coords[i]
                lat2, lon2 = coords[j]
                
                # Haversine distance
                R = 6371000  # radius of Earth in meters
                phi1, phi2 = math.radians(lat1), math.radians(lat2)
                dphi = math.radians(lat2 - lat1)
                dlambda = math.radians(lon2 - lon1)
                
                a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(dlambda/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                
                distance = R * c
                distance_matrix[i][j] = distance
                duration_matrix[i][j] = distance / avg_speed_mps

        return duration_matrix, distance_matrix, "haversine_fallback"

class OSRMProvider(DistanceProvider):
    def __init__(self, base_url: str = "http://router.project-osrm.org"):
        self.base_url = base_url.rstrip("/")

    def get_cost_matrix(self, coords: List[Tuple[float, float]]) -> Tuple[List[List[float]], List[List[float]], str]:
        if not coords:
            return [], [], "osrm"

        # OSRM expects "lon,lat;lon,lat..."
        coord_string = ";".join([f"{lon},{lat}" for lat, lon in coords])
        
        # Use the table service and request both duration and distance
        url = f"{self.base_url}/table/v1/driving/{coord_string}?annotations=duration,distance"
        
        try:
            response = requests.get(url, timeout=3.0)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == "Ok":
                duration_matrix = data.get("durations", [])
                distance_matrix = data.get("distances", [])
                
                # Verify matrices are complete (no None values which OSRM can return if route not found)
                # Fallback to Haversine if any leg is unroutable
                for row in duration_matrix:
                    if None in row:
                        raise ValueError("OSRM returned None for a duration")
                for row in distance_matrix:
                    if None in row:
                        raise ValueError("OSRM returned None for a distance")
                        
                return duration_matrix, distance_matrix, "osrm"
            else:
                raise ValueError(f"OSRM returned non-Ok code: {data.get('code')}")
                
        except (requests.RequestException, ValueError) as e:
            print(f"OSRM request failed: {e}. Falling back to Haversine.")
            fallback = HaversineProvider()
            return fallback.get_cost_matrix(coords)
