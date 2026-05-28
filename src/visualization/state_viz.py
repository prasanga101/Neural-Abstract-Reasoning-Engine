def build_state_viz(state):
    return {
        "ambulances": state.get("available_ambulances"),
        "ambulances_dispatched": state.get("ambulances_dispatched", 0),
        "shelters": state.get("available_shelters"),
        "shelters_allocated": state.get("shelters_allocated", 0),
        "hospitals": state.get("nearby_hospitals") or state.get("available_hospitals", []),
        "blocked_routes": state.get("blocked_routes", []),
        "blocked_route_details": state.get("blocked_route_details", []),
        "blocked_route_detection": state.get("blocked_route_detection"),
        "routes": state.get("alternative_routes", []),
        "best_route": state.get("optimized_route"),
        "routing_graph": state.get("routing_graph"),
        "resolved_location": state.get("resolved_location"),
        "event_coordinates": state.get("event_coordinates") or state.get("sensor_data"),
    }
