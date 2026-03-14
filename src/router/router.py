from task_classifier import predict_task
from router_utils import load_router_components, get_recommended_tools, build_router_response


def route_query(text, model, tokenizer, le):
    task, confidence = predict_task(text, model, tokenizer, le)
    tools = get_recommended_tools(task)
    return build_router_response(task, confidence, tools)


if __name__ == "__main__":
    model, tokenizer, le = load_router_components()
    text = input("Enter the query: ")
    result = route_query(text, model, tokenizer, le)
    print(result)