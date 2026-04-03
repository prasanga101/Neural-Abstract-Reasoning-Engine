from src.slr.reasoning_graph import ReasoningGraph
from src.executor.simulation_env import SimulationEnv
from src.executor.resource_allocator import ResourceAllocator

class Executor:
    def __init__(self, reasoning_graph: ReasoningGraph, env: SimulationEnv , allocator: ResourceAllocator):
        self.reasoning_graph = reasoning_graph
        self.env = env
        self.allocator = allocator
        self.context = {}
        self.execution_trace = []

    def _execute_node(self, node):

        if node.name == "estimate_number_of_casualties":
            severity = self.env.get_state("injury_severity")
            estimated = 350 if severity != "low" else 100
            self.env.update_state("estimated_casualties", estimated)
            return {"estimated_casualties": estimated}
        elif node.name == "dispatch_ambulances":
            return self.allocator.allocate_ambulances()
        elif node.name == "allocate_temporary_shelters":
            return self.allocator.allocate_shelters()
        return {"result": f"Executed {node.name}"}

    def execute(self):
        order = self.reasoning_graph.get_execution_order()

        for step_num, node_name in enumerate(order, start=1):
            node = self.reasoning_graph.nodes[node_name]

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

            except Exception as e:
                node.status = "failed"

                self.execution_trace.append({
                    "step": step_num,
                    "node": node.name,
                    "status": node.status,
                    "error": str(e)
                })

                return {
                    "status": "failed",
                    "execution_trace": self.execution_trace,
                    "final_outputs": self.context
                }

        return {
            "status": "completed",
            "execution_trace": self.execution_trace,
            "final_outputs": self.context
        }


if __name__ == "__main__":

    from src.slr.node_representation import ReasoningNode
    from src.slr.reasoning_graph import ReasoningGraph

    print("\n--- EXECUTOR TEST ---\n")

    # Step 1: Create nodes
    node1 = ReasoningNode(name="estimate_number_of_casualties")
    node2 = ReasoningNode(name="dispatch_ambulances")
    node3 = ReasoningNode(name="allocate_temporary_shelters")

    # Step 2: Build graph
    graph = ReasoningGraph()
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(node3)

    graph.add_edge("estimate_number_of_casualties", "dispatch_ambulances")
    graph.add_edge("dispatch_ambulances", "allocate_temporary_shelters")

    graph.validate_graph()

    # Step 3: Create environment
    env = SimulationEnv("Tsunami in India with heavy casualties")
    env.update_state("injury_severity", "critical")

    # Step 4: Create allocator
    allocator = ResourceAllocator(env)

    # Step 5: Create executor
    executor = Executor(graph, env, allocator)

    # Step 6: Execute
    result = executor.execute()

    # Step 7: Print results
    print("Final Status:", result["status"])
    print("\nExecution Trace:")
    for step in result["execution_trace"]:
        print(step)

    print("\nFinal Outputs:")
    print(result["final_outputs"])

    print("\nFinal Environment State:")
    print(env.get_full_state())