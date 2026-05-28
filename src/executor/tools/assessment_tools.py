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

    def run(self, context: dict, env):
        event_context = env.get_state("event_context") or {}
        severity = event_context.get("severity") or env.get_state("injury_severity") or "low"
        demands = "high" if severity in ("high", "critical") else "moderate" if severity == "moderate" else "low"
        env.update_state("population_demands", demands)
        return {"population_demands": demands}


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
