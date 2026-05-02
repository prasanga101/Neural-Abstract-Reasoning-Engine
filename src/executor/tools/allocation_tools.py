from src.executor.base_tools import BaseTool
import requests
class AmbulanceDispatchTool(BaseTool):
    def __init__(self):
        super().__init__(name="dispatch_ambulances")

    def run(self, context: dict, env):
        estimated_casualties = env.get_state("estimated_casualties") or 0
        available_ambulances = env.get_state("available_ambulances") or 0

        ambulances_to_dispatch = min(estimated_casualties // 10, available_ambulances)

        env.update_state("available_ambulances", available_ambulances - ambulances_to_dispatch)
        return {"ambulances_dispatched": ambulances_to_dispatch}

class ShelterAllocationTool(BaseTool):
    def __init__(self):
        super().__init__(name="allocate_temporary_shelters")

    def run(self, context: dict, env):
        estimated_casualties = env.get_state("estimated_casualties") or 0
        available_shelters = env.get_state("available_shelters") or 0

        shelters_needed = max(1, estimated_casualties // 50) if estimated_casualties > 0 else 0
        shelters_to_allocate = min(shelters_needed, available_shelters)

        env.update_state("available_shelters", available_shelters - shelters_to_allocate)
        return {"shelters_allocated": shelters_to_allocate}


class AggregateResourceAllocationTool(BaseTool):
    def __init__(self):
        super().__init__(name="allocate_resources")

    def run(self, context: dict, env):
        resource_availability = env.get_state("resource_availability") or {}
        population_demands = env.get_state("population_demands") or {}
        estimated_population = (
            population_demands.get("estimated_affected_population")
            or env.get_state("estimated_affected_population")
            or 0
        )
        estimated_casualties = env.get_state("estimated_casualties") or 0
        available_ambulances = resource_availability.get(
            "available_ambulances",
            env.get_state("available_ambulances") or 0,
        )
        available_shelters = resource_availability.get(
            "available_shelters",
            env.get_state("available_shelters") or 0,
        )

        shelter_need = max(0, int(estimated_population // 5000))
        ambulance_need = max(1, int(estimated_casualties // 10)) if estimated_casualties else 0
        medical_kit_need = max(0, int(estimated_casualties * 2))
        water_need_liters = max(0, int(estimated_population * 3))
        food_need_packs = max(0, int(estimated_population * 0.5))

        allocation = {
            "ambulances": min(available_ambulances, ambulance_need),
            "shelters": min(available_shelters, shelter_need),
            "medical_kits": min(medical_kit_need, 5000),
            "water_liters": min(water_need_liters, 30000),
            "food_packs": min(food_need_packs, 10000),
            "basis": {
                "estimated_population": estimated_population,
                "estimated_casualties": estimated_casualties,
                "demand_level": population_demands.get("demand_level", "unknown"),
            },
        }

        env.update_state("resource_allocation_plan", allocation)
        return {"resource_allocation_plan": allocation}


class ReliefAllocationTool(BaseTool):

    def __init__(self):

        super().__init__(name="allocate_relief_resources")

    def run(self, context: dict, env):

        estimated_casualties = env.get_state("estimated_casualties") or 0

        try:

            sensor = env.get_state("sensor_data") or {}

            lat = sensor.get("latitude")

            lon = sensor.get("longitude")

            if lat is None or lon is None:

                raise Exception("Missing lat/lon")

            from src.executor.LLMdef.population_details import get_population_from_worldpop

            population = get_population_from_worldpop(lat, lon)

            location = env.get_state("event_context")["location"]

            relief = requests.get(

                "https://api.reliefweb.int/v1/reports",

                params={"query[value]": location, "limit": 1},

                timeout=5

            ).json()

            available_resources = 5000 if relief else 2000

            demand = max(population * 0.1, estimated_casualties)

            allocated = int(min(demand, available_resources))

            env.update_state("relief_resources_allocated", allocated)

            return {

                "relief_resources_allocated": allocated,

                "population": population,

                "lat": lat,

                "lon": lon,

                "source": "api"

            }

        except Exception:

            injury_severity = env.get_state("injury_severity") or "unknown"

            if injury_severity == "critical":

                allocated = min(estimated_casualties * 2, 1000)

            elif injury_severity == "moderate":

                allocated = min(estimated_casualties, 500)

            else:

                allocated = min(estimated_casualties // 2, 200)

            env.update_state("relief_resources_allocated", allocated)

            return {

                "relief_resources_allocated": allocated,

                "source": "fallback"

            }
            
class FoodAllocationTool(BaseTool):
    def __init__(self):
        super().__init__(name="allocate_food_resources")

    def run(self, context: dict, env):
        population_needs = env.get_state("population_needs") or "low"
        estimated_casualties = env.get_state("estimated_casualties") or 0

        if population_needs == "high":
            food_allocated = min(estimated_casualties * 3, 2000)
        else:
            food_allocated = min(estimated_casualties, 500)

        env.update_state("food_supplies_allocated", food_allocated)
        return {"food_supplies_allocated": food_allocated}
    
class WaterAllocationTool(BaseTool):
    def __init__(self):
        super().__init__(name="allocate_water_resources")

    def run(self, context: dict, env):
        population_needs = env.get_state("population_needs") or "low"
        estimated_casualties = env.get_state("estimated_casualties") or 0

        if population_needs == "high":
            water_allocated = min(estimated_casualties * 4, 3000)
        else:
            water_allocated = min(estimated_casualties * 2, 1000)

        env.update_state("water_supplies_allocated", water_allocated)
        return {"water_supplies_allocated": water_allocated}

class MedicalSupplyAllocationTool(BaseTool):
    def __init__(self):
        super().__init__(name="allocate_medical_supplies")

    def run(self, context: dict, env):
        injury_severity = env.get_state("injury_severity") or "unknown"
        estimated_casualties = env.get_state("estimated_casualties") or 0

        if injury_severity == "critical":
            medical_supplies_allocated = min(estimated_casualties * 5, 5000)
        elif injury_severity == "moderate":
            medical_supplies_allocated = min(estimated_casualties * 2, 2000)
        else:
            medical_supplies_allocated = min(estimated_casualties, 1000)

        env.update_state("medical_supplies_allocated", medical_supplies_allocated)
        return {"medical_supplies_allocated": medical_supplies_allocated}
    
