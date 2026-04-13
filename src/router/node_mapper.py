from src.router.config import TASK_NODE_MAP, MIN_ROUTER_CONFIDENCE, DEFAULT_FALLBACK_TASK

SUPPORTED_TASKS = list(TASK_NODE_MAP.keys())


def map_tasks_to_nodes(predicted_tasks, confidence_scores):
    """
    Multi-label node mapping:
    - keeps only tasks above confidence threshold
    - falls back to default task if nothing is strong enough
    - merges nodes from all selected tasks
    """

    selected_tasks = []

    for task in predicted_tasks:
        if task not in SUPPORTED_TASKS:
            print(f"[Router Warning] Unsupported task: {task}, skipping")
            continue

        score = confidence_scores.get(task, 0.0)
        if score >= MIN_ROUTER_CONFIDENCE:
            selected_tasks.append(task)

    if not selected_tasks:
        selected_tasks = [DEFAULT_FALLBACK_TASK]

    nodes = []
    for task in selected_tasks:
        nodes.extend(TASK_NODE_MAP.get(task, []))

    # remove duplicates while preserving order
    return list(dict.fromkeys(nodes))