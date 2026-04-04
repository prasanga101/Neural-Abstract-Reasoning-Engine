from src.executor.base_tools import BaseTool

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
    
class ReliefAllocationTool(BaseTool):
    def __init__(self):
        super().__init__(name="allocate_relief_resources")

    def run(self, context: dict, env):
        injury_severity = env.get_state("injury_severity") or "unknown"
        estimated_casualties = env.get_state("estimated_casualties") or 0

        if injury_severity == "critical":
            resources_allocated = min(estimated_casualties * 2, 1000)
        elif injury_severity == "moderate":
            resources_allocated = min(estimated_casualties, 500)
        else:
            resources_allocated = min(estimated_casualties // 2, 200)

        env.update_state("relief_resources_allocated", resources_allocated)
        return {"relief_resources_allocated": resources_allocated}
    
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