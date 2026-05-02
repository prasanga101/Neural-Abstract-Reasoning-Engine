from src.executor.base_tools import BaseTool
from src.executor.geo_utils import geocode_location
import requests

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
        try:
            resolved_location = env.get_state("resolved_location") or geocode_location(location)
            if not resolved_location:
                raise ValueError(f"Could not geocode location: {location}")

            latitude = resolved_location["latitude"]
            longitude = resolved_location["longitude"]

            env.update_state("resolved_location", resolved_location)
            env.update_state("event_coordinates", {
                "latitude": latitude,
                "longitude": longitude,
                "location": resolved_location.get("formatted") or location,
                "source": resolved_location.get("source"),
            })

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
            sensor_data = {
                "location": location,
                "latitude": None,
                "longitude": None,
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
        sensor_data = env.get_state("sensor_data") or {}

        if sensor_data.get("temperature", 0) > 28 and sensor_data.get("wind_speed", 0) > 15:
            analysis_result = "high_risk"
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
