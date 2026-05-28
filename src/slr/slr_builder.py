from src.slr.node_representation import ReasoningNode
from src.slr.reasoning_graph import ReasoningGraph


class SLRBuilder:
    def __init__(self):
        self.dependency_map = {
            "retrieve_disaster_information": ["analyze_event_context"],
            "assess_injury_severity": ["analyze_event_context"],
            "collect_sensor_data": ["analyze_event_context"],
            "estimate_number_of_casualties": [
                "retrieve_disaster_information",
                "assess_injury_severity"
            ],
            "identify_nearest_hospitals": ["analyze_event_context"],
            "identify_alternative_routes": [
                "collect_sensor_data",
                "identify_nearest_hospitals",
                "detect_blocked_routes"
            ],
            "optimize_transport_paths": ["identify_alternative_routes"],
            "allocate_medical_supplies": ["analyze_resource_availability"],
            "allocate_food_resources": ["analyze_resource_availability"],
            "allocate_water_resources": ["analyze_resource_availability"],
            "allocate_relief_resources": [
                "estimate_population_demand",
                "analyze_resource_availability",
                "assess_injury_severity",
                "estimate_number_of_casualties",
            ],
            "allocate_resources": [
                "estimate_population_demand",
                "analyze_resource_availability",
                "assess_injury_severity",
                "estimate_number_of_casualties",
            ],
            "allocate_temporary_shelters": [
                "estimate_number_of_casualties"
            ],
            "dispatch_ambulances": [
                "assess_injury_severity",
                "estimate_number_of_casualties",
                "identify_nearest_hospitals"
            ],
            "allocate_temporary_shelters": [
                "estimate_number_of_casualties",
                "assess_population_needs"
            ],
            "deploy_rescue_teams": [
                "assess_infrastructure_damage",
                "locate_trapped_victims"
            ],
            "detect_blocked_routes": ["collect_sensor_data"],
            "assess_structural_damage": ["analyze_event_context"],
            "scan_disaster_zone": [
                "analyze_event_context",
                "assess_infrastructure_damage"
            ],
            "locate_trapped_victims": [
                "scan_disaster_zone",
                "estimate_number_of_casualties"
            ],
            "assess_infrastructure_damage": [
                "analyze_event_context",
                "detect_blocked_routes"
            ],
            "monitor_disaster_activity": ["analyze_event_context"],
            "analyze_disaster_data": ["collect_sensor_data"],
            "generate_situation_reports": ["analyze_disaster_data"],
            "generate_information_summary": ["retrieve_disaster_information"],
            "update_public_reports": ["generate_information_summary"],
            "dispatch_relief_teams": [
                "allocate_relief_resources",
                "prioritize_affected_regions"
            ],
            "coordinate_hospital_capacity": [
                "identify_nearest_hospitals",
                "assess_injury_severity",
                "estimate_number_of_casualties"
            ],
            "prioritize_affected_regions": ["analyze_event_context"],
            "estimate_population_demand": ["analyze_event_context", "identify_nearest_hospitals"],
            "analyze_resource_availability": ["analyze_event_context"],
            "identify_supply_sources": ["analyze_event_context"],
            "assess_population_needs": ["analyze_event_context"],
        }

    def _collect_with_dependencies(self, predicted_nodes):
        final_nodes = set(predicted_nodes)
        changed = True

        while changed:
            changed = False
            current_nodes = list(final_nodes)

            for node in current_nodes:
                for dep in self.dependency_map.get(node, []):
                    if dep not in final_nodes:
                        final_nodes.add(dep)
                        changed = True

        return list(final_nodes)

    def _augment_operational_nodes(self, message, predicted_tasks, predicted_nodes):
        text = " ".join(
            str(part or "")
            for part in [message, *(predicted_tasks or []), *(predicted_nodes or [])]
        ).lower()

        augmented = set(predicted_nodes)

        # Always include core situational awareness nodes for any disaster
        augmented.update({
            "scan_disaster_zone",
            "assess_infrastructure_damage",
            "generate_information_summary",
            "update_public_reports",
            "coordinate_hospital_capacity",
        })

        if any(keyword in text for keyword in ("medical", "hospital", "injury", "casualt", "ambulance")):
            augmented.update({
                "identify_nearest_hospitals",
                "dispatch_ambulances",
                "locate_trapped_victims",
                "deploy_rescue_teams",
            })

        if any(keyword in text for keyword in ("route", "routing", "transport", "corridor", "blocked", "access")):
            augmented.update({
                "collect_sensor_data",
                "identify_alternative_routes",
                "optimize_transport_paths",
            })

        if any(keyword in text for keyword in ("shelter", "evac", "displace", "temporary shelter")):
            augmented.add("allocate_temporary_shelters")

        if any(keyword in text for keyword in ("earthquake", "flood", "tsunami", "fire", "disaster", "emergency", "rescue", "trapped", "victim")):
            augmented.update({
                "locate_trapped_victims",
                "deploy_rescue_teams",
            })

        return list(augmented)

    def build(self, message, predicted_tasks, confidence_scores, predicted_nodes):
        if not predicted_nodes:
            raise ValueError("No predicted nodes provided")

        predicted_nodes = self._augment_operational_nodes(message, predicted_tasks, predicted_nodes)
        all_nodes = self._collect_with_dependencies(predicted_nodes)

        graph = ReasoningGraph()
        graph.message = message
        graph.predicted_tasks = predicted_tasks
        graph.confidence_scores = confidence_scores

        for node_name in all_nodes:
            dependencies = [
                dep for dep in self.dependency_map.get(node_name, [])
                if dep in all_nodes
            ]

            node = ReasoningNode(
                name=node_name,
                node_type="action",
                description="",
                inputs=[],
                outputs=[],
                dependencies=dependencies,
                priority=0,
                status="pending"
            )
            graph.add_node(node)

        graph.build_from_dependencies()
        graph.validate_graph()

        return graph
