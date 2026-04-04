import pickle
import torch
from transformers import DistilBertTokenizer

from src.planner.transformer_planner import TransformerPlanner
from src.planner.planner_utils import decode_node_sequence
from src.router.router_utils import load_router_components
from src.router.router import route_query
from src.planner.embeddings import Embeddings
from src.planner.transformer_block import TransformerBlock

SAVE_DIR = "planner_model"


def load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def load_planner():
    task_to_idx = load_pickle(f"{SAVE_DIR}/task_to_idx.pkl")
    idx_to_task = load_pickle(f"{SAVE_DIR}/idx_to_task.pkl")
    node_to_idx = load_pickle(f"{SAVE_DIR}/node_to_idx.pkl")
    idx_to_node = load_pickle(f"{SAVE_DIR}/idx_to_node.pkl")
    meta = load_pickle(f"{SAVE_DIR}/planner_meta.pkl")

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
        num_tasks=meta["num_tasks"],
        num_heads=meta["num_heads"],
        d_ff=meta["d_ff"],
        num_layers=meta["num_layers"],
        num_nodes=meta["num_nodes"],
        max_steps=meta["max_steps"],
    ).to(device)

    model.load_state_dict(torch.load(f"{SAVE_DIR}/planner_model.pt", map_location=device))
    model.eval()

    return model, tokenizer, task_to_idx, idx_to_task, node_to_idx, idx_to_node, meta, device


def predict_plan(message, task_type):
    model, tokenizer, task_to_idx, idx_to_task, node_to_idx, idx_to_node, meta, device = load_planner()

    if task_type not in task_to_idx:
        raise ValueError(f"Unknown task_type: {task_type}")

    input_text = f"task_type: {task_type} | query: {message}"

    encoded = tokenizer(
        input_text,
        truncation=True,
        padding="max_length",
        max_length=meta["max_input_len"],
        return_tensors="pt"
    )

    input_ids = encoded["input_ids"].to(device)
    task_ids = torch.tensor([task_to_idx[task_type]], dtype=torch.long).to(device)

    with torch.no_grad():
        step_logits, attention_maps = model(input_ids, task_ids)

    predicted_ids = torch.argmax(step_logits, dim=-1).squeeze(0).tolist()
    predicted_nodes = decode_node_sequence(predicted_ids, idx_to_node)

    return {
        "message": message,
        "task_type": task_type,
        "predicted_ids": predicted_ids,
        "predicted_nodes": predicted_nodes
    }


if __name__ == "__main__":
    message = input("Enter the Emergency: ")

    # Load router
    router_model, router_tokenizer, le = load_router_components()

    # Router predicts task type
    router_result = route_query(message, router_model, router_tokenizer, le)
    task_type = router_result["task_type"]

    # Planner predicts steps
    result_steps = predict_plan(message, task_type)

    print("Message:", result_steps["message"])
    print("Predicted Task Type:", task_type)
    print("Router Confidence:", router_result["confidence"])
    print("Predicted Step IDs:", result_steps["predicted_ids"])
    print("Predicted Nodes:")
    for i, node in enumerate(result_steps["predicted_nodes"], start=1):
        print(f"  Step {i}: {node}")