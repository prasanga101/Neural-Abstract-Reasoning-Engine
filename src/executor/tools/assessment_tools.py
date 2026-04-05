from src.executor.base_tools import BaseTool
from src.executor.LLMdef.model import GeminiClient

class InjuryAssessmentTool(BaseTool):
    def __init__(self):
        super().__init__(name="assess_injury_severity")
        self.client = GeminiClient()

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

        severity = result.get("injury_severity", "low")

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
        population_density = env.get_state("population_density") or 0
        needs = "high" if population_density > 1000 else "low"
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
        population_density = env.get_state("population_density") or 0
        demands = "high" if population_density > 1000 else "low"
        env.update_state("population_demands", demands)
        return {"population_demands": demands}


class RegionAccessibilityTool(BaseTool):
    def __init__(self):
        super().__init__(name="prioritize_affected_regions")

    def run(self, context: dict, env):
        accessibility = env.get_state("region_accessibility") or "unknown"
        env.update_state("region_accessibility", accessibility)
        return {"region_accessibility": accessibility}


class EventContextAnalysisTool(BaseTool):
    def __init__(self):
        super().__init__(name="analyze_event_context")
        self.client = GeminiClient()

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
            "disaster_type": result.get("disaster_type", "unknown"),
            "location": result.get("location", "unknown"),
            "severity": result.get("severity", "moderate"),
            "affected_area": result.get("affected_area", "unknown")
        }

        env.update_state("event_context", event_context)

        return {"event_context": event_context}