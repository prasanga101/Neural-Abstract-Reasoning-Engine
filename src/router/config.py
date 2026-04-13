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

    "infrastructure_and_route_planning": [
        "analyze_event_context",
        "assess_infrastructure_damage",
        "detect_blocked_routes",
        "identify_alternative_routes",
        "optimize_transport_paths"
    ],

    "general_disaster_information": [
        "analyze_event_context",
        "retrieve_disaster_information",
        "collect_sensor_data"
    ]
}

MIN_ROUTER_CONFIDENCE = 0.5
DEFAULT_FALLBACK_TASK = "general_disaster_information"


def map_tasks_to_nodes(predicted_tasks, confidence_scores=None):
    """
    Merge nodes from all predicted tasks.
    Optionally filter tasks using confidence scores.
    """
    selected_tasks = []

    for task in predicted_tasks:
        if confidence_scores is None:
            selected_tasks.append(task)
        else:
            score = confidence_scores.get(task, 0.0)
            if score >= MIN_ROUTER_CONFIDENCE:
                selected_tasks.append(task)

    if not selected_tasks:
        selected_tasks = [DEFAULT_FALLBACK_TASK]

    nodes = []
    for task in selected_tasks:
        nodes.extend(TASK_NODE_MAP.get(task, []))

    # remove duplicates while preserving order
    return list(dict.fromkeys(nodes))