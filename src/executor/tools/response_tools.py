from src.executor.base_tools import BaseTool
from src.executor.LLMdef.model import OllamaClient
import requests
import os
from dotenv import load_dotenv
load_dotenv()

KNOWN_HOSPITALS = [
    {"name": "Manipal Teaching Hospital", "lat": 28.2377, "lon": 83.9956, "city": "pokhara"},
    {"name": "Gandaki Medical College Teaching Hospital", "lat": 28.2096, "lon": 83.9856, "city": "pokhara"},
    {"name": "Western Regional Hospital", "lat": 28.2184, "lon": 83.9938, "city": "pokhara"},
    {"name": "Charak Memorial Hospital", "lat": 28.2097, "lon": 83.9859, "city": "pokhara"},
    {"name": "Bir Hospital", "lat": 27.7046, "lon": 85.3131, "city": "kathmandu"},
    {"name": "Tribhuvan University Teaching Hospital", "lat": 27.7365, "lon": 85.3302, "city": "kathmandu"},
    {"name": "Patan Hospital", "lat": 27.6687, "lon": 85.3206, "city": "lalitpur"},
]

KNOWN_LOCATIONS = {
    "pokhara": (28.2096, 83.9856),
    "kathmandu": (27.7172, 85.3240),
    "lalitpur": (27.6588, 85.3247),
    "bhaktapur": (27.6710, 85.4298),
    "nepal": (28.2096, 83.9856),
}


class HospitalDispatchTool(BaseTool):
    def __init__(self):
        super().__init__(name="identify_nearest_hospitals")
        self.geoapify_api_key = os.getenv("GEOAPIFY_API_KEY")
        self.client = OllamaClient()

    def run(self, context: dict, env):
        event_context = env.get_state("event_context") or {}
        location = event_context.get("location", "Kathmandu")
        if not isinstance(location, str) or not location.strip():
            location = "Kathmandu"
        location = location.strip()

        hospital_list = (
            self._fetch_from_api(location)
            or self._fetch_from_known_locations(location)
            or self._fetch_from_llm(location)
        )

        env.update_state("available_hospitals", hospital_list)
        env.update_state("nearby_hospitals", hospital_list)
        return {
            "nearby_hospitals": hospital_list,
            "available_hospitals": hospital_list,
        }

    def _fetch_from_api(self, location: str) -> list:
        try:
            if not self.geoapify_api_key:
                return []

            lat, lon = self._geocode_location(location)
            if lat is None or lon is None:
                return []

            url = (
                "https://api.geoapify.com/v2/places"
                f"?categories=healthcare.hospital"
                f"&filter=circle:{lon},{lat},15000"
                f"&limit=5"
                f"&apiKey={self.geoapify_api_key}"
            )
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            hospitals = []
            for feature in response.json().get("features", []):
                props = feature.get("properties", {})
                coords = feature.get("geometry", {}).get("coordinates", [])
                name = (props.get("name") or props.get("formatted") or "").strip()
                if not name or len(coords) < 2:
                    continue
                hospitals.append({"name": name, "lat": coords[1], "lon": coords[0]})

            return hospitals

        except Exception as e:
            print(f"[HospitalDispatchTool API ERROR] {e}")
            return []

    def _fetch_from_llm(self, location: str) -> list:
        try:
            prompt = f"""You are a disaster response expert.

List up to 5 real hospitals or medical facilities near {location}.

Return ONLY a valid JSON array (no extra text):
[
  {{"name": "Hospital Name", "lat": 0.0, "lon": 0.0}},
  ...
]
"""
            result = self.client.generate_json(prompt)
            if isinstance(result, list):
                return [
                    {
                        "name": h.get("name", "Hospital"),
                        "lat": float(h.get("lat", 0.0)),
                        "lon": float(h.get("lon", 0.0)),
                        "source": "llm",
                    }
                    for h in result
                    if isinstance(h, dict) and h.get("name")
                ]
        except Exception as e:
            print(f"[HospitalDispatchTool LLM ERROR] {e}")
        return []

    def _geocode_location(self, location: str):
        normalized = location.strip().lower()
        for key, coords in KNOWN_LOCATIONS.items():
            if key in normalized:
                return coords

        try:
            response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location, "count": 1},
                timeout=5
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            if not results:
                return None, None
            return results[0]["latitude"], results[0]["longitude"]
        except Exception as e:
            print(f"[HospitalDispatchTool Geocoding ERROR] {e}")
            return None, None

    def _fetch_from_known_locations(self, location: str) -> list:
        lat, lon = self._geocode_location(location)
        if lat is None or lon is None:
            return []

        hospitals = []
        for hospital in KNOWN_HOSPITALS:
            distance_km = _haversine_km(lat, lon, hospital["lat"], hospital["lon"])
            hospitals.append({
                "name": hospital["name"],
                "lat": hospital["lat"],
                "lon": hospital["lon"],
                "distance_km": round(distance_km, 2),
                "source": "local_fallback",
            })

        return sorted(hospitals, key=lambda hospital: hospital["distance_km"])[:5]


def _haversine_km(lat1, lon1, lat2, lon2):
    from math import asin, cos, radians, sin, sqrt

    radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    return 2 * radius_km * asin(sqrt(a))


class RescueTeamAllocationTool(BaseTool):
    def __init__(self):
        super().__init__(name="deploy_rescue_teams")

    def run(self, context: dict, env):
        damage_assessment = env.get_state("damage_assessment") or "unknown"
        population_needs = env.get_state("population_needs") or "low"

        if damage_assessment == "severe" and population_needs == "high":
            rescue_teams_allocated = 5
        elif damage_assessment == "moderate":
            rescue_teams_allocated = 3
        else:
            rescue_teams_allocated = 1

        env.update_state("rescue_teams_allocated", rescue_teams_allocated)

        return {"rescue_teams_allocated": rescue_teams_allocated}


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

    def run(self, context: dict, env):
        # Derive from event_context already set by EventContextAnalysisTool — no LLM call needed.
        message = env.get_state("message") or ""
        event_context = env.get_state("event_context") or {}

        severity = event_context.get("severity", "low")
        affected_population = (
            "high" if severity == "high"
            else "medium" if severity == "moderate"
            else "low"
        )

        disaster_type = event_context.get("disaster_type", "unknown")
        immediate_needs = ["medical", "shelter", "rescue"]
        if disaster_type in ("flood", "tsunami"):
            immediate_needs.append("water")
        if severity == "high":
            immediate_needs.append("food")

        disaster_info = {
            "summary": message[:200],
            "disaster_type": disaster_type,
            "location": event_context.get("location", "unknown"),
            "affected_population": affected_population,
            "immediate_needs": immediate_needs,
        }

        env.update_state("disaster_information", disaster_info)
        return {"disaster_information": disaster_info}
class RescueTeamAllocationTool(BaseTool):
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
