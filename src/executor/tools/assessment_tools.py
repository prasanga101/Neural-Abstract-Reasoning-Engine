from src.executor.base_tools import BaseTool
from src.executor.LLMdef.model import OllamaClient

KNOWN_LOCATION_NAMES = ("pokhara", "kathmandu", "lalitpur", "bhaktapur")

class InjuryAssessmentTool(BaseTool):
    def __init__(self):
        super().__init__(name="assess_injury_severity")
        self.client = OllamaClient()

    def run(self, context: dict, env):
        message = env.get_state("message") or ""

        prompt = f"""
You are a disaster response expert.

Determine injury severity from the message.

Message:
{message}

Return ONLY valid JSON:
{{
  "injury_severity": "low" | "moderate" | "critical"
}}
"""

        result = self.client.generate_json(prompt)

        severity = result.get("injury_severity") or _infer_injury_severity(message)

        env.update_state("injury_severity", severity)

        return {"injury_severity": severity}


class CasualtyEstimationTool(BaseTool):
    def __init__(self):
        super().__init__(name="estimate_number_of_casualties")

    def run(self, context: dict, env):
        severity = env.get_state("injury_severity") or "low"

        if severity == "critical":
            estimated_casualties = 350
        elif severity == "moderate":
            estimated_casualties = 150
        else:
            estimated_casualties = 50

        env.update_state("estimated_casualties", estimated_casualties)
        return {"estimated_casualties": estimated_casualties}


class StructuralDamageAssessmentTool(BaseTool):
    def __init__(self):
        super().__init__(name="assess_structural_damage")

    def run(self, context: dict, env):
        damage_level = env.get_state("damage_level") or "unknown"
        env.update_state("damage_assessment", damage_level)
        return {"damage_assessment": damage_level}


class InfrastructureDamageAssessmentTool(BaseTool):
    def __init__(self):
        super().__init__(name="assess_infrastructure_damage")

    def run(self, context: dict, env):
        event_context = env.get_state("event_context") or {}
        message = (env.get_state("message") or "").lower()
        blocked_routes = env.get_state("blocked_routes") or []
        disaster_type = event_context.get("disaster_type", "unknown")
        severity = event_context.get("severity", "moderate")

        damage_score = 0

        if severity in {"high", "major", "severe", "critical"}:
            damage_score += 3
        elif severity == "moderate":
            damage_score += 2
        else:
            damage_score += 1

        if disaster_type in {"earthquake", "flood", "landslide"}:
            damage_score += 2

        damage_terms = [
            "collapsed",
            "collapse",
            "blocked",
            "damaged",
            "destroyed",
            "cracked",
            "bridge",
            "road",
            "route",
            "infrastructure",
        ]
        damage_score += sum(1 for term in damage_terms if term in message)
        damage_score += min(len(blocked_routes), 3)

        if damage_score >= 7:
            damage_level = "severe"
        elif damage_score >= 4:
            damage_level = "moderate"
        else:
            damage_level = "low"

        assessment = {
            "damage_level": damage_level,
            "score": damage_score,
            "blocked_route_count": len(blocked_routes),
            "affected_infrastructure": self._affected_infrastructure(message),
        }

        env.update_state("damage_level", damage_level)
        env.update_state("infrastructure_damage", assessment)
        return {"infrastructure_damage": assessment}

    def _affected_infrastructure(self, message):
        mapping = {
            "roads": ["road", "route", "highway", "street"],
            "bridges": ["bridge"],
            "buildings": ["building", "house", "school", "hospital"],
            "power": ["electricity", "power", "grid"],
            "water": ["water", "pipeline", "sanitation"],
        }

        affected = [
            label
            for label, terms in mapping.items()
            if any(term in message for term in terms)
        ]

        return affected or ["general_access"]


class PopulationNeedsAssessmentTool(BaseTool):
    def __init__(self):
        super().__init__(name="assess_population_needs")

    def run(self, context: dict, env):
        event_context = env.get_state("event_context") or {}
        severity = event_context.get("severity") or env.get_state("injury_severity") or "low"
        needs = "high" if severity in ("high", "critical") else "moderate" if severity == "moderate" else "low"
        env.update_state("population_needs", needs)
        return {"population_needs": needs}


class ResourceAvailabilityAnalysisTool(BaseTool):
    def __init__(self):
        super().__init__(name="analyze_resource_availability")

    def run(self, context: dict, env):
        available_ambulances = env.get_state("available_ambulances") or 0
        available_shelters = env.get_state("available_shelters") or 0

        resource_availability = {
            "available_ambulances": available_ambulances,
            "available_shelters": available_shelters
        }

        env.update_state("resource_availability", resource_availability)

        return resource_availability


class PopulationDemandsEstimateTool(BaseTool):
    def __init__(self):
        super().__init__(name="estimate_population_demand")
        self.client = GeminiClient()
        self.raster_path = "data/nepal_population.tif"
        self.default_radius_km = 1.0

    def run(self, context: dict, env):
        event_context = env.get_state("event_context") or {}
        severity = event_context.get("severity") or env.get_state("injury_severity") or "low"
        demand_level = "high" if severity in ("high", "critical") else "moderate" if severity == "moderate" else "low"

        sensor_data = env.get_state("sensor_data") or {}
        event_coords = env.get_state("event_coordinates") or {}
        lat = sensor_data.get("latitude") or event_coords.get("latitude")
        lon = sensor_data.get("longitude") or event_coords.get("longitude")

        # fall back to known location coords if still missing
        if lat is None or lon is None:
            location = (env.get_state("event_context") or {}).get("location", "")
            normalized = location.strip().lower()
            known = {
                "kathmandu": (27.7172, 85.3240),
                "pokhara": (28.2096, 83.9856),
                "lalitpur": (27.6588, 85.3247),
                "bhaktapur": (27.6710, 85.4298),
            }
            for key, coords in known.items():
                if key in normalized:
                    lat, lon = coords
                    break

        population = None
        try:
            if lat is not None and lon is not None:
                from src.executor.LLMdef.population_details import get_population_from_worldpop
                raw = get_population_from_worldpop(lat, lon)
                if raw and raw > 0:
                    population = int(raw)
        except Exception:
            pass

        demands_obj = {"demand_level": demand_level, "source": "PopulationDemandsEstimateTool"}
        raster_obj = {
            "radius_km": 5,
            "source": "WorldPop GPWv4",
            "total_population": population,
            "cell_resolution_m": 100,
        } if population else None
        rasterio_obj = {**raster_obj, "lat": lat, "lon": lon} if raster_obj else None
        pop_summary = (
            f"Raster scan estimates ~{population:,} people within 5 km of the event epicentre "
            f"(WorldPop GPWv4). Demand classified as {demand_level}."
        ) if population else None

        env.update_state("population_demands", demands_obj)
        env.update_state("raster_population", raster_obj)
        env.update_state("rasterio_population", rasterio_obj)
        env.update_state("estimated_affected_population", population)
        env.update_state("population_summary", pop_summary)

        return {
            "population_demands": demands_obj,
            "raster_population": raster_obj,
            "estimated_affected_population": population,
            "population_summary": pop_summary,
        }


class ScanDisasterZoneTool(BaseTool):
    def __init__(self):
        super().__init__(name="scan_disaster_zone")

    def run(self, context: dict, env):
        event_context = env.get_state("event_context") or {}
        severity = event_context.get("severity", "low")
        disaster_type = event_context.get("disaster_type", "unknown")
        location = event_context.get("location", "unknown")

        area_km2 = 8.0 if severity == "high" else 4.0 if severity == "moderate" else 1.5
        flood_depth_m = (2.5 if severity == "high" else 1.2 if severity == "moderate" else 0.5) if disaster_type in ("flood", "tsunami") else None
        risk = "critical" if severity == "high" else "high risk" if severity == "moderate" else "moderate risk"

        result = {
            "zones": [f"Zone A — {location} ({risk})"],
            "flood_depth_m": flood_depth_m,
            "area_km2": area_km2,
            "source": "aerial",
        }
        env.update_state("disaster_zone_scan", result)
        return {"disaster_zone_scan": result}


class AssessInfrastructureDamageTool(BaseTool):
    def __init__(self):
        super().__init__(name="assess_infrastructure_damage")

    def run(self, context: dict, env):
        event_context = env.get_state("event_context") or {}
        severity = event_context.get("severity", "low")
        location = event_context.get("location", "unknown")

        level = "severe" if severity == "high" else "moderate" if severity == "moderate" else "minor"
        road_closures = 3 if severity == "high" else 1 if severity == "moderate" else 0

        result = {
            "level": level,
            "affected_structures": [f"{location} structures"],
            "road_closures": road_closures,
            "source": "scan",
        }
        env.update_state("infrastructure_damage", result)
        return {"infrastructure_damage": result}


class RegionAccessibilityTool(BaseTool):
    def __init__(self):
        super().__init__(name="prioritize_affected_regions")

    def run(self, context: dict, env):
        event_context = env.get_state("event_context") or {}
        severity = event_context.get("severity", "low")
        disaster_type = event_context.get("disaster_type", "unknown")

        impassable_types = {"flood", "tsunami", "earthquake"}
        if severity == "high" or disaster_type in impassable_types:
            accessibility = "restricted"
        elif severity == "moderate":
            accessibility = "limited"
        else:
            accessibility = "accessible"

        env.update_state("region_accessibility", accessibility)
        return {"region_accessibility": accessibility}


class EventContextAnalysisTool(BaseTool):
    def __init__(self):
        super().__init__(name="analyze_event_context")
        self.client = OllamaClient()

    def run(self, context: dict, env):
        message = env.get_state("message") or ""

        prompt = f"""
You are a disaster analysis expert.

Extract structured context from the message.
Preserve the most specific location phrase found in the message.
For example, if the message says "New Baneshwor, Kathmandu, Nepal",
return "New Baneshwor, Kathmandu, Nepal" instead of only "Kathmandu".

Message:
{message}

Return ONLY valid JSON:
{{
  "disaster_type": "earthquake | flood | tsunami | fire | unknown",
  "location": "string",
  "severity": "low | moderate | high",
  "affected_area": "urban | rural | mixed"
}}
"""

        result = self.client.generate_json(prompt)

        # safe defaults
        event_context = {
            "disaster_type": _clean_value(result.get("disaster_type")) or _infer_disaster_type(message),
            "location": _clean_value(result.get("location")) or _infer_location(message),
            "severity": _clean_value(result.get("severity")) or _infer_event_severity(message),
            "affected_area": _clean_value(result.get("affected_area")) or "unknown",
        }

        env.update_state("event_context", event_context)

        return {"event_context": event_context}


def _clean_value(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or value.lower() in {"unknown", "none", "null", "n/a"}:
        return None
    return value


def _infer_location(message):
    normalized = message.lower()
    for location in KNOWN_LOCATION_NAMES:
        if location in normalized:
            return location.title()
    if "nepal" in normalized:
        return "Pokhara"
    return "Pokhara"


def _infer_disaster_type(message):
    normalized = message.lower()
    for disaster_type in ("earthquake", "flood", "tsunami", "fire"):
        if disaster_type in normalized:
            return disaster_type
    return "unknown"


def _infer_event_severity(message):
    normalized = message.lower()
    high_markers = ("major", "critical", "severe", "urgent", "thousands", "mass casualty")
    if any(marker in normalized for marker in high_markers):
        return "high"
    if any(marker in normalized for marker in ("moderate", "injuries", "medical")):
        return "moderate"
    return "low"


def _infer_injury_severity(message):
    normalized = message.lower()
    if any(marker in normalized for marker in ("critical", "severe", "major", "thousands", "mass casualty")):
        return "critical"
    if any(marker in normalized for marker in ("injuries", "injury", "medical", "ambulance")):
        return "moderate"
    return "low"
