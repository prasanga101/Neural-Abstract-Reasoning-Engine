from pprint import pprint
from pathlib import Path
from src.router.task_classifier import predict_tasks
from src.router.router_utils import load_router_components, build_router_response
from src.router.node_mapper import map_tasks_to_nodes
from src.rl.abstraction_learning import init_abstraction
import pickle

# =========================
# SAFE PATH LOADING
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BANDIT_PATH = BASE_DIR / "src" / "rl" / "bandit.pkl"

with open(BANDIT_PATH, "rb") as f:
    agent = pickle.load(f)

abstraction = init_abstraction()

# =========================
# ROUTE QUERY
# =========================
def route_query(text, model, tokenizer, threshold=0.5):

    # --- STATE EXTRACTION ---
    state = abstraction.extract(text)

    # --- CLASSIFIER ---
    predicted_tasks, confidence_scores = predict_tasks(
        text,
        model,
        tokenizer,
        threshold=threshold
    )

    # --- RL ACTION ---
    rl_action = agent.select_action(state)
    rl_injected = False

    # --- HYBRID BASE ---
    if len(predicted_tasks) > 0:
        base_tasks      = predicted_tasks.copy()
        base_confidence = confidence_scores.copy()
        source          = "classifier"
    else:
        base_tasks      = [rl_action]
        base_confidence = {rl_action: 1.0}
        source          = "rl"

    # --- RL INJECTION ---
    if rl_action not in base_tasks:
        base_tasks.append(rl_action)
        base_confidence[rl_action] = 0.6
        rl_injected = True

    # --- FILTERING — use passed threshold, not hardcoded ---
    TOP_K = 3

    filtered = [
        (task, score)
        for task, score in base_confidence.items()
        if score >= threshold  # ← uses frontend threshold now
    ]

    # Fallback safety
    if not filtered:
        filtered = [(rl_action, 1.0)]

    filtered         = sorted(filtered, key=lambda x: x[1], reverse=True)
    filtered         = filtered[:TOP_K]
    final_tasks      = [task for task, _ in filtered]
    final_confidence = {task: score for task, score in filtered}

    # --- NODE MAPPING ---
    nodes = map_tasks_to_nodes(final_tasks, final_confidence)

    # --- RL METADATA ---
    rl_metadata = {
        "rl_action"    : rl_action,
        "rl_injected"  : rl_injected,
        "rl_source"    : source,
        "classifier_tasks": predicted_tasks,
        "classifier_scores": confidence_scores,
    }

    return build_router_response(
        input_text=text,
        predicted_tasks=final_tasks,
        confidence_scores=final_confidence,
        nodes=nodes,
        rl_metadata=rl_metadata   # ← pass RL info through
    )

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    model, tokenizer = load_router_components()
    text   = input("Enter the query: ")
    result = route_query(text, model, tokenizer)
    pprint(result)