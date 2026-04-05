from src.executor.base_tools import BaseTool
from src.executor.LLMdef.model import GeminiClient
import requests



class HospitalDispatchTool(BaseTool):
    def __init__(self):
        super().__init__(name="identify_nearest_hospitals")

    def run(self, context: dict, env):
        event_context = env.get_state("event_context") or {}
        location = event_context.get("location", "Kathmandu")

        if not isinstance(location, str) or not location.strip():
            location = "Kathmandu"

        location = location.strip()

        try:
            geo_response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location, "count": 1},
                timeout=5
            )
            geo_response.raise_for_status()
            geo_data = geo_response.json()
            results = geo_data.get("results", [])

            if not results:
                env.update_state("nearby_hospitals", [])
                return {"nearby_hospitals": []}

            lat = results[0]["latitude"]
            lon = results[0]["longitude"]

            query = f"""
[out:json][timeout:25];
(
  node["amenity"~"hospital|clinic|pharmacy|healthcare"](around:50000,{lat},{lon});
  way["amenity"~"hospital|clinic|pharmacy|healthcare"](around:50000,{lat},{lon});
  relation["amenity"~"hospital|clinic|pharmacy|healthcare"](around:50000,{lat},{lon});
);
out center;
"""

            overpass_response = requests.get(
                "https://overpass-api.de/api/interpreter",
                params={"data": query},
                timeout=15
            )
            overpass_response.raise_for_status()
            data = overpass_response.json()
            hospitals = data.get("elements", [])

            hospital_list = []
            for h in hospitals[:5]:
                if h.get("type") == "node":
                    h_lat = h.get("lat")
                    h_lon = h.get("lon")
                else:
                    center = h.get("center", {})
                    h_lat = center.get("lat")
                    h_lon = center.get("lon")

                hospital_list.append({
                    "name":  h.get("tags", {}).get("name", "Unnamed Hospital"),
                    "lat": h_lat,
                    "lon": h_lon
                })

            # optional fallback for demo stability
            if not hospital_list and "mumbai" in location.lower():
                hospital_list = [
                    {"name": "Kokilaben Hospital", "lat": 19.136, "lon": 72.825},
                    {"name": "Lilavati Hospital", "lat": 19.051, "lon": 72.829},
                    {"name": "Nanavati Hospital", "lat": 19.095, "lon": 72.840}
                ]

        except Exception:
            hospital_list = []

        env.update_state("nearby_hospitals", hospital_list)
        return {"nearby_hospitals": hospital_list}


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