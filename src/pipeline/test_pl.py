from src.slr.reasoning_graph import ReasoningGraph
from src.executor.simulation_env import SimulationEnv
from src.executor.resource_allocator import ResourceAllocator
from src.executor.tool_registry import ToolRegistry
import json


class Executor:
    def __init__(self, reasoning_graph: ReasoningGraph, env: SimulationEnv, allocator: ResourceAllocator):
        self.reasoning_graph = reasoning_graph
        self.env = env
        self.allocator = allocator
        self.context = {}
        self.execution_trace = []
        self.registry = ToolRegistry()

    def _execute_node(self, node):
        tool = self.registry.get_tool(node.name)
        return tool.run(self.context, self.env)

    def execute(self):
        order = self.reasoning_graph.get_execution_order()
        print(f"[Executor] Execution order: {order}", flush=True)

        for step_num, node_name in enumerate(order, start=1):
            node = self.reasoning_graph.nodes[node_name]
            print(f"[Executor] Starting step {step_num}: {node.name}", flush=True)

            try:
                output = self._execute_node(node)

                self.context[node.name] = output
                node.status = "completed"

                self.execution_trace.append({
                    "step": step_num,
                    "node": node.name,
                    "status": node.status,
                    "output": output
                })

                print(f"[Executor] Completed step {step_num}: {node.name}", flush=True)

            except Exception as e:
                node.status = "failed"

                self.execution_trace.append({
                    "step": step_num,
                    "node": node.name,
                    "status": node.status,
                    "error": str(e)
                })

                print(f"[Executor] Failed at step {step_num}: {node.name} -> {e}", flush=True)

                return {
                    "status": "failed",
                    "execution_trace": self.execution_trace,
                    "final_outputs": self.context
                }

        print("[Executor] Execution completed successfully.", flush=True)
        return {
            "status": "completed",
            "execution_trace": self.execution_trace,
            "final_outputs": self.context
        }


if __name__ == "__main__":
    from src.slr.node_representation import ReasoningNode

    print("\n--- EXECUTOR TEST ---\n")

    node1 = ReasoningNode(name="analyze_event_context")
    node2 = ReasoningNode(name="retrieve_disaster_information")
    node3 = ReasoningNode(name="assess_injury_severity")
    node4 = ReasoningNode(name="collect_sensor_data")
    node5 = ReasoningNode(name="estimate_number_of_casualties")
    node6 = ReasoningNode(name="identify_nearest_hospitals")
    node7 = ReasoningNode(name="identify_alternative_routes")
    node8 = ReasoningNode(name="optimize_transport_paths")

    graph = ReasoningGraph()
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(node3)
    graph.add_node(node4)
    graph.add_node(node5)
    graph.add_node(node6)
    graph.add_node(node7)
    graph.add_node(node8)

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

    env = SimulationEnv(
        "There has been a major earthquake in Kathmandu, Nepalwith many critically injured people and blocked roads. Emergency responders need to identify the nearest hospitals and the best routes for ambulances immediately."
    )
    allocator = ResourceAllocator(env)

    executor = Executor(graph, env, allocator)
    result = executor.execute()

    print("Final Status:", result["status"])

    print("\nExecution Trace:")
    print(json.dumps(result["execution_trace"], indent=2, ensure_ascii=False, default=str))

    print("\nFinal Outputs:")
    print(json.dumps(result["final_outputs"], indent=2, ensure_ascii=False, default=str))

    print("\nFinal Environment State:")
    print(json.dumps(env.get_full_state(), indent=2, ensure_ascii=False, default=str))