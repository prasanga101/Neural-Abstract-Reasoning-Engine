def build_state_viz(state):
    return {
        "ambulances": state.get("available_ambulances"),
        "shelters": state.get("available_shelters"),
        "hospitals": state.get("nearby_hospitals", []),
        "blocked_routes": state.get("blocked_routes", []),
        "routes": state.get("alternative_routes", []),
        "best_route": state.get("optimized_route")
    }