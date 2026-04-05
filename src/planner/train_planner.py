import os
import json
import pickle

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split
from transformers import DistilBertTokenizer
from sklearn.metrics import f1_score, precision_score, recall_score

from src.planner.transformer_planner import TransformerPlanner


MODEL_NAME = "distilbert-base-uncased"
DATA_PATH = "data/planner/processed/planner_multilabel_dataset.json"
SAVE_DIR = "planner_model"


class PlannerDataset(Dataset):
    def __init__(self, input_texts, labels, tokenizer, max_input_len):
        self.input_texts = input_texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_input_len = max_input_len

    def __len__(self):
        return len(self.input_texts)

    def __getitem__(self, idx):
        text = self.input_texts[idx]
        label = self.labels[idx]

        encoded = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_input_len,
            return_tensors="pt"
        )

        return {
            "input_ids": encoded["input_ids"].squeeze(0),
            "labels": torch.tensor(label, dtype=torch.float)
        }


def load_data(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)

    texts = [item["message"] for item in data]
    active_tasks = [item["active_tasks"] for item in data]
    required_nodes = [item["required_nodes"] for item in data]

    return texts, active_tasks, required_nodes


def build_node_vocab(required_nodes):
    unique_nodes = sorted(set(node for nodes in required_nodes for node in nodes))
    node_to_idx = {node: idx for idx, node in enumerate(unique_nodes)}
    idx_to_node = {idx: node for node, idx in node_to_idx.items()}
    return node_to_idx, idx_to_node, unique_nodes


def encode_nodes_multihot(required_nodes, node_to_idx):
    labels = []
    num_nodes = len(node_to_idx)

    for nodes in required_nodes:
        vec = [0] * num_nodes
        for node in nodes:
            vec[node_to_idx[node]] = 1
        labels.append(vec)

    return labels


def build_input_text(texts, active_tasks):
    combined = []
    for text, tasks in zip(texts, active_tasks):
        task_text = ", ".join(tasks)
        combined.append(f"Tasks: {task_text} | Message: {text}")
    return combined


@torch.no_grad()
def evaluate(model, dataloader, device, threshold=0.5):
    model.eval()

    all_labels = []
    all_preds = []
    total_loss = 0.0

    criterion = nn.BCEWithLogitsLoss()

    for batch in dataloader:
        input_ids = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)

        logits, _ = model(input_ids)
        loss = criterion(logits, labels)

        probs = torch.sigmoid(logits)
        preds = (probs >= threshold).int()

        total_loss += loss.item()
        all_labels.append(labels.cpu())
        all_preds.append(preds.cpu())

    all_labels = torch.cat(all_labels).numpy()
    all_preds = torch.cat(all_preds).numpy()

    metrics = {
        "loss": total_loss / len(dataloader),
        "micro_f1": f1_score(all_labels, all_preds, average="micro", zero_division=0),
        "macro_f1": f1_score(all_labels, all_preds, average="macro", zero_division=0),
        "micro_precision": precision_score(all_labels, all_preds, average="micro", zero_division=0),
        "micro_recall": recall_score(all_labels, all_preds, average="micro", zero_division=0),
    }

    return metrics


def train():
    os.makedirs(SAVE_DIR, exist_ok=True)

    if torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    texts, active_tasks, required_nodes = load_data(DATA_PATH)

    node_to_idx, idx_to_node, node_list = build_node_vocab(required_nodes)
    labels = encode_nodes_multihot(required_nodes, node_to_idx)
    input_texts = build_input_text(texts, active_tasks)

    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)

    max_input_len = 96
    batch_size = 8
    num_epochs = 8
    lr = 1e-4

    d_model = 128
    num_heads = 8
    d_ff = 512
    num_layers = 2

    dataset = PlannerDataset(
        input_texts=input_texts,
        labels=labels,
        tokenizer=tokenizer,
        max_input_len=max_input_len
    )

    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = random_split(
        dataset,
        [train_size, val_size],
        generator=torch.Generator().manual_seed(42)
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)

    model = TransformerPlanner(
        vocab_size=tokenizer.vocab_size,
        max_len=max_input_len,
        d_model=d_model,
        num_heads=num_heads,
        d_ff=d_ff,
        num_layers=num_layers,
        num_nodes=len(node_to_idx)
    ).to(device)

    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    best_micro_f1 = -1.0

    for epoch in range(num_epochs):
        model.train()
        total_loss = 0.0

        for batch in train_loader:
            input_ids = batch["input_ids"].to(device)
            labels = batch["labels"].to(device)

            optimizer.zero_grad()

            logits, _ = model(input_ids)
            loss = criterion(logits, labels)

            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_train_loss = total_loss / len(train_loader)
        val_metrics = evaluate(model, val_loader, device)

        print(
            f"Epoch {epoch+1}/{num_epochs} | "
            f"Train Loss: {avg_train_loss:.4f} | "
            f"Val Loss: {val_metrics['loss']:.4f} | "
            f"Micro F1: {val_metrics['micro_f1']:.4f} | "
            f"Macro F1: {val_metrics['macro_f1']:.4f} | "
            f"Precision: {val_metrics['micro_precision']:.4f} | "
            f"Recall: {val_metrics['micro_recall']:.4f}"
        )

        if val_metrics["micro_f1"] > best_micro_f1:
            best_micro_f1 = val_metrics["micro_f1"]
            torch.save(model.state_dict(), os.path.join(SAVE_DIR, "planner_model.pt"))

    tokenizer.save_pretrained(SAVE_DIR)

    with open(os.path.join(SAVE_DIR, "node_to_idx.pkl"), "wb") as f:
        pickle.dump(node_to_idx, f)

    with open(os.path.join(SAVE_DIR, "idx_to_node.pkl"), "wb") as f:
        pickle.dump(idx_to_node, f)

    with open(os.path.join(SAVE_DIR, "planner_meta.pkl"), "wb") as f:
        pickle.dump(
            {
                "max_input_len": max_input_len,
                "d_model": d_model,
                "num_heads": num_heads,
                "d_ff": d_ff,
                "num_layers": num_layers,
                "num_nodes": len(node_to_idx),
                "node_list": node_list,
            },
            f
        )

    print(f"Planner model saved to {SAVE_DIR}")


if __name__ == "__main__":
    train()