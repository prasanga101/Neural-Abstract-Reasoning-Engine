from src.router.config import TASK_NODE_MAP, MIN_ROUTER_CONFIDENCE, DEFAULT_FALLBACK_TASK
SUPPORTED_TASKS = list(TASK_NODE_MAP.keys())

def map_task_to_nodes(task: str, confidence: float):
    # low confidence → fallback
    if confidence < MIN_ROUTER_CONFIDENCE:
        return TASK_NODE_MAP.get(DEFAULT_FALLBACK_TASK, []).copy()

    # unknown task → fallback
    if task not in SUPPORTED_TASKS:
        print(f"[Router Warning] Unsupported task: {task}, using fallback")
        return TASK_NODE_MAP.get(DEFAULT_FALLBACK_TASK, []).copy()

    return TASK_NODE_MAP[task].copy()


