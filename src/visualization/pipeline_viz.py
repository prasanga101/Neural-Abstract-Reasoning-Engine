from src.pipeline.reasoning_pipeline import ReasoningPipeline
from src.visualization.router_viz import build_router_viz

from src.visualization.planner_viz import build_planner_viz
from src.visualization.slr_graph_viz import build_slr_viz
from src.visualization.executor_viz import build_executor_viz
from src.visualization.verifier_viz import build_verifier_viz
from src.visualization.state_viz import build_state_viz
from pprint import pprint
def build_pipeline_viz(message):
    pipeline = ReasoningPipeline()
    result = pipeline.run(message)

    return {
        "message": message,
        "router": build_router_viz(result["router_result"]),
        "planner": build_planner_viz(result["planner_result"]),
        "slr": build_slr_viz(result["slr_result"]),
        "executor": build_executor_viz(result["execution_result"]),
        "verifier": build_verifier_viz(result["verification_result"]),
        "state": build_state_viz(result["final_environment_state"])
    }

if __name__ == "__main__":
    message = input("Enter the Emergency: ")
    viz_data = build_pipeline_viz(message)
    pprint(viz_data)