from src.router.task_classifier import predict_task
from src.router.router_utils import load_router_components, build_router_response
from src.router.node_mapper import map_task_to_nodes
from pprint import pprint
def route_query(text, model, tokenizer, le):
    task, confidence = predict_task(text, model, tokenizer, le)
    task = str(task)
    nodes = map_task_to_nodes(task, confidence)
    return build_router_response(task, confidence, nodes)


if __name__ == "__main__":
    model, tokenizer, le = load_router_components()
    text = input("Enter the query: ")
    result = route_query(text, model, tokenizer, le)
    pprint(result)