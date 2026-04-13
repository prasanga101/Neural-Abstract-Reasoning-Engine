import torch
import torch.nn as nn
import math
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model , num_heads):
        super().__init__()
        self.d_model = d_model  
        self.num_heads = num_heads
        assert d_model % num_heads == 0 , "There is no divisiility issue"
        self.head_dim = d_model // num_heads
        self.W_q = nn.Linear(d_model , d_model)
        self.W_k = nn.Linear(d_model , d_model)
        self.W_v = nn.Linear(d_model , d_model)
        self.W_o = nn.Linear(d_model , d_model) #this is the output projection that concats the processings of other heads

    def forward(self , x , mask = None):
        batch_size , seq_len, _ = x.shape

        Q = self.W_q(x)
        K = self.W_k(x)
        V = self.W_v(x)
        Q = Q.view(batch_size , seq_len , self.num_heads , self.head_dim).transpose(1,2)
        K = K.view(batch_size , seq_len , self.num_heads , self.head_dim).transpose(1,2)
        V = V.view(batch_size , seq_len , self.num_heads , self.head_dim).transpose(1,2)

        scores = Q @ K.transpose(-2 , -1)
        scores = scores / math.sqrt(self.head_dim)

        if mask is not None:
            scores = scores.masked_fill(mask == 0 , -1.e9)
        
        weights = torch.softmax(scores , dim = -1)
        output = weights @ V
        output = output.transpose(1, 2).contiguous().view(batch_size, seq_len, self.d_model)
        output = self.W_o(output)


        return output , weights
        


