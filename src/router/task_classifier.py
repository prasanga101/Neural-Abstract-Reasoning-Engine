import pandas as pd
from sklearn.preprocessing import LabelEncoder
from datasets import Dataset
import torch
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments
)

MODEL_NAME = "distilbert-base-uncased"


def load_data(file):
    df = pd.read_csv(file)

    texts = df["message"].tolist()
    labels = df["task_type"].tolist()

    le = LabelEncoder()
    labels = le.fit_transform(labels)

    return texts, labels, le


def tokenize_data(texts, labels):
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)

    encodings = tokenizer(
        texts,
        truncation=True,
        padding=True,
        max_length=64
    )

    dataset = Dataset.from_dict({
        "input_ids": encodings["input_ids"],
        "attention_mask": encodings["attention_mask"],
        "labels": labels
    })

    return dataset, tokenizer


def train_model(dataset, num_labels):
    model = DistilBertForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=num_labels
    )

    training_args = TrainingArguments(
        output_dir="./router_model",
        num_train_epochs=2,
        per_device_train_batch_size=8,
        logging_dir="./logs",
        save_strategy="epoch",
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset
    )

    trainer.train()
    trainer.save_model("./router_model")


def predict_task(text, model, tokenizer, le):
    model.eval()

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=64
    )

    with torch.no_grad():
        output = model(**inputs)
    probs = torch.nn.functional.softmax(output.logits, dim=1)
    pred = torch.argmax(output.logits, dim=1).item()
    confidence = probs[0][pred].item()

    return le.inverse_transform([pred])[0] , confidence


import pickle

if __name__ == "__main__":
    texts, labels, le = load_data("data/processed/router_dataset.csv")

    # optional: smaller sample for fast testing
    # texts = texts[:3000]
    # labels = labels[:3000]

    dataset, tokenizer = tokenize_data(texts, labels)
    train_model(dataset, num_labels=len(le.classes_))

    # save label encoder
    with open("./router_model/label_encoder.pkl", "wb") as f:
        pickle.dump(le, f)

    model = DistilBertForSequenceClassification.from_pretrained("./router_model")

    test_text = "Please call an ambulance there is a medical emergency"
    predicted_task = predict_task(test_text, model, tokenizer, le)

    print(f"Predicted task type: {predicted_task}")