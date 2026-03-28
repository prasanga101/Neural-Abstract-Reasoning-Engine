import os
import pickle

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertTokenizer

from transformer_planner import TransformerPlanner
from planner_utils import (
    load_data,
    build_task_vocab,
    build_nodes_vocab,
    get_max_steps,
    encode_task_ids,
    encode_all_node_sequences,
    build_input_text,
)


MODEL_NAME = "distilbert-base-uncased"
DATA_PATH = r"data/planner/processed/planner_dataset.json"
SAVE_DIR = "planner_model"


class PlannerDataset(Dataset):
    def __init__(self, input_texts, task_ids, labels, tokenizer, max_input_len):
        self.input_texts = input_texts
        self.task_ids = task_ids
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_input_len = max_input_len

    def __len__(self):
        return len(self.input_texts)

    def __getitem__(self, idx):
        text = self.input_texts[idx]
        task_id = self.task_ids[idx]
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
            "task_ids": torch.tensor(task_id, dtype=torch.long),
            "labels": torch.tensor(label, dtype=torch.long)
        }


def train():
    os.makedirs(SAVE_DIR, exist_ok=True)

    if torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    texts, task_types, required_nodes = load_data(DATA_PATH)

    task_to_idx, idx_to_task = build_task_vocab(task_types)
    node_to_idx, idx_to_node, node_list = build_nodes_vocab(required_nodes)

    max_steps = get_max_steps(required_nodes)

    task_ids = encode_task_ids(task_types, task_to_idx)
    labels = encode_all_node_sequences(required_nodes, node_to_idx, max_steps)
    input_texts = build_input_text(texts, task_types)

    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)

    max_input_len = 64
    batch_size = 8
    num_epochs = 10
    lr = 1e-4

    d_model = 128
    num_heads = 8
    d_ff = 512
    num_layers = 2

    dataset = PlannerDataset(
        input_texts=input_texts,
        task_ids=task_ids,
        labels=labels,
        tokenizer=tokenizer,
        max_input_len=max_input_len
    )

    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = TransformerPlanner(
        vocab_size=tokenizer.vocab_size,
        max_len=max_input_len,
        d_model=d_model,
        num_tasks=len(task_to_idx),
        num_heads=num_heads,
        d_ff=d_ff,
        num_layers=num_layers,
        num_nodes=len(node_to_idx),
        max_steps=max_steps
    ).to(device)

    criterion = nn.CrossEntropyLoss(ignore_index=node_to_idx["<PAD>"])
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    for epoch in range(num_epochs):
        model.train()
        total_loss = 0.0

        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            task_ids = batch["task_ids"].to(device)
            labels = batch["labels"].to(device)  # [B, max_steps]

            optimizer.zero_grad()

            step_logits, _ = model(input_ids, task_ids)  # [B, max_steps, num_nodes]

            loss = criterion(
                step_logits.view(-1, step_logits.size(-1)),
                labels.view(-1)
            )

            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}")

    torch.save(model.state_dict(), os.path.join(SAVE_DIR, "planner_model.pt"))

    tokenizer.save_pretrained(SAVE_DIR)

    with open(os.path.join(SAVE_DIR, "task_to_idx.pkl"), "wb") as f:
        pickle.dump(task_to_idx, f)

    with open(os.path.join(SAVE_DIR, "idx_to_task.pkl"), "wb") as f:
        pickle.dump(idx_to_task, f)

    with open(os.path.join(SAVE_DIR, "node_to_idx.pkl"), "wb") as f:
        pickle.dump(node_to_idx, f)

    with open(os.path.join(SAVE_DIR, "idx_to_node.pkl"), "wb") as f:
        pickle.dump(idx_to_node, f)

    with open(os.path.join(SAVE_DIR, "planner_meta.pkl"), "wb") as f:
        pickle.dump(
            {
                "max_input_len": max_input_len,
                "max_steps": max_steps,
                "d_model": d_model,
                "num_heads": num_heads,
                "d_ff": d_ff,
                "num_layers": num_layers,
                "num_tasks": len(task_to_idx),
                "num_nodes": len(node_to_idx),
            },
            f
        )

    print(f"Planner model saved to {SAVE_DIR}")


if __name__ == "__main__":
    train()