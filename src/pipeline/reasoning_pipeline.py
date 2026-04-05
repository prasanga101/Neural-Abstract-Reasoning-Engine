import json

from src.router.router_utils import load_router_components
from src.router.router import route_query

from src.planner.run_planner import predict_plan

from src.slr.slr_builder import SLRBuilder

from src.executor.executor import Executor
from src.executor.resource_allocator import ResourceAllocator
from src.executor.simulation_env import SimulationEnv

from src.verifier.verifier import Verifier


class ReasoningPipeline:
    def __init__(self, verifier_api_key=None):
        self.router_model, self.router_tokenizer = load_router_components()
        self.slr_builder = SLRBuilder()
        self.verifier = Verifier(api_key=verifier_api_key)

    def run(self, message: str):
        # 1. Router
        router_result = route_query(
            text=message,
            model=self.router_model,
            tokenizer=self.router_tokenizer
        )

        predicted_tasks = router_result["predicted_tasks"]
        confidence_scores = router_result["confidence_scores"]

        # 2. Planner
        planner_result = predict_plan(
            message=message,
            predicted_tasks=predicted_tasks
        )

        predicted_nodes = planner_result["predicted_nodes"]
        node_confidence_scores = planner_result["node_confidence_scores"]

        # 3. Build SLR reasoning graph
        reasoning_graph = self.slr_builder.build(
            message=message,
            predicted_tasks=predicted_tasks,
            confidence_scores=confidence_scores,
            predicted_nodes=predicted_nodes
        )

        # 4. Executor
        env = SimulationEnv(message)
        allocator = ResourceAllocator(env)
        executor = Executor(reasoning_graph, env, allocator)

        execution_result = executor.execute()

        # 5. Verifier
        verification_result = self.verifier.verify(
            message=message,
            execution_result=execution_result,
            env=env
        )

        return {
            "message": message,
            "router_result": router_result,
            "planner_result": {
                "predicted_tasks": predicted_tasks,
                "predicted_nodes": predicted_nodes,
                "node_confidence_scores": node_confidence_scores,
            },
            "slr_result": {
                "graph_nodes": list(reasoning_graph.nodes.keys()),
                "graph_edges": reasoning_graph.edges,
                "execution_order": reasoning_graph.get_execution_order(),
            },
            "execution_result": execution_result,
            "verification_result": verification_result,
            "final_environment_state": env.get_full_state()
        }


if __name__ == "__main__":
    pipeline = ReasoningPipeline()

    message = input("Enter the Emergency: ")
    result = pipeline.run(message)

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))