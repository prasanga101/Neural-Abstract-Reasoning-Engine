from src.executor.base_tools import BaseTool
from src.executor.geo_utils import geocode_location
import requests

KNOWN_LOCATIONS = {
    "pokhara": (28.2096, 83.9856),
    "kathmandu": (27.7172, 85.3240),
    "lalitpur": (27.6588, 85.3247),
    "bhaktapur": (27.6710, 85.4298),
    "nepal": (28.2096, 83.9856),
}

class DisasterMonitoringTool(BaseTool):
    def __init__(self):
        super().__init__(name="monitor_disaster_activity")

    def run(self, context: dict, env):
        env.update_state("disaster_activity", "ongoing")
        return {"disaster_activity": "ongoing"}


class SensorCollectionTool(BaseTool):
    def __init__(self):
        super().__init__(name="collect_sensor_data")

    def run(self, context: dict, env):
        event_context = env.get_state("event_context") or {}
        location = event_context.get("location", "Kathmandu")
        latitude, longitude = _known_location_coords(location)
        try:
            if latitude is None or longitude is None:
                geo_response = requests.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={"name": location, "count": 1},
                    timeout=5
                )
                geo_data = geo_response.json()
                results = geo_data.get("results", [])
                if results:
                    latitude = results[0].get("latitude")
                    longitude = results[0].get("longitude")

            if latitude is None or longitude is None:
                latitude, longitude = KNOWN_LOCATIONS["pokhara"]

            weather_response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current_weather": True
                },
                timeout=5
            )
            weather_data = weather_response.json()
            current = weather_data.get("current_weather", {})
            sensor_data = {
                "location": location,
                "latitude": latitude,
                "longitude": longitude,
                "resolved_location": resolved_location.get("formatted"),
                "geocode_source": resolved_location.get("source"),
                "temperature": current.get("temperature"),
                "windspeed": current.get("windspeed")
            }
        except Exception:
            if latitude is None or longitude is None:
                latitude, longitude = KNOWN_LOCATIONS["pokhara"]
            sensor_data = {
                "location": location,
                "latitude": latitude,
                "longitude": longitude,
                "temperature": 25,
                "humidity": 70,
                "wind_speed": 10
            }
        env.update_state("sensor_data", sensor_data)
        return {"sensor_data": sensor_data}


class DisasterAnalysisTool(BaseTool):
    def __init__(self):
        super().__init__(name="analyze_disaster_data")

    def run(self, context: dict, env):
        event_context = env.get_state("event_context") or {}
        severity = event_context.get("severity") or env.get_state("injury_severity") or "low"

        if severity in ("high", "critical"):
            analysis_result = "high_risk"
        elif severity == "moderate":
            analysis_result = "medium_risk"
        else:
            analysis_result = "low_risk"

        env.update_state("disaster_analysis", analysis_result)
        return {"disaster_analysis": analysis_result}


class SituationReportTool(BaseTool):
    def __init__(self):
        super().__init__(name="generate_situation_reports")

    def run(self, context: dict, env):
        analysis = env.get_state("disaster_analysis") or "unknown"
        activity = env.get_state("disaster_activity") or "unknown"

        report = {
            "status": activity,
            "risk_level": analysis
        }

        env.update_state("situation_report", report)
        return {"situation_report": report}


def _known_location_coords(location):
    normalized = str(location or "").strip().lower()
    for key, coords in KNOWN_LOCATIONS.items():
        if key in normalized:
            return coords
    return None, None
