from src.executor.base_tools import BaseTool
import requests
class BlockedRouteDetectionTool(BaseTool):
    def __init__(self):
        super().__init__(name="detect_blocked_routes")

    def run(self, context: dict, env):
        # Simulate blocked route detection
        blocked_routes = ["Route A", "Route C"]
        env.update_state("blocked_routes", blocked_routes)
        return {"blocked_routes": blocked_routes}

class AlternativeRouteTool(BaseTool):
    def __init__(self):
        super().__init__(name="identify_alternative_routes")

    def run(self, context: dict, env):
        sensor_data = env.get_state("sensor_data") or {}
        hospitals = env.get_state("nearby_hospitals") or []

        if not sensor_data or not hospitals:
            env.update_state("alternative_routes", [])
            return {"alternative_routes": []}

        src_lat = sensor_data.get("latitude")
        src_lon = sensor_data.get("longitude")

        dest = hospitals[0]
        dest_lat = dest.get("lat")
        dest_lon = dest.get("lon")

        if None in [src_lat, src_lon, dest_lat, dest_lon]:
            env.update_state("alternative_routes", [])
            return {"alternative_routes": []}

        try:
            response = requests.get(
                f"https://router.project-osrm.org/route/v1/driving/{src_lon},{src_lat};{dest_lon},{dest_lat}",
                params={
                    "alternatives": "true",
                    "overview": "false",
                    "steps": "false"
                },
                timeout=5
            )

            data = response.json()
            routes = data.get("routes", [])

            alternative_routes = [
                {
                    "distance": route.get("distance"),
                    "duration": route.get("duration")
                }
                for route in routes
            ]

        except Exception:
            alternative_routes = []

        env.update_state("alternative_routes", alternative_routes)
        return {"alternative_routes": alternative_routes}

class TransportOptimizationTool(BaseTool):
    def __init__(self):
        super().__init__(name="optimize_transport_paths")

    def run(self, context: dict, env):
        routes = env.get_state("alternative_routes") or []

        if not routes:
            env.update_state("optimized_route", None)
            return {"optimized_route": None}

        best_route = min(routes, key=lambda r: r["duration"])
        env.update_state("optimized_route", best_route)
        return {"optimized_route": best_route}