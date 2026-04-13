from src.planner.multi_head_attention import MultiHeadAttention
from src.planner.feed_forward import FeedForwardNetwork

import torch
import torch.nn as nn

class TransformerBlock(nn.Module):
    def __init__(self, d_model , num_heads , d_ff):
        super().__init__()
        self.d_model = d_model
        self.num_heads = num_heads
        self.dim_heads = d_model // num_heads
        self.d_ff = d_ff
        self.mha = MultiHeadAttention(d_model , num_heads)
        self.ffn = FeedForwardNetwork(d_model , d_ff)

        self.n1 = nn.LayerNorm(d_model)
        self.n2 = nn.LayerNorm(d_model)

    def forward(self , x , mask = None):
        attn_output, weights = self.mha(x , mask)
        x = self.n1(x + attn_output)
        ffn_output = self.ffn(x)
        x = self.n2(x + ffn_output)

        return x, weights