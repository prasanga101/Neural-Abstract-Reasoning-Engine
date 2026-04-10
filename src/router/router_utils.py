import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

MODEL_PATH = "./router_model"


def load_router_components():
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_PATH)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    return model, tokenizer


def build_router_response(input_text, predicted_tasks, confidence_scores, nodes):
    return {
        "query": input_text,
        "predicted_tasks": predicted_tasks,
        "confidence_scores": {
            k: round(v, 4) for k, v in confidence_scores.items()
        },
        "required_nodes": nodes
    }