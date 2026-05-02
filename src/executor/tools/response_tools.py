from src.executor.base_tools import BaseTool
from src.executor.LLMdef.model import GeminiClient
from src.executor.geo_utils import geocode_location
import math
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env")

class HospitalDispatchTool(BaseTool):
    def __init__(self):
        super().__init__(name="identify_nearest_hospitals")
        self.geoapify_api_key = os.getenv("GEOAPIFY_API_KEY")

    def run(self, context: dict, env):
        event_context = env.get_state("event_context") or {}
        location = event_context.get("location", "Kathmandu")

        if not isinstance(location, str) or not location.strip():
            location = "Kathmandu"

        location = location.strip()

        hospital_list = []

        try:
            if not self.geoapify_api_key:
                raise ValueError("GEOAPIFY_API_KEY is not set")

            resolved_location = geocode_location(location, self.geoapify_api_key)

            if not resolved_location:
                env.update_state("nearby_hospitals", [])
                return {"nearby_hospitals": []}

            lat = resolved_location["latitude"]
            lon = resolved_location["longitude"]

            env.update_state("resolved_location", resolved_location)
            env.update_state("event_coordinates", {
                "latitude": lat,
                "longitude": lon,
                "location": resolved_location.get("formatted") or location,
                "source": resolved_location.get("source"),
            })

            url = (
                "https://api.geoapify.com/v2/places"
                f"?categories=healthcare.hospital"
                f"&filter=circle:{lon},{lat},12000"
                f"&bias=proximity:{lon},{lat}"
                f"&limit=50"
                f"&apiKey={self.geoapify_api_key}"
            )

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            features = data.get("features", [])

            candidates = []
            fallback_candidates = []

            for feature in features:
                props = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                coords = geometry.get("coordinates", [])

                name = (
                    props.get("name")
                    or props.get("formatted")
                    or ""
                ).strip()

                if not name or len(coords) < 2:
                    continue

                candidate = {
                    "name": name,
                    "lat": coords[1],
                    "lon": coords[0],
                    "distance_m": props.get("distance") or self._distance_m(
                        lat, lon, coords[1], coords[0]
                    ),
                    "categories": props.get("categories", []),
                    "address": props.get("formatted"),
                }

                score = self._hospital_quality_score(candidate)
                candidate["confidence"] = score

                if score >= 2:
                    candidates.append(candidate)
                elif score >= 0:
                    fallback_candidates.append(candidate)

            ranked = sorted(
                candidates or fallback_candidates,
                key=lambda item: (-item["confidence"], item["distance_m"])
            )

            if len(candidates) < 3:
                ranked = self._merge_hospital_candidates(
                    ranked,
                    self._fetch_osm_hospitals(lat, lon)
                )

            hospital_list = [
                {
                    "name": item["name"],
                    "lat": item["lat"],
                    "lon": item["lon"],
                    "distance_m": round(item["distance_m"], 1),
                    "confidence": item["confidence"],
                    "categories": item["categories"],
                    "address": item["address"],
                }
                for item in ranked[:5]
            ]

        except Exception as e:
            print(f"[HospitalDispatchTool ERROR] {e}")
            hospital_list = []

        env.update_state("nearby_hospitals", hospital_list)
        return {"nearby_hospitals": hospital_list}

    def _hospital_quality_score(self, candidate):
        name = candidate["name"].casefold()
        categories = " ".join(candidate.get("categories") or []).casefold()
        text = f"{name} {categories}"

        reject_terms = [
            "pharmacy",
            "medical hall",
            "health post",
            "health centre",
            "health center",
            "basic health",
            "clinic",
            "polyclinic",
            "dental",
            "diagnostic",
            "rehabilitation",
            "ayurveda",
            "मेडिकल हल",
            "स्वास्थ्य केन्द्र",
            "स्वास्थ्य केंद्र",
            "क्लिनिक",
            "फार्मेसी",
            "दन्त",
            "आयुर्वेद",
        ]
        strong_terms = [
            "hospital",
            "medical college",
            "teaching hospital",
            "trauma",
            "emergency",
            "अस्पताल",
        ]

        if any(term in text for term in reject_terms):
            return -3

        score = 0

        if "healthcare.hospital" in categories:
            score += 2

        for term in strong_terms:
            if term in text:
                score += 3

        distance_m = candidate.get("distance_m") or 0
        if distance_m <= 3000:
            score += 1
        elif distance_m > 9000:
            score -= 1

        return score

    def _fetch_osm_hospitals(self, lat, lon, radius_m=12000):
        query = f"""
[out:json][timeout:12];
(
  node(around:{radius_m},{lat},{lon})["amenity"="hospital"];
  way(around:{radius_m},{lat},{lon})["amenity"="hospital"];
  relation(around:{radius_m},{lat},{lon})["amenity"="hospital"];
  node(around:{radius_m},{lat},{lon})["healthcare"="hospital"];
  way(around:{radius_m},{lat},{lon})["healthcare"="hospital"];
  relation(around:{radius_m},{lat},{lon})["healthcare"="hospital"];
);
out center tags;
"""

        try:
            response = requests.post(
                "https://overpass-api.de/api/interpreter",
                data={"data": query},
                timeout=15,
            )
            response.raise_for_status()
            elements = response.json().get("elements", [])
        except Exception as exc:
            print(f"[HospitalDispatchTool OSM fallback ERROR] {exc}")
            return []

        candidates = []

        for element in elements:
            tags = element.get("tags", {})
            name = (tags.get("name") or tags.get("name:en") or "").strip()
            center = element.get("center") or {}
            item_lat = element.get("lat") or center.get("lat")
            item_lon = element.get("lon") or center.get("lon")

            if not name or item_lat is None or item_lon is None:
                continue

            candidate = {
                "name": name,
                "lat": item_lat,
                "lon": item_lon,
                "distance_m": self._distance_m(lat, lon, item_lat, item_lon),
                "categories": ["osm.healthcare.hospital"],
                "address": tags.get("addr:full") or tags.get("addr:street"),
            }
            candidate["confidence"] = max(3, self._hospital_quality_score(candidate))
            candidates.append(candidate)

        return sorted(candidates, key=lambda item: (-item["confidence"], item["distance_m"]))

    def _merge_hospital_candidates(self, primary, secondary):
        merged = []
        seen = set()

        for item in [*primary, *secondary]:
            key = self._hospital_key(item["name"])
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)

        return sorted(merged, key=lambda item: (-item["confidence"], item["distance_m"]))

    def _hospital_key(self, name):
        return " ".join(name.casefold().replace("&", "and").split())

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


class RescueTeamDeploymentTool(BaseTool):
    def __init__(self):
        super().__init__(name="deploy_rescue_teams")

    def run(self, context: dict, env):
        infrastructure_damage = env.get_state("infrastructure_damage") or {}
        damage_assessment = (
            infrastructure_damage.get("damage_level")
            or env.get_state("damage_assessment")
            or "unknown"
        )
        trapped_victims = env.get_state("trapped_victims") or {}
        trapped_count = trapped_victims.get("estimated_trapped_victims", 0)
        teams_available = env.get_state("available_rescue_teams") or 10

        if damage_assessment == "severe":
            teams_needed = max(4, trapped_count // 25)
        elif damage_assessment == "moderate":
            teams_needed = max(2, trapped_count // 40)
        else:
            teams_needed = max(1, trapped_count // 75)

        rescue_teams_allocated = min(teams_available, teams_needed)
        env.update_state("available_rescue_teams", teams_available - rescue_teams_allocated)
        env.update_state("rescue_teams_allocated", rescue_teams_allocated)

        return {
            "rescue_teams_allocated": rescue_teams_allocated,
            "teams_needed": teams_needed,
            "teams_remaining": teams_available - rescue_teams_allocated,
            "basis": {
                "damage_assessment": damage_assessment,
                "estimated_trapped_victims": trapped_count,
            },
        }


class DisasterZoneScanTool(BaseTool):
    def __init__(self):
        super().__init__(name="scan_disaster_zone")

    def run(self, context: dict, env):
        event_context = env.get_state("event_context") or {}
        coordinates = env.get_state("event_coordinates") or {}
        infrastructure_damage = env.get_state("infrastructure_damage") or {}
        sensor_data = env.get_state("sensor_data") or {}
        message = (env.get_state("message") or "").lower()

        severity = event_context.get("severity", "moderate")
        damage_level = infrastructure_damage.get("damage_level", "unknown")

        if severity == "high" or damage_level == "severe":
            scan_radius_km = 3.0
            priority = "urgent"
        elif severity == "moderate" or damage_level == "moderate":
            scan_radius_km = 1.5
            priority = "high"
        else:
            scan_radius_km = 0.75
            priority = "normal"

        hazards = []
        if "earthquake" in message or event_context.get("disaster_type") == "earthquake":
            hazards.extend(["aftershock_risk", "structural_collapse"])
        if "flood" in message:
            hazards.append("inundation")
        if "fire" in message:
            hazards.append("fire_spread")
        if sensor_data.get("windspeed", 0) and sensor_data.get("windspeed", 0) > 20:
            hazards.append("high_wind")

        scan = {
            "center": {
                "latitude": coordinates.get("latitude"),
                "longitude": coordinates.get("longitude"),
                "location": coordinates.get("location") or event_context.get("location"),
            },
            "radius_km": scan_radius_km,
            "priority": priority,
            "hazards": list(dict.fromkeys(hazards)) or ["access_disruption"],
            "recommended_methods": ["drone_survey", "field_team_sweep", "hospital_access_check"],
        }

        env.update_state("disaster_zone_scan", scan)
        return {"disaster_zone_scan": scan}


class TrappedVictimLocationTool(BaseTool):
    def __init__(self):
        super().__init__(name="locate_trapped_victims")

    def run(self, context: dict, env):
        scan = env.get_state("disaster_zone_scan") or {}
        infrastructure_damage = env.get_state("infrastructure_damage") or {}
        estimated_casualties = env.get_state("estimated_casualties") or 0
        message = (env.get_state("message") or "").lower()

        damage_level = infrastructure_damage.get("damage_level", "unknown")
        trapped_ratio = 0.08

        if damage_level == "severe":
            trapped_ratio = 0.22
        elif damage_level == "moderate":
            trapped_ratio = 0.14

        if any(term in message for term in ["trapped", "collapsed", "rubble", "buried"]):
            trapped_ratio += 0.08

        estimated_trapped = int(max(0, estimated_casualties * trapped_ratio))
        center = scan.get("center") or {}
        radius_km = scan.get("radius_km") or 1.0

        hotspots = [
            {
                "zone": "inner_impact_zone",
                "estimated_victims": int(estimated_trapped * 0.6),
                "radius_km": round(radius_km * 0.35, 2),
                "priority": "critical" if estimated_trapped else "monitor",
            },
            {
                "zone": "outer_impact_zone",
                "estimated_victims": estimated_trapped - int(estimated_trapped * 0.6),
                "radius_km": radius_km,
                "priority": "high" if estimated_trapped else "monitor",
            },
        ]

        trapped_victims = {
            "center": center,
            "estimated_trapped_victims": estimated_trapped,
            "confidence": "medium" if estimated_casualties else "low",
            "hotspots": hotspots,
        }

        env.update_state("trapped_victims", trapped_victims)
        return {"trapped_victims": trapped_victims}


class SupplySourceIdentificationTool(BaseTool):
    def __init__(self):
        super().__init__(name="identify_supply_sources")

    def run(self, context: dict, env):
        event_context = env.get_state("event_context") or "unknown"

        if event_context == "urban":
            supply_sources = ["local_warehouses", "nearby_cities"]
        elif event_context == "rural":
            supply_sources = ["regional_centers", "neighboring_towns"]
        else:
            supply_sources = ["national_suppliers"]

        env.update_state("supply_sources_identified", supply_sources)

        return {"supply_sources_identified": supply_sources}


class InformationRetrievalTool(BaseTool):
    def __init__(self):
        super().__init__(name="retrieve_disaster_information")
        self.client = GeminiClient()

    def run(self, context: dict, env):
        message = env.get_state("message") or ""

        prompt = f"""
You are a disaster intelligence assistant.

Extract key disaster information from the message.

Message:
{message}

Return ONLY valid JSON:
{{
  "summary": "short summary",
  "disaster_type": "earthquake | flood | tsunami | fire | landslide | unknown",
  "location": "string",
  "affected_population": "low | medium | high | unknown",
  "immediate_needs": ["medical", "shelter", "food", "water", "rescue"]
}}
"""

        result = self.client.generate_json(prompt)

        if "error" in result:
            disaster_info = {
                "summary": message,
                "disaster_type": "unknown",
                "location": "unknown",
                "affected_population": "unknown",
                "immediate_needs": []
            }
        else:
            disaster_info = {
                "summary": result.get("summary", message),
                "disaster_type": result.get("disaster_type", "unknown"),
                "location": result.get("location", "unknown"),
                "affected_population": result.get("affected_population", "unknown"),
                "immediate_needs": result.get("immediate_needs", [])
            }

        env.update_state("disaster_information", disaster_info)
        return {"disaster_information": disaster_info}
class InformationSummaryTool(BaseTool):
    def __init__(self):
        super().__init__(name="generate_information_summary")

    def run(self, context: dict, env):
        event_context = env.get_state("event_context") or {}
        disaster_information = env.get_state("disaster_information") or {}
        situation_report = env.get_state("situation_report") or {}
        population_demands = env.get_state("population_demands") or {}
        optimized_route = env.get_state("optimized_route") or {}
        hospitals = env.get_state("nearby_hospitals") or []

        summary = {
            "headline": disaster_information.get("summary") or env.get_state("message"),
            "location": event_context.get("location") or disaster_information.get("location"),
            "disaster_type": event_context.get("disaster_type") or disaster_information.get("disaster_type"),
            "severity": event_context.get("severity", "unknown"),
            "risk_level": situation_report.get("risk_level", "unknown"),
            "affected_population": population_demands.get("estimated_affected_population"),
            "top_hospital": optimized_route.get("hospital") or (hospitals[0].get("name") if hospitals else None),
            "best_route": {
                "distance_km": optimized_route.get("distance_km"),
                "duration_min": optimized_route.get("duration_min"),
            } if optimized_route else None,
            "immediate_needs": disaster_information.get("immediate_needs", []),
        }

        env.update_state("information_summary", summary)
        return {"information_summary": summary}


class PublicReportUpdateTool(BaseTool):
    def __init__(self):
        super().__init__(name="update_public_reports")

    def run(self, context: dict, env):
        summary = env.get_state("information_summary") or {}
        blocked_routes = env.get_state("blocked_routes") or []
        shelters = env.get_state("available_shelters")
        ambulances = env.get_state("available_ambulances")

        public_report = {
            "status": "active",
            "location": summary.get("location"),
            "message": self._compose_public_message(summary, blocked_routes),
            "public_guidance": [
                "Avoid damaged buildings and blocked corridors.",
                "Prioritize emergency medical transport for critical injuries.",
                "Use verified shelters and official route updates.",
            ],
            "resource_snapshot": {
                "ambulances_available": ambulances,
                "shelters_available": shelters,
                "blocked_routes": blocked_routes,
            },
        }

        env.update_state("public_report", public_report)
        return {"public_report": public_report}

    def _compose_public_message(self, summary, blocked_routes):
        location = summary.get("location") or "the affected area"
        disaster_type = summary.get("disaster_type") or "disaster"
        severity = summary.get("severity") or "unknown"
        hospital = summary.get("top_hospital")

        message = f"{severity.title()} {disaster_type} response is active in {location}."

        if hospital:
            message += f" Priority medical routing is currently directed toward {hospital}."

        if blocked_routes:
            message += f" Blocked corridors reported: {', '.join(blocked_routes)}."

        return message


class HospitalCapacityCoordinationTool(BaseTool):
    def __init__(self):
        super().__init__(name="coordinate_hospital_capacity")

    def run(self, context: dict, env):
        hospitals = env.get_state("nearby_hospitals") or []
        injury_severity = env.get_state("injury_severity") or "unknown"
        estimated_casualties = env.get_state("estimated_casualties") or 0

        if not hospitals:
            capacity_plan = {
                "status": "no_hospitals_available",
                "assignments": [],
                "overflow_required": estimated_casualties > 0,
            }
            env.update_state("hospital_capacity_plan", capacity_plan)
            return {"hospital_capacity_plan": capacity_plan}

        critical_share = 0.35 if injury_severity == "critical" else 0.15
        critical_patients = int(estimated_casualties * critical_share)
        remaining_patients = max(0, estimated_casualties - critical_patients)
        assignments = []

        for index, hospital in enumerate(hospitals):
            base_capacity = max(10, 45 - index * 5)
            critical_capacity = max(2, int(base_capacity * 0.25))
            assigned_critical = min(critical_patients, critical_capacity)
            critical_patients -= assigned_critical
            assigned_general = min(remaining_patients, base_capacity - assigned_critical)
            remaining_patients -= assigned_general

            assignments.append({
                "hospital": hospital.get("name"),
                "distance_m": hospital.get("distance_m"),
                "estimated_capacity": base_capacity,
                "critical_patients": assigned_critical,
                "general_patients": assigned_general,
                "status": "receiving" if assigned_critical or assigned_general else "standby",
            })

        capacity_plan = {
            "status": "overflow_required" if critical_patients or remaining_patients else "balanced",
            "assignments": assignments,
            "unassigned_critical": critical_patients,
            "unassigned_general": remaining_patients,
        }

        env.update_state("hospital_capacity_plan", capacity_plan)
        return {"hospital_capacity_plan": capacity_plan}


class ReliefTeamDispatchTool(BaseTool):
    def __init__(self):
        super().__init__(name="dispatch_relief_teams")
    def run(self,context:dict,env):
        estimated_casualties=env.get_state("estimated_casualties")or 0
        resources=env.get_state("relief_resources_allocated")or 0
        teams_available=env.get_state("available_rescue_teams")or 10
        teams_needed=max(1,estimated_casualties//50)
        if resources>1000:
            teams_needed+=2
        max_dispatch_limit=max(1,int(teams_available*0.6))
        teams_dispatched=min(teams_needed,max_dispatch_limit,teams_available)
        remaining=teams_available-teams_dispatched
        env.update_state("available_rescue_teams",remaining)
        return{
            "relief_teams_dispatched":teams_dispatched,
            "teams_remaining":remaining,
            "teams_needed":teams_needed,
            "dispatch_limit":max_dispatch_limit
        }
