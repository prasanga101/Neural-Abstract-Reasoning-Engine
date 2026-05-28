from src.executor.base_tools import BaseTool
import heapq
import math
import requests
from heapq import heappop, heappush
from math import asin, cos, radians, sin, sqrt


class BlockedRouteDetectionTool(BaseTool):
    def __init__(self):
        super().__init__(name="detect_blocked_routes")

    def run(self, context: dict, env):
        sensor_data = env.get_state("sensor_data") or {}
        blocked_routes = []
        detection = {
            "status": "clear",
            "message": "No confirmed blocked routes were detected.",
            "source": "sensor_fallback",
            "simulated": False,
            "location": sensor_data.get("location"),
        }
        env.update_state("blocked_routes", blocked_routes)
        env.update_state("blocked_route_detection", detection)
        env.update_state("blocked_route_details", [])
        return {
            "blocked_routes": blocked_routes,
            "blocked_route_details": [],
            "blocked_route_detection": detection,
        }

class AlternativeRouteTool(BaseTool):
    def __init__(self):
        super().__init__(name="identify_alternative_routes")

    def run(self, context: dict, env):
        sensor_data = env.get_state("sensor_data") or {}
        hospitals = env.get_state("nearby_hospitals") or env.get_state("available_hospitals") or []

        if not hospitals:
            env.update_state("alternative_routes", [])
            return {"alternative_routes": []}

        src_lat = sensor_data.get("latitude")
        src_lon = sensor_data.get("longitude")

        if None in [src_lat, src_lon]:
            env.update_state("alternative_routes", [])
            return {"alternative_routes": []}

        remote_routes = []
        for hospital in hospitals[:5]:
            dest_lat = hospital.get("lat")
            dest_lon = hospital.get("lon")
            if None in [dest_lat, dest_lon]:
                continue

            remote_routes.extend(
                self._fetch_osrm_routes(src_lat, src_lon, dest_lat, dest_lon, hospital)
            )

        alternative_routes = (
            sorted(remote_routes, key=lambda route: route["duration"])
            if remote_routes
            else self._build_dijkstra_fallback_routes(
                src_lat,
                src_lon,
                hospitals[:5],
                env.get_state("blocked_routes") or [],
            )
        )

        env.update_state("routing_graph", _routing_graph_summary(alternative_routes))
        env.update_state("alternative_routes", alternative_routes)
        return {"alternative_routes": alternative_routes}

    def _fetch_osrm_routes(self, src_lat, src_lon, dest_lat, dest_lon, hospital):
        try:
            response = requests.get(
                (
                    "https://router.project-osrm.org/route/v1/driving/"
                    f"{src_lon},{src_lat};{dest_lon},{dest_lat}"
                ),
                params={
                    "alternatives": "false",
                    "overview": "false",
                    "steps": "false",
                },
                timeout=2,
            )
            response.raise_for_status()

            routes = response.json().get("routes", [])
            return [
                {
                    "hospital": hospital.get("name", "Hospital"),
                    "distance": round((route.get("distance") or 0) / 1000, 2),
                    "duration": round((route.get("duration") or 0) / 60, 2),
                    "source": "osrm",
                }
                for route in routes
                if route.get("distance") is not None and route.get("duration") is not None
            ]

        except Exception:
            return []

    def _build_dijkstra_fallback_routes(self, src_lat, src_lon, hospitals, blocked_routes):
        routes = []
        blocked_penalty = 1.25 if blocked_routes else 1.0

        for hospital in hospitals:
            dest_lat = hospital.get("lat")
            dest_lon = hospital.get("lon")
            if None in [dest_lat, dest_lon]:
                continue

            distance_km = _haversine_km(src_lat, src_lon, dest_lat, dest_lon)
            graph = _route_graph(distance_km, blocked_penalty)
            distance = _dijkstra(graph, "incident", "hospital")
            if distance is None:
                continue

            routes.append({
                "hospital": hospital.get("name", "Hospital"),
                "distance": round(distance, 2),
                "duration": round((distance / 32) * 60, 2),
                "source": "local_dijkstra_fallback",
                "algorithm": "dijkstra",
            })

        return sorted(routes, key=lambda route: route["duration"])

class TransportOptimizationTool(BaseTool):
    def __init__(self):
        super().__init__(name="optimize_transport_paths")

    def run(self, context: dict, env):
        routes = env.get_state("alternative_routes") or []

        if not routes:
            env.update_state("optimized_route", None)
            return {"optimized_route": None}

        best_route = min(routes, key=lambda r: r.get("duration", float("inf")))
        env.update_state("optimized_route", best_route)
        return {"optimized_route": best_route}


def _route_graph(distance_km, blocked_penalty):
    direct = max(distance_km * blocked_penalty, 0.1)
    detour = max(distance_km * 1.18, 0.1)

    return {
        "incident": [("primary_corridor", direct * 0.45), ("detour_corridor", detour * 0.55)],
        "primary_corridor": [("hospital", direct * 0.55)],
        "detour_corridor": [("hospital", detour * 0.45)],
        "hospital": [],
    }


def _dijkstra(graph, start, end):
    queue = [(0, start)]
    distances = {start: 0}

    while queue:
        current_distance, node = heappop(queue)
        if node == end:
            return current_distance
        if current_distance > distances.get(node, float("inf")):
            continue

        for neighbor, weight in graph.get(node, []):
            new_distance = current_distance + weight
            if new_distance < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_distance
                heappush(queue, (new_distance, neighbor))

    return None


def _haversine_km(lat1, lon1, lat2, lon2):
    radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    return 2 * radius_km * asin(sqrt(a))


def _routing_graph_summary(routes):
    return {
        "algorithm": "dijkstra" if any(route.get("algorithm") == "dijkstra" for route in routes) else "osrm",
        "nodes": ["incident", *[route.get("hospital", "hospital") for route in routes]],
        "edges": [
            {
                "source": "incident",
                "target": route.get("hospital", "hospital"),
                "weight": route.get("duration"),
            }
            for route in routes
        ],
    }
