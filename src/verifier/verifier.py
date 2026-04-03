from src.verifier.rule_checker import RuleChecker
from src.verifier.gemini_verifier import GeminiVerifier
from src.executor.simulation_env import SimulationEnv

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

    from src.slr.node_representation import ReasoningNode
    from src.slr.reasoning_graph import ReasoningGraph
    from src.executor.executor import Executor
    from src.executor.simulation_env import SimulationEnv
    from src.executor.resource_allocator import ResourceAllocator

    print("\n--- FULL PIPELINE TEST ---\n")

    # 1. Create nodes
    node1 = ReasoningNode(name="estimate_number_of_casualties")
    node2 = ReasoningNode(name="dispatch_ambulances")
    node3 = ReasoningNode(name="allocate_temporary_shelters")

    # 2. Build graph
    graph = ReasoningGraph()
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(node3)

    graph.add_edge("estimate_number_of_casualties", "dispatch_ambulances")
    graph.add_edge("dispatch_ambulances", "allocate_temporary_shelters")

    graph.validate_graph()

    # 3. Environment
    env = SimulationEnv("Tsunami in India with heavy casualties")
    env.update_state("injury_severity", "critical")

    # 4. Allocator
    allocator = ResourceAllocator(env)

    # 5. Executor
    executor = Executor(graph, env, allocator)

    result = executor.execute()

    # 6. Verifier
    verifier = Verifier()

    verification = verifier.verify(
        env.get_state("message"),
        result,
        env
    )

    print("\n--- VERIFICATION ---")
    print(verification)