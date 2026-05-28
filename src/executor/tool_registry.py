from src.executor.tools.assessment_tools import (
    InjuryAssessmentTool,
    CasualtyEstimationTool,
    StructuralDamageAssessmentTool,
    InfrastructureDamageAssessmentTool,
    PopulationNeedsAssessmentTool,
    ResourceAvailabilityAnalysisTool,
    PopulationDemandsEstimateTool,
    RegionAccessibilityTool,
    EventContextAnalysisTool,
    ScanDisasterZoneTool,
    AssessInfrastructureDamageTool,
)
from src.executor.tools.allocation_tools import (
    AmbulanceDispatchTool,
    ShelterAllocationTool,
    ReliefAllocationTool,
    FoodAllocationTool,
    WaterAllocationTool,
    MedicalSupplyAllocationTool,
    AggregateResourceAllocationTool,
)
from src.executor.tools.response_tools import (
    HospitalDispatchTool,
    DeployRescueTeamsTool,
    RescueTeamAllocationTool,
    SupplySourceIdentificationTool,
    InformationRetrievalTool,
    LocateTrappedVictimsTool,
    GenerateInformationSummaryTool,
    UpdatePublicReportsTool,
    CoordinateHospitalCapacityTool,
)
from src.executor.tools.monitoring_tools import (
    DisasterMonitoringTool,
    SensorCollectionTool,
    DisasterAnalysisTool,
    SituationReportTool,
)
from src.executor.tools.routing_tools import (
    BlockedRouteDetectionTool,
    AlternativeRouteTool,
    TransportOptimizationTool,
)


class DummyTool:
    def __init__(self, name):
        self.name = name

    def run(self, context, env):
        return {
            "status": "skipped",
            "node": self.name,
            "message": f"{self.name} not implemented yet"
        }


class ToolRegistry:
    def __init__(self):
        self.tools = {
            "assess_injury_severity": InjuryAssessmentTool(),
            "estimate_number_of_casualties": CasualtyEstimationTool(),
            "assess_structural_damage": StructuralDamageAssessmentTool(),
            "assess_infrastructure_damage": InfrastructureDamageAssessmentTool(),
            "assess_population_needs": PopulationNeedsAssessmentTool(),
            "analyze_resource_availability": ResourceAvailabilityAnalysisTool(),
            "estimate_population_demand": PopulationDemandsEstimateTool(),
            "prioritize_affected_regions": RegionAccessibilityTool(),
            "analyze_event_context": EventContextAnalysisTool(),
            "dispatch_ambulances": AmbulanceDispatchTool(),
            "allocate_temporary_shelters": ShelterAllocationTool(),
            "allocate_relief_resources": ReliefAllocationTool(),
            "allocate_food_resources": FoodAllocationTool(),
            "allocate_water_resources": WaterAllocationTool(),
            "allocate_medical_supplies": MedicalSupplyAllocationTool(),
            "allocate_resources": AggregateResourceAllocationTool(),
            "identify_nearest_hospitals": HospitalDispatchTool(),
            "deploy_rescue_teams": DeployRescueTeamsTool(),
            "identify_supply_sources": SupplySourceIdentificationTool(),
            "retrieve_disaster_information": InformationRetrievalTool(),
            "scan_disaster_zone": DisasterZoneScanTool(),
            "locate_trapped_victims": TrappedVictimLocationTool(),
            "generate_information_summary": InformationSummaryTool(),
            "update_public_reports": PublicReportUpdateTool(),
            "coordinate_hospital_capacity": HospitalCapacityCoordinationTool(),
            "monitor_disaster_activity": DisasterMonitoringTool(),
            "collect_sensor_data": SensorCollectionTool(),
            "analyze_disaster_data": DisasterAnalysisTool(),
            "generate_situation_reports": SituationReportTool(),
            "scan_disaster_zone": ScanDisasterZoneTool(),
            "assess_infrastructure_damage": AssessInfrastructureDamageTool(),
            "locate_trapped_victims": LocateTrappedVictimsTool(),
            "generate_information_summary": GenerateInformationSummaryTool(),
            "update_public_reports": UpdatePublicReportsTool(),
            "coordinate_hospital_capacity": CoordinateHospitalCapacityTool(),
            "detect_blocked_routes": BlockedRouteDetectionTool(),
            "identify_alternative_routes": AlternativeRouteTool(),
            "optimize_transport_paths": TransportOptimizationTool(),
            "dispatch_relief_teams": RescueTeamAllocationTool(),
            "allocate_resources": ReliefAllocationTool(),
        }

    def get_tool(self, tool_name: str):
        if tool_name not in self.tools:
            print(f"[Executor Warning] Tool {tool_name} not found. Using dummy tool.")
            return DummyTool(tool_name)
        return self.tools[tool_name]
