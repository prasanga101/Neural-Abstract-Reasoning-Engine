def build_state_viz(state):
    population_demands = state.get("population_demands")
    estimated_population = state.get("estimated_affected_population")

    raster_population = None
    population_summary = None

    if population_demands:
        raster_population = {
            "estimated_affected_population": population_demands.get(
                "estimated_affected_population",
                estimated_population,
            ),
            "demand_level": population_demands.get("demand_level"),
            "source": population_demands.get("source"),
            "method": population_demands.get("method"),
            "radius_km": population_demands.get("radius_km"),
            "coordinates": population_demands.get("coordinates"),
            "exposed_population": population_demands.get("exposed_population"),
            "affected_fraction": population_demands.get("affected_fraction"),
        }

        if raster_population["estimated_affected_population"] is not None:
            population_summary = (
                f"Population demand estimated as {raster_population['demand_level']} "
                f"with approximately {raster_population['estimated_affected_population']:,} "
                f"people affected (source: {raster_population['source']})."
            )

    return {
        "ambulances": state.get("available_ambulances"),
        "shelters": state.get("available_shelters"),
        "hospitals": state.get("nearby_hospitals", []),
        "blocked_routes": state.get("blocked_routes", []),
        "blocked_route_details": state.get("blocked_route_details", []),
        "blocked_route_detection": state.get("blocked_route_detection"),
        "routes": state.get("alternative_routes", []),
        "best_route": state.get("optimized_route"),
        "routing_graph": state.get("routing_graph"),
        "resolved_location": state.get("resolved_location"),
        "event_coordinates": state.get("event_coordinates"),
        "infrastructure_damage": state.get("infrastructure_damage"),
        "disaster_zone_scan": state.get("disaster_zone_scan"),
        "trapped_victims": state.get("trapped_victims"),
        "rescue_teams_allocated": state.get("rescue_teams_allocated"),
        "hospital_capacity_plan": state.get("hospital_capacity_plan"),
        "resource_allocation_plan": state.get("resource_allocation_plan"),
        "information_summary": state.get("information_summary"),
        "public_report": state.get("public_report"),
        "population_demands": population_demands,
        "estimated_affected_population": estimated_population,
        "raster_population": raster_population,
        "rasterio_population": raster_population,
        "population_summary": population_summary,
    }
