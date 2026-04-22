import pickle
from pathlib import Path

import torch
from transformers import DistilBertTokenizer

from src.planner.transformer_planner import TransformerPlanner
from src.router.router_utils import load_router_components
from src.router.router import route_query

REPO_ROOT = Path(__file__).resolve().parents[2]
SAVE_DIR = REPO_ROOT / "planner_model"


def load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def load_planner():
    node_to_idx = load_pickle(SAVE_DIR / "node_to_idx.pkl")
    idx_to_node = load_pickle(SAVE_DIR / "idx_to_node.pkl")
    meta = load_pickle(SAVE_DIR / "planner_meta.pkl")

    tokenizer = DistilBertTokenizer.from_pretrained(SAVE_DIR)

    if torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    model = TransformerPlanner(
        vocab_size=tokenizer.vocab_size,
        max_len=meta["max_input_len"],
        d_model=meta["d_model"],
        num_heads=meta["num_heads"],
        d_ff=meta["d_ff"],
        num_layers=meta["num_layers"],
        num_nodes=meta["num_nodes"],
    ).to(device)

    model.load_state_dict(torch.load(SAVE_DIR / "planner_model.pt", map_location=device))
    model.eval()

    return model, tokenizer, node_to_idx, idx_to_node, meta, device


def predict_plan(message, predicted_tasks, threshold=0.5):
    model, tokenizer, node_to_idx, idx_to_node, meta, device = load_planner()

    task_text = ", ".join(predicted_tasks)
    input_text = f"Tasks: {task_text} | Message: {message}"

    encoded = tokenizer(
        input_text,
        truncation=True,
        padding="max_length",
        max_length=meta["max_input_len"],
        return_tensors="pt"
    )

    input_ids = encoded["input_ids"].to(device)

    with torch.no_grad():
        logits, attention_maps = model(input_ids)

    probs = torch.sigmoid(logits).squeeze(0).cpu().numpy()
    preds = (probs >= threshold).astype(int)

    predicted_nodes = [
        idx_to_node[i]
        for i, pred in enumerate(preds)
        if pred == 1
    ]

    node_confidence_scores = {
        idx_to_node[i]: float(probs[i])
        for i in range(len(probs))
    }

    return {
        "message": message,
        "predicted_tasks": predicted_tasks,
        "predicted_nodes": predicted_nodes,
        "node_confidence_scores": node_confidence_scores,
        "attention_maps": attention_maps
    }


if __name__ == "__main__":
    message = input("Enter the Emergency: ")

    # Load router
    router_model, router_tokenizer = load_router_components()

    # Router predicts tasks
    router_result = route_query(message, router_model, router_tokenizer)
    predicted_tasks = router_result["predicted_tasks"]

    # Planner predicts nodes
    planner_result = predict_plan(message, predicted_tasks)

    print("\nMessage:", planner_result["message"])
    print("Predicted Tasks:", planner_result["predicted_tasks"])

    print("\nRouter Confidence Scores:")
    for task, score in router_result["confidence_scores"].items():
        print(f"  {task}: {score:.4f}")

    print("\nPredicted Nodes:")
    for node in planner_result["predicted_nodes"]:
        print(f"  - {node}")

    print("\nPlanner Node Confidence Scores:")
    for node, score in planner_result["node_confidence_scores"].items():
        if score >= 0.5:
            print(f"  {node}: {score:.4f}")
