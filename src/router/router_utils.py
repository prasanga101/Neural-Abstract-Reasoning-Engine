from pathlib import Path

import torch
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = REPO_ROOT / "router_model"


def load_router_components():
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_PATH)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    return model, tokenizer


def build_router_response(input_text, predicted_tasks, confidence_scores, nodes, rl_metadata=None):
    scores = [
        {"task": task, "score": round(confidence_scores.get(task, 0.0), 4)}
        for task in predicted_tasks
    ]
    scores = sorted(scores, key=lambda x: x["score"], reverse=True)
    top = scores[0]["task"] if scores else None

    response = {
        "query": input_text,
        "predicted_tasks": predicted_tasks,
        "confidence_scores": confidence_scores,
        "required_nodes": nodes,
        "router": {
            "tasks": predicted_tasks,
            "scores": scores,
            "top": top,
        },
    }

    if rl_metadata:
        response["rl"] = {
            "action": rl_metadata["rl_action"],
            "injected": rl_metadata["rl_injected"],
            "source": rl_metadata["rl_source"],
            "classifier_tasks": rl_metadata["classifier_tasks"],
        }

    return response
