from src.executor.base_tools import BaseTool
from src.executor.LLMdef.model import GeminiClient
import requests
import os
import requests
from dotenv import load_dotenv
load_dotenv()
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

            lat, lon = self._geocode_location(location)

            if lat is None or lon is None:
                env.update_state("nearby_hospitals", [])
                return {"nearby_hospitals": []}

            url = (
                "https://api.geoapify.com/v2/places"
                f"?categories=healthcare.hospital"
                f"&filter=circle:{lon},{lat},5000"
                f"&limit=5"
                f"&apiKey={self.geoapify_api_key}"
            )

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            features = data.get("features", [])

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

                hospital_list.append({
                    "name": name,
                    "lat": coords[1],
                    "lon": coords[0]
                })

        except Exception as e:
            print(f"[HospitalDispatchTool ERROR] {e}")
            hospital_list = []

        env.update_state("nearby_hospitals", hospital_list)
        return {"nearby_hospitals": hospital_list}

    def _geocode_location(self, location: str):
        try:
            response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location, "count": 1},
                timeout=5
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            if not results:
                return None, None

            return results[0]["latitude"], results[0]["longitude"]

        except Exception as e:
            print(f"[HospitalDispatchTool Geocoding ERROR] {e}")
            return None, None


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