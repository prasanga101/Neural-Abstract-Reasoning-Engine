import pickle
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification


def load_router_components():
    model = DistilBertForSequenceClassification.from_pretrained("./router_model")
    tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

    with open("./router_model/label_encoder.pkl", "rb") as f:
        le = pickle.load(f)

    return model, tokenizer, le


def build_router_response(task_type, confidence, nodes):
    return {
        "task_type": task_type,
        "confidence": round(float(confidence), 4),
        "recommended_nodes": nodes
    }