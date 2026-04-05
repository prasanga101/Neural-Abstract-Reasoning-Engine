import pandas as pd
import json
import os

medical_response_required_nodes = [
    "assess_injury_severity",
    "estimate_number_of_casualties",
    "identify_nearest_hospitals",
    "dispatch_ambulances"
]

search_and_rescue_required_nodes = [
    "assess_structural_damage",
    "scan_disaster_zone",
    "locate_trapped_victims",
    "deploy_rescue_teams"
]

relief_distribution_required_nodes = [
    "assess_population_needs",
    "identify_supply_sources",
    "allocate_relief_resources",
    "dispatch_relief_teams"
]

resource_allocation_required_nodes = [
    "analyze_resource_availability",
    "estimate_population_demand",
    "prioritize_affected_regions",
    "allocate_resources"
]

disaster_monitoring_required_nodes = [
    "monitor_disaster_activity",
    "collect_sensor_data",
    "analyze_disaster_data",
    "generate_situation_reports"
]

infrastructure_route_required_nodes = [
    "assess_infrastructure_damage",
    "detect_blocked_routes",
    "identify_alternative_routes",
    "optimize_transport_paths"
]

general_information_nodes = [
    "retrieve_disaster_information",
    "analyze_event_context",
    "generate_information_summary",
    "update_public_reports"
]

TASK_NODE_MAP = {
    "medical_response": medical_response_required_nodes,
    "search_and_rescue_operation": search_and_rescue_required_nodes,
    "relief_distribution": relief_distribution_required_nodes,
    "resource_allocation": resource_allocation_required_nodes,
    "disaster_event_monitoring": disaster_monitoring_required_nodes,
    "infrastructure_and_route_planning": infrastructure_route_required_nodes,
    "general_disaster_information": general_information_nodes
}

ROUTER_TASKS = list(TASK_NODE_MAP.keys())


def add_context_nodes(message, nodes):
    msg = message.lower()

    if any(word in msg for word in ["road blocked", "roads blocked", "bridge collapsed", "route blocked"]):
        nodes.extend([
            "detect_blocked_routes",
            "identify_alternative_routes"
        ])

    if any(word in msg for word in ["hospital overloaded", "hospital full", "hospitals are full", "no beds"]):
        nodes.append("coordinate_hospital_capacity")

    if any(word in msg for word in ["medical supplies", "medicine", "medicines", "supplies"]):
        nodes.append("allocate_medical_supplies")

    if any(word in msg for word in ["trapped", "collapsed building", "under debris", "under rubble"]):
        nodes.extend([
            "assess_structural_damage",
            "locate_trapped_victims",
            "deploy_rescue_teams"
        ])

    if any(word in msg for word in ["food", "hungry", "starving"]):
        nodes.append("allocate_food_resources")

    if any(word in msg for word in ["water", "drinking water", "clean water"]):
        nodes.append("allocate_water_resources")

    if any(word in msg for word in ["shelter", "homeless", "displaced", "tents"]):
        nodes.append("allocate_temporary_shelters")

    if any(word in msg for word in ["ambulance", "ambulances"]):
        nodes.append("dispatch_ambulances")

    if any(word in msg for word in ["injured", "wounded", "bleeding", "critical"]):
        nodes.append("assess_injury_severity")

    if any(word in msg for word in ["dead", "killed", "died", "fatalities"]):
        nodes.append("estimate_number_of_casualties")

    return list(dict.fromkeys(nodes))


def get_active_tasks(row):
    active_tasks = [task for task in ROUTER_TASKS if row[task] == 1]

    if not active_tasks:
        active_tasks = ["general_disaster_information"]

    return active_tasks


def get_required_nodes_from_tasks(active_tasks):
    nodes = []

    for task in active_tasks:
        nodes.extend(TASK_NODE_MAP.get(task, []))

    return list(dict.fromkeys(nodes))


def build_planner_dataset(input_file, output_file):
    df = pd.read_csv(input_file)
    planner_dataset = []

    for _, row in df.iterrows():
        message = row["message"]

        active_tasks = get_active_tasks(row)
        core_nodes = get_required_nodes_from_tasks(active_tasks)
        final_nodes = add_context_nodes(message, core_nodes)

        planner_dataset.append({
            "message": message,
            "active_tasks": active_tasks,
            "required_nodes": final_nodes
        })

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(planner_dataset, f, indent=4)

    print(f"Planner dataset created with {len(planner_dataset)} samples")
    print("Sample:")
    print(json.dumps(planner_dataset[:2], indent=4))


if __name__ == "__main__":
    build_planner_dataset(
        "data/processed/router_multilabel_dataset.csv",
        "data/planner/processed/planner_multilabel_dataset.json"
    )