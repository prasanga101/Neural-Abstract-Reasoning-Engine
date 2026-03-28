import torch
import torch.nn as nn
import math
#d_ff is he fidden expansion dimension inside the ffn
#expand->non-linearity->compress
#d_ff expands the hidden space for learning
class FeedForwardNetwork(nn.Module):
    def __init__(self,d_model , d_ff):
        super().__init__()
        self.d_model = d_model
        self.d_ff = d_ff
        self.l1 = nn.Linear(d_model, d_ff)
        self.relu = nn.ReLU()
        self.l2 = nn.Linear(d_ff , d_model)
        self.relu = nn.ReLU()

    def forward(self ,x):
        x = self.l1(x)
        x = self.relu(x)
        x = self.l2(x)
        return x



        
