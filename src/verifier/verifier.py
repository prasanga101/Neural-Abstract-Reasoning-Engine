from src.verifier.rule_checker import RuleChecker
from src.verifier.gemini_verifier import GeminiVerifier
from src.executor.simulation_env import SimulationEnv
import json
from src.slr.node_representation import ReasoningNode
from src.slr.reasoning_graph import ReasoningGraph
from src.executor.executor import Executor
from src.executor.resource_allocator import ResourceAllocator

class Verifier:
    def __init__(self, api_key=None):
        self.rule_checker = RuleChecker()
        self.gemini_verifier = GeminiVerifier(api_key=api_key)

    def verify(self, message, execution_result, env):
        rule_result = self.rule_checker.validate_execution(
            env,
            execution_result["execution_trace"]
        )

        gemini_result = self.gemini_verifier.validate(
            message,
            execution_result["execution_trace"],
            env.get_full_state()
        )

        overall_valid = rule_result["valid"] and gemini_result.get("valid", False)

        return {
            "overall_valid": overall_valid,
            "rule_validation": rule_result,
            "gemini_validation": gemini_result
        }

if __name__ == "__main__":



    print("\n--- FULL PIPELINE TEST ---\n")

    node1 = ReasoningNode(name="analyze_event_context")
    node2 = ReasoningNode(name="retrieve_disaster_information")
    node3 = ReasoningNode(name="assess_injury_severity")
    node4 = ReasoningNode(name="collect_sensor_data")
    node5 = ReasoningNode(name="estimate_number_of_casualties")
    node6 = ReasoningNode(name="identify_nearest_hospitals")
    node7 = ReasoningNode(name="identify_alternative_routes")
    node8 = ReasoningNode(name="optimize_transport_paths")

    graph = ReasoningGraph()
    for node in [node1, node2, node3, node4, node5, node6, node7, node8]:
        graph.add_node(node)

    graph.add_edge("analyze_event_context", "retrieve_disaster_information")
    graph.add_edge("analyze_event_context", "assess_injury_severity")
    graph.add_edge("analyze_event_context", "collect_sensor_data")
    graph.add_edge("retrieve_disaster_information", "estimate_number_of_casualties")
    graph.add_edge("assess_injury_severity", "estimate_number_of_casualties")
    graph.add_edge("analyze_event_context", "identify_nearest_hospitals")
    graph.add_edge("identify_nearest_hospitals", "identify_alternative_routes")
    graph.add_edge("collect_sensor_data", "identify_alternative_routes")
    graph.add_edge("identify_alternative_routes", "optimize_transport_paths")

    graph.validate_graph()

    env = SimulationEnv("There is a major earthquake in Mumbai, India with critical injuries and many wounded people")
    allocator = ResourceAllocator(env)

    executor = Executor(graph, env, allocator)
    result = executor.execute()

    verifier = Verifier()
    verification = verifier.verify(
        env.get_state("message"),
        result,
        env
    )
    print("\n--- EXECUTION RESULT BEFORE VERIFIER ---")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    print("\n--- ENV STATE BEFORE VERIFIER ---")
    print(json.dumps(env.get_full_state(), indent=2, ensure_ascii=False, default=str))

    print("\n--- VERIFICATION ---")
    print(json.dumps(verification, indent=2, ensure_ascii=False, default=str))