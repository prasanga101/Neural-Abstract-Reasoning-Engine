import re
import pandas as pd
import numpy as np
import torch
from datetime import datetime
from pathlib import Path
from datasets import Dataset
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, precision_score, recall_score
import pickle

MODEL_NAME = "distilbert-base-uncased"
RESULTS_PATH = "TRAINING_RESULTS.md"


def _write_results_md(path, section, metrics: dict):
    existing = Path(path).read_text() if Path(path).exists() else "# Training Results\n"
    header = f"## {section}"
    block = (
        f"\n{header}\n"
        f"_Last trained: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n"
        + "\n".join(f"- **{k}**: {v}" for k, v in metrics.items())
        + "\n"
    )
    if header in existing:
        existing = re.sub(rf"{re.escape(header)}.*?(?=\n## |\Z)", block.lstrip("\n"), existing, flags=re.DOTALL)
    else:
        existing = existing.rstrip("\n") + "\n" + block
    Path(path).write_text(existing)

ROUTER_TASKS = [
    "medical_response",
    "search_and_rescue_operation",
    "relief_distribution",
    "infrastructure_and_route_planning",
    "disaster_event_monitoring",
    "resource_allocation",
    "general_disaster_information"
]


def load_data(file):
    df = pd.read_csv(file)

    texts = df["message"].tolist()
    labels = df[ROUTER_TASKS].values.astype(np.float32)

    return texts, labels


def tokenize_data(texts, labels, tokenizer):
    encodings = tokenizer(
        texts,
        truncation=True,
        padding=True,
        max_length=64
    )

    dataset = Dataset.from_dict({
        "input_ids": encodings["input_ids"],
        "attention_mask": encodings["attention_mask"],
        "labels": labels.tolist()
    })

    return dataset


def compute_metrics(eval_pred):
    logits, labels = eval_pred

    probs = 1 / (1 + np.exp(-logits))   # sigmoid
    preds = (probs >= 0.5).astype(int)

    return {
        "micro_f1": f1_score(labels, preds, average="micro", zero_division=0),
        "macro_f1": f1_score(labels, preds, average="macro", zero_division=0),
        "micro_precision": precision_score(labels, preds, average="micro", zero_division=0),
        "micro_recall": recall_score(labels, preds, average="micro", zero_division=0),
    }


def train_model(train_dataset, val_dataset, num_labels):
    model = DistilBertForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=num_labels,
        problem_type="multi_label_classification"
    )

    training_args = TrainingArguments(
        output_dir="./router_model",
        num_train_epochs=100,
        per_device_train_batch_size=64,
        per_device_eval_batch_size=64,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_dir="./logs",
        report_to="none",
        load_best_model_at_end=True,
        metric_for_best_model="micro_f1",
        greater_is_better=True,
        fp16=torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics
    )

    trainer.train()
    trainer.save_model("./router_model")

    return trainer


def predict_tasks(text, model, tokenizer, threshold=0.5):
    model.eval()

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=64
    )

    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        output = model(**inputs)

    probs = torch.sigmoid(output.logits).cpu().numpy()[0]
    preds = (probs >= threshold).astype(int)

    predicted_tasks = [
        ROUTER_TASKS[i]
        for i, pred in enumerate(preds)
        if pred == 1
    ]

    confidence_scores = {
        ROUTER_TASKS[i]: float(probs[i])
        for i in range(len(ROUTER_TASKS))
    }

    if not predicted_tasks:
        predicted_tasks = ["general_disaster_information"]

    return predicted_tasks, confidence_scores


if __name__ == "__main__":
    texts, labels = load_data("data/processed/router_multilabel_dataset.csv")

    X_train, X_val, y_train, y_val = train_test_split(
        texts,
        labels,
        test_size=0.2,
        random_state=42
    )

    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)

    train_dataset = tokenize_data(X_train, y_train, tokenizer)
    val_dataset = tokenize_data(X_val, y_val, tokenizer)

    trainer = train_model(
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        num_labels=len(ROUTER_TASKS)
    )

    tokenizer.save_pretrained("./router_model")

    with open("./router_model/router_tasks.pkl", "wb") as f:
        pickle.dump(ROUTER_TASKS, f)

    model = DistilBertForSequenceClassification.from_pretrained("./router_model")
    model.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))

    test_text = "Please send ambulances, food, and water urgently. Roads are blocked."
    predicted_tasks, confidence_scores = predict_tasks(test_text, model, tokenizer)

    print(f"Predicted tasks: {predicted_tasks}")
    print("Confidence scores:")
    for task, score in confidence_scores.items():
        print(f"{task}: {score:.4f}")

    best_metrics = trainer.state.best_metric or 0.0
    eval_results = trainer.evaluate()
    _write_results_md(RESULTS_PATH, "Router", {
        "Epochs": 100,
        "Micro F1": f"{eval_results.get('eval_micro_f1', best_metrics):.4f}",
        "Macro F1": f"{eval_results.get('eval_macro_f1', 0):.4f}",
        "Precision": f"{eval_results.get('eval_micro_precision', 0):.4f}",
        "Recall": f"{eval_results.get('eval_micro_recall', 0):.4f}",
    })