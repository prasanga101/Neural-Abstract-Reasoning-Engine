import torch
import torch.nn as nn


class TokenEmbeddings(nn.Module):
    def __init__(self, vocab_size, d_model):
        super().__init__()
        self.embeddings = nn.Embedding(vocab_size, d_model)

    def forward(self, x):
        return self.embeddings(x)   # [batch_size, seq_len, d_model]


class PositionalEmbeddings(nn.Module):
    def __init__(self, max_len, d_model):
        super().__init__()
        self.pos_embedding = nn.Embedding(max_len, d_model)

    def forward(self, x):
        batch_size, seq_len = x.shape
        positions = torch.arange(0, seq_len, device=x.device).unsqueeze(0).expand(batch_size, seq_len)
        return self.pos_embedding(positions)   # [batch_size, seq_len, d_model]


class Embeddings(nn.Module):
    def __init__(self, vocab_size, max_len, d_model):
        super().__init__()

        self.token_embeddings = TokenEmbeddings(vocab_size, d_model)
        self.positional_embeddings = PositionalEmbeddings(max_len, d_model)
        self.layer_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(0.1)

    def forward(self, input_ids):
        token_embeds = self.token_embeddings(input_ids)
        pos_embeds = self.positional_embeddings(input_ids)

        embeddings = token_embeds + pos_embeds
        embeddings = self.layer_norm(embeddings)
        embeddings = self.dropout(embeddings)

        return embeddings