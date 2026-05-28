def build_state_viz(state):
    ambulances_dispatched = state.get("ambulances_dispatched", 0)
    shelters_allocated = state.get("shelters_allocated", 0)
    food_supplies = state.get("food_supplies_allocated", 0)
    water_supplies = state.get("water_supplies_allocated", 0)
    medical_supplies = state.get("medical_supplies_allocated", 0)
    relief_resources = state.get("relief_resources_allocated", 0)

    resource_allocation_plan = None
    if any([ambulances_dispatched, shelters_allocated, food_supplies, water_supplies, medical_supplies, relief_resources]):
        resource_allocation_plan = {
            "ambulances_dispatched": ambulances_dispatched,
            "shelters_allocated": shelters_allocated,
            "food_supplies": food_supplies,
            "water_supplies": water_supplies,
            "medical_supplies": medical_supplies,
            "relief_resources": relief_resources,
        }

    return {
        "ambulances": state.get("available_ambulances"),
        "shelters": state.get("available_shelters"),
        "hospitals": state.get("nearby_hospitals") or state.get("available_hospitals", []),
        "blocked_routes": state.get("blocked_routes", []),
        "blocked_route_details": state.get("blocked_route_details", []),
        "blocked_route_detection": state.get("blocked_route_detection"),
        "routes": state.get("alternative_routes", []),
        "best_route": state.get("optimized_route"),
        "routing_graph": state.get("routing_graph"),
        "resolved_location": state.get("resolved_location"),
        "event_coordinates": state.get("event_coordinates") or state.get("sensor_data"),
        "infrastructure_damage": state.get("infrastructure_damage"),
        "disaster_zone_scan": state.get("disaster_zone_scan"),
        "trapped_victims": state.get("trapped_victims"),
        "rescue_teams_allocated": state.get("rescue_teams_allocated"),
        "hospital_capacity_plan": state.get("hospital_capacity_plan"),
        "resource_allocation_plan": resource_allocation_plan,
        "information_summary": state.get("information_summary"),
        "public_report": state.get("public_report"),
        "population_demands": state.get("population_demands"),
        "estimated_affected_population": state.get("estimated_affected_population"),
        "raster_population": state.get("raster_population"),
        "rasterio_population": state.get("rasterio_population"),
        "population_summary": state.get("population_summary"),
    }
