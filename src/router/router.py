from pprint import pprint
from src.router.task_classifier import predict_tasks
from src.router.router_utils import load_router_components, build_router_response
from src.router.node_mapper import map_tasks_to_nodes


def route_query(text, model, tokenizer):
    predicted_tasks, confidence_scores = predict_tasks(text, model, tokenizer)

    nodes = map_tasks_to_nodes(predicted_tasks, confidence_scores)

    return build_router_response(
        input_text=text,
        predicted_tasks=predicted_tasks,
        confidence_scores=confidence_scores,
        nodes=nodes
    )


if __name__ == "__main__":
    model, tokenizer = load_router_components()
    text = input("Enter the query: ")
    result = route_query(text, model, tokenizer)
    pprint(result)