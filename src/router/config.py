TASK_NODE_MAP = {
    "medical_response": [
        "analyze_event_context",
        "retrieve_disaster_information",
        "assess_injury_severity",
        "collect_sensor_data",
        "estimate_number_of_casualties",
        "identify_nearest_hospitals",
        "identify_alternative_routes",
        "optimize_transport_paths"
    ],

    "search_and_rescue_operation": [
        "analyze_event_context",
        "collect_sensor_data",
        "detect_blocked_routes",
        "identify_alternative_routes",
        "deploy_rescue_teams"
    ],

    "resource_allocation": [
        "analyze_event_context",
        "estimate_population_demand",
        "analyze_resource_availability",
        "allocate_relief_resources",
        "allocate_food_resources",
        "allocate_water_resources",
        "allocate_medical_supplies"
    ],

    "relief_distribution": [
        "analyze_event_context",
        "identify_supply_sources",
        "prioritize_affected_regions",
        "optimize_transport_paths"
    ],

    "disaster_event_monitoring": [
        "monitor_disaster_activity",
        "collect_sensor_data",
        "analyze_disaster_data",
        "generate_situation_reports"
    ],

    "general_disaster_information": [
        "analyze_event_context",
        "retrieve_disaster_information",
        "collect_sensor_data"
    ]
}

MIN_ROUTER_CONFIDENCE = 0.7
DEFAULT_FALLBACK_TASK = "general_disaster_information"