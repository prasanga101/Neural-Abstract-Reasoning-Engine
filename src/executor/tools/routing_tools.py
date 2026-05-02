from src.executor.base_tools import BaseTool
import heapq
import math
import requests


class BlockedRouteDetectionTool(BaseTool):
    def __init__(self):
        super().__init__(name="detect_blocked_routes")

    def run(self, context: dict, env):
        sensor_data = env.get_state("sensor_data") or {}
        event_coordinates = env.get_state("event_coordinates") or {}
        event_context = env.get_state("event_context") or {}

        src_lat = event_coordinates.get("latitude") or sensor_data.get("latitude")
        src_lon = event_coordinates.get("longitude") or sensor_data.get("longitude")

        if src_lat is None or src_lon is None:
            detection = {
                "status": "missing_coordinates",
                "source": None,
                "method": "osm_nearby_roads_simulated_blockage",
                "note": "Road names require resolved incident coordinates.",
            }
            env.update_state("blocked_routes", [])
            env.update_state("blocked_route_details", [])
            env.update_state("blocked_route_detection", detection)
            return {
                "blocked_routes": [],
                "blocked_route_details": [],
                "blocked_route_detection": detection,
            }

        severity = str(
            event_context.get("severity")
            or context.get("severity")
            or context.get("disaster_severity")
            or ""
        ).lower()
        message = str(
            context.get("message")
            or context.get("prompt")
            or event_context.get("message")
            or ""
        ).lower()

        roads = self._fetch_nearby_roads(src_lat, src_lon)
        details = self._select_blockage_risks(
            roads=roads,
            src_lat=src_lat,
            src_lon=src_lon,
            severity=severity,
            message=message,
        )
        blocked_routes = [road["name"] for road in details]

        detection = {
            "status": "completed" if details else "no_named_roads_found",
            "source": "overpass_osm" if roads else None,
            "method": "osm_nearby_roads_simulated_blockage",
            "simulated": True,
            "radius_m": 2500,
            "candidate_count": len(roads),
            "note": (
                "Road names are real OSM roads near the incident; blockage is "
                "risk-based unless confirmed by a live closure feed."
            ),
        }

        env.update_state("blocked_routes", blocked_routes)
        env.update_state("blocked_route_details", details)
        env.update_state("blocked_route_detection", detection)
        return {
            "blocked_routes": blocked_routes,
            "blocked_route_details": details,
            "blocked_route_detection": detection,
        }

    def _fetch_nearby_roads(self, src_lat, src_lon, radius_m=2500):
        query = f"""
        [out:json][timeout:12];
        (
          way(around:{int(radius_m)},{src_lat},{src_lon})["highway"]["name"];
        );
        out center tags;
        """

        elements = []
        endpoints = (
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
        )

        for endpoint in endpoints:
            try:
                response = requests.post(
                    endpoint,
                    data={"data": query},
                    headers={
                        "User-Agent": (
                            "Neural-Abstract-Reasoning-Engine/1.0 "
                            "(disaster-response-routing)"
                        )
                    },
                    timeout=15,
                )
                response.raise_for_status()
                elements = response.json().get("elements", [])
                break
            except Exception as exc:
                print(
                    "[BlockedRouteDetectionTool Overpass ERROR] "
                    f"{type(exc).__name__}"
                )

        if not elements:
            return []

        roads_by_name = {}

        for element in elements:
            tags = element.get("tags") or {}
            local_name = self._clean_name(tags.get("name"))
            english_name = self._clean_name(tags.get("name:en"))
            name = english_name or local_name
            highway = tags.get("highway")
            center = element.get("center") or {}
            lat = center.get("lat")
            lon = center.get("lon")

            if not name or not highway or lat is None or lon is None:
                continue

            distance_m = self._distance_m(src_lat, src_lon, lat, lon)
            name_key = name.casefold()
            existing = roads_by_name.get(name_key)

            if existing and existing["distance_m"] <= distance_m:
                continue

            roads_by_name[name_key] = {
                "name": name,
                "local_name": local_name,
                "road_class": highway,
                "lat": lat,
                "lon": lon,
                "distance_m": round(distance_m, 1),
                "bridge": tags.get("bridge") in {"yes", "viaduct"},
                "tunnel": tags.get("tunnel") == "yes",
                "oneway": tags.get("oneway") == "yes",
                "source": "overpass_osm",
            }

        return list(roads_by_name.values())

    def _select_blockage_risks(self, roads, src_lat, src_lon, severity, message):
        if not roads:
            return []

        road_priority = {
            "motorway": 10,
            "trunk": 9,
            "primary": 8,
            "secondary": 7,
            "tertiary": 6,
            "unclassified": 4,
            "residential": 3,
            "service": 2,
            "track": 1,
        }
        severity_bonus = 2 if severity in {"major", "severe", "critical", "high"} else 0
        message_bonus = (
            2
            if any(
                term in message
                for term in (
                    "blocked",
                    "bridge",
                    "collapse",
                    "collapsed",
                    "road",
                    "route",
                    "transport",
                )
            )
            else 0
        )

        scored = []
        for road in roads:
            distance = road.get("distance_m") or self._distance_m(
                src_lat, src_lon, road["lat"], road["lon"]
            )
            proximity_score = max(0, 5 - (distance / 500))
            structural_bonus = 2 if road.get("bridge") or road.get("tunnel") else 0
            score = (
                road_priority.get(road.get("road_class"), 2)
                + proximity_score
                + structural_bonus
                + severity_bonus
                + message_bonus
            )
            scored.append((score, distance, road))

        scored.sort(key=lambda item: (-item[0], item[1], item[2]["name"]))
        selected_count = 3 if severity in {"major", "severe", "critical", "high"} else 2

        selected = []
        for score, _distance, road in scored[:selected_count]:
            selected.append(
                {
                    **road,
                    "risk_score": round(score, 2),
                    "simulated_blockage": True,
                    "evidence": (
                        "Selected from nearby named OSM roads using road class, "
                        "proximity, structural features, and disaster context."
                    ),
                }
            )

        return selected

    def _clean_name(self, name):
        if not isinstance(name, str):
            return None
        cleaned = " ".join(name.strip().split())
        return cleaned or None

    def _distance_m(self, src_lat, src_lon, dest_lat, dest_lon):
        radius_m = 6371000
        phi1 = math.radians(src_lat)
        phi2 = math.radians(dest_lat)
        delta_phi = math.radians(dest_lat - src_lat)
        delta_lambda = math.radians(dest_lon - src_lon)

        a = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1)
            * math.cos(phi2)
            * math.sin(delta_lambda / 2) ** 2
        )
        return radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

class AlternativeRouteTool(BaseTool):
    def __init__(self):
        super().__init__(name="identify_alternative_routes")

    def run(self, context: dict, env):
        sensor_data = env.get_state("sensor_data") or {}
        event_coordinates = env.get_state("event_coordinates") or {}
        hospitals = env.get_state("nearby_hospitals") or []

        if not hospitals:
            env.update_state("alternative_routes", [])
            return {"alternative_routes": []}

        src_lat = event_coordinates.get("latitude") or sensor_data.get("latitude")
        src_lon = event_coordinates.get("longitude") or sensor_data.get("longitude")

        if src_lat is None or src_lon is None:
            env.update_state("alternative_routes", [])
            return {"alternative_routes": []}

        routing_graph = self._build_route_graph(src_lat, src_lon, hospitals)
        distances, paths = self._dijkstra(routing_graph, "incident")

        alternative_routes = []

        for hospital_index, hospital in enumerate(hospitals):
            node_id = f"hospital_{hospital_index}"
            route_cost = distances.get(node_id)

            if route_cost is None or math.isinf(route_cost):
                continue

            edge = routing_graph["edges"].get("incident", {}).get(node_id, {})
            distance_m = edge.get("distance")
            duration_s = edge.get("duration")

            alternative_routes.append(
                {
                    "hospital": hospital.get("name"),
                    "hospital_index": hospital_index,
                    "distance": distance_m,
                    "duration": duration_s,
                    "distance_m": distance_m,
                    "duration_s": duration_s,
                    "distance_km": round(distance_m / 1000, 2)
                    if distance_m is not None else None,
                    "duration_min": round(duration_s / 60, 1)
                    if duration_s is not None else None,
                    "route_cost": route_cost,
                    "path": paths.get(node_id, []),
                    "algorithm": "dijkstra",
                    "weight": "distance_m",
                    "source": edge.get("source"),
                    "destination": {
                        "lat": hospital.get("lat"),
                        "lon": hospital.get("lon"),
                    },
                }
            )

        alternative_routes = sorted(
            alternative_routes,
            key=lambda route: route["route_cost"]
        )

        env.update_state("alternative_routes", alternative_routes)
        env.update_state("routing_graph", routing_graph)
        return {"alternative_routes": alternative_routes}

    def _build_route_graph(self, src_lat, src_lon, hospitals):
        nodes = {
            "incident": {
                "type": "incident",
                "lat": src_lat,
                "lon": src_lon,
            }
        }
        edges = {"incident": {}}

        for index, hospital in enumerate(hospitals):
            node_id = f"hospital_{index}"
            dest_lat = hospital.get("lat")
            dest_lon = hospital.get("lon")

            if dest_lat is None or dest_lon is None:
                continue

            nodes[node_id] = {
                "type": "hospital",
                "name": hospital.get("name"),
                "lat": dest_lat,
                "lon": dest_lon,
            }
            edges.setdefault(node_id, {})

            route = self._road_route(src_lat, src_lon, dest_lat, dest_lon)

            if not route:
                distance = self._distance_m(src_lat, src_lon, dest_lat, dest_lon)
                route = {
                    "distance": distance,
                    "duration": self._estimated_duration(distance),
                    "source": "haversine_fallback",
                }

            edges["incident"][node_id] = route

        return {
            "nodes": nodes,
            "edges": edges,
            "algorithm": "dijkstra",
            "weight": "distance_m",
        }

    def _road_route(self, src_lat, src_lon, dest_lat, dest_lon):
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
                timeout=5,
            )
            response.raise_for_status()

            routes = response.json().get("routes", [])
            if not routes:
                return None

            best = routes[0]
            return {
                "distance": best.get("distance"),
                "duration": best.get("duration"),
                "source": "osrm",
            }
        except Exception as exc:
            print(f"[AlternativeRouteTool OSRM ERROR] {type(exc).__name__}")
            return None

    def _dijkstra(self, graph, source):
        distances = {node_id: math.inf for node_id in graph["nodes"]}
        paths = {node_id: [] for node_id in graph["nodes"]}
        distances[source] = 0
        paths[source] = [source]

        queue = [(0, source)]

        while queue:
            current_distance, current_node = heapq.heappop(queue)

            if current_distance > distances[current_node]:
                continue

            for neighbor, edge in graph["edges"].get(current_node, {}).items():
                edge_weight = edge.get("distance")

                if edge_weight is None:
                    continue

                next_distance = current_distance + edge_weight

                if next_distance < distances[neighbor]:
                    distances[neighbor] = next_distance
                    paths[neighbor] = paths[current_node] + [neighbor]
                    heapq.heappush(queue, (next_distance, neighbor))

        return distances, paths

    def _distance_m(self, src_lat, src_lon, dest_lat, dest_lon):
        radius_m = 6371000
        phi1 = math.radians(src_lat)
        phi2 = math.radians(dest_lat)
        delta_phi = math.radians(dest_lat - src_lat)
        delta_lambda = math.radians(dest_lon - src_lon)

        a = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1)
            * math.cos(phi2)
            * math.sin(delta_lambda / 2) ** 2
        )
        return radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _estimated_duration(self, distance_m):
        # Ambulance crawl-speed fallback for damaged-road conditions.
        meters_per_second = 25_000 / 3600
        return distance_m / meters_per_second

class TransportOptimizationTool(BaseTool):
    def __init__(self):
        super().__init__(name="optimize_transport_paths")

    def run(self, context: dict, env):
        routes = env.get_state("alternative_routes") or []

        if not routes:
            env.update_state("optimized_route", None)
            return {"optimized_route": None}

        best_route = min(
            routes,
            key=lambda route: route.get("route_cost", route.get("distance", math.inf))
        )
        env.update_state("optimized_route", best_route)
        return {"optimized_route": best_route}
