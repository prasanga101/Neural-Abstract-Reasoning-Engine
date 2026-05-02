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
        self.client = GeminiClient()
        self.raster_path = "data/nepal_population.tif"
        self.default_radius_km = 1.0

    def run(self, context: dict, env):
        message       = env.get_state("message") or ""
        event_context = env.get_state("event_context") or {}
        casualties    = env.get_state("estimated_casualties") or 0

        population_result = self._estimate_from_raster(env)

        if population_result is None:
            population_result = {
                "estimated_affected_population": self._estimate_from_llm(
                    message, event_context, casualties
                ),
                "source": "llm",
                "method": "context_fallback"
            }

        estimated_population = population_result["estimated_affected_population"]

        if estimated_population > 100000:
            demand_level = "critical"
        elif estimated_population > 50000:
            demand_level = "high"
        elif estimated_population > 10000:
            demand_level = "moderate"
        else:
            demand_level = "low"

        population_data = {
            "estimated_affected_population": estimated_population,
            "demand_level": demand_level,
            "source": population_result.get("source", "unknown"),
            "method": population_result.get("method"),
            "radius_km": population_result.get("radius_km"),
            "coordinates": population_result.get("coordinates"),
            "exposed_population": population_result.get("exposed_population"),
            "affected_fraction": population_result.get("affected_fraction"),
        }

        env.update_state("population_demands", population_data)
        env.update_state("estimated_affected_population", estimated_population)

        return population_data

    def _raster_available(self):
        import os
        return os.path.exists(self.raster_path)

    def _estimate_from_raster(self, env):
        if not self._raster_available():
            print("[PopulationTool] Raster not found, falling back to LLM.")
            return None

        try:
            import rasterio
            from rasterio.windows import from_bounds
            import numpy as np
            import math

            event_coordinates = env.get_state("event_coordinates") or {}
            sensor_data = env.get_state("sensor_data") or {}
            hospitals = env.get_state("nearby_hospitals") or []

            lat = event_coordinates.get("latitude") or sensor_data.get("latitude")
            lon = event_coordinates.get("longitude") or sensor_data.get("longitude")

            if (lat is None or lon is None) and hospitals:
                lat = hospitals[0].get("lat")
                lon = hospitals[0].get("lon")

            if lat is None or lon is None:
                return None

            radius_km = self._impact_radius_km(env)
            lat_radius = radius_km / 111.32
            lon_radius = radius_km / (111.32 * max(math.cos(math.radians(lat)), 0.01))

            bounds = (
                lon - lon_radius,
                lat - lat_radius,
                lon + lon_radius,
                lat + lat_radius,
            )

            with rasterio.open(self.raster_path) as src:
                window = from_bounds(*bounds, transform=src.transform)
                data   = src.read(1, window=window)
                data   = np.where(data < 0, 0, data)

                rows, cols = np.indices(data.shape)
                transform = src.window_transform(window)
                xs = (
                    transform.c
                    + (cols + 0.5) * transform.a
                    + (rows + 0.5) * transform.b
                )
                ys = (
                    transform.f
                    + (cols + 0.5) * transform.d
                    + (rows + 0.5) * transform.e
                )
                dx_km = (xs - lon) * 111.32 * math.cos(math.radians(lat))
                dy_km = (ys - lat) * 111.32
                circular_mask = (dx_km ** 2 + dy_km ** 2) <= radius_km ** 2
                exposed_population = int(data[circular_mask].sum())
                affected_fraction = self._affected_fraction(env)
                estimated_affected = self._scale_exposed_to_affected(
                    exposed_population,
                    affected_fraction,
                    env,
                )

            print(
                f"[PopulationTool] Raster exposed population: {exposed_population}; "
                f"affected estimate: {estimated_affected} within {radius_km}km"
            )
            return {
                "estimated_affected_population": estimated_affected,
                "exposed_population": exposed_population,
                "affected_fraction": affected_fraction,
                "source": "raster",
                "method": "worldpop_circular_window_scaled",
                "radius_km": radius_km,
                "coordinates": {
                    "latitude": lat,
                    "longitude": lon
                }
            }

        except Exception as e:
            print(f"[PopulationTool] Raster error: {e}")
            return None

    def _impact_radius_km(self, env):
        event_context = env.get_state("event_context") or {}
        severity = str(event_context.get("severity", "")).lower()
        location = str(event_context.get("location", "")).lower()
        message = str(env.get_state("message") or "").lower()
        normalized_location = location.replace(" ", "").replace(",", "")
        is_specific_place = location.count(",") >= 2 or any(
            place in location
            for place in ["baneshwor", "koteshwor", "baluwatar", "pulchowk", "thamel"]
        )
        is_kathmandu_neighborhood = (
            "kathmandu" in location
            and normalized_location not in {"kathmandu", "kathmandunepal"}
        )

        if "citywide" in message or "across kathmandu" in message:
            return 3.0
        if is_specific_place or is_kathmandu_neighborhood:
            return 0.5
        if severity == "high":
            return 1.0
        if severity == "moderate":
            return 0.75
        return self.default_radius_km

    def _affected_fraction(self, env):
        event_context = env.get_state("event_context") or {}
        severity = str(event_context.get("severity", "")).lower()
        message = str(env.get_state("message") or "").lower()

        if "citywide" in message or "across kathmandu" in message:
            return 0.35
        if any(term in message for term in ["thousands", "mass displacement", "collapsed"]):
            return 0.28
        if severity == "high":
            return 0.22
        if severity == "moderate":
            return 0.12
        return 0.05

    def _scale_exposed_to_affected(self, exposed_population, affected_fraction, env):
        message = str(env.get_state("message") or "").lower()
        estimated_casualties = env.get_state("estimated_casualties") or 0

        affected = int(exposed_population * affected_fraction)

        if "thousands" in message:
            affected = max(affected, 5000)

        if "critical injuries" in message or "critically injured" in message:
            affected = max(affected, estimated_casualties * 5)

        return min(affected, exposed_population)

    def _estimate_from_llm(self, message, event_context, casualties):
        prompt = f"""
You are a disaster response expert.
Estimate affected population based on context.

Message: {message}
Event context: {event_context}
Estimated casualties: {casualties}

Return ONLY valid JSON:
{{
  "estimated_affected_population": <integer>
}}
"""
        result = self.client.generate_json(prompt)
        return result.get("estimated_affected_population", 10000)


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
            "disaster_type": result.get("disaster_type", "unknown"),
            "location": result.get("location", "unknown"),
            "severity": result.get("severity", "moderate"),
            "affected_area": result.get("affected_area", "unknown")
        }

        env.update_state("event_context", event_context)

        return {"event_context": event_context}
