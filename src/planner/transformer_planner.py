import torch
import torch.nn as nn
from src.planner.embeddings import Embeddings
from src.planner.transformer_block import TransformerBlock


class TransformerPlanner(nn.Module):
    def __init__(
        self,
        vocab_size,
        max_len,
        d_model,
        num_heads,
        d_ff,
        num_layers,
        num_nodes
    ):
        super().__init__()

        self.embeddings = Embeddings(vocab_size, max_len, d_model)

        self.blocks = nn.ModuleList([
            TransformerBlock(d_model, num_heads, d_ff)
            for _ in range(num_layers)
        ])

        self.dropout = nn.Dropout(0.1)
        self.classifier = nn.Linear(d_model, num_nodes)

    def forward(self, input_ids, mask=None):
        x = self.embeddings(input_ids)

        attention_maps = []
        for block in self.blocks:
            x, weights = block(x, mask)
            attention_maps.append(weights)

        pooled = x.mean(dim=1)
        pooled = self.dropout(pooled)

        logits = self.classifier(pooled)

        return logits, attention_maps