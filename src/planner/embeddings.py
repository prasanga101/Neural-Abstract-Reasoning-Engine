import torch
import torch.nn as nn

class TokenEmbeddings(nn.Module):
    def __init__(self , vocab_size , d_model):
        super().__init__()
        self.embeddings = nn.Embedding(vocab_size , d_model)
    def forward(self , x):
        return self.embeddings(x)
    
class PositionalEmbeddings(nn.Module):
    def __init__(self , max_len , d_model):
        super().__init__()
        self.pos_embedding = nn.Embedding(max_len , d_model)
    def forward(self,x):
        batch_size , seq_len = x.shape
        positions = torch.arange(0 , seq_len).unsqueeze(0).expand(batch_size , seq_len).to(x.device)
        return self.pos_embedding(positions)
    
class TaskEmbeddings(nn.Module):
    def __init__(self , num_tasks , d_model):
        super().__init__()
        self.task_embedding = nn.Embedding(num_tasks , d_model)
    def forward(self , task_ids):
        return self.task_embedding(task_ids)
    
class Embeddings(nn.Module):

    def __init__(self , vocab_size , max_len , d_model , num_tasks):
        super().__init__()

        self.token_embeddings = TokenEmbeddings(vocab_size , d_model)
        self.positional_embeddings = PositionalEmbeddings(max_len , d_model)
        self.task_embeddings = TaskEmbeddings(num_tasks , d_model)

    def forward(self , input_ids , task_ids):

        token_embeds = self.token_embeddings(input_ids)
        pos_embeds = self.positional_embeddings(input_ids)

        task_embeds = self.task_embeddings(task_ids)

        batch_size , seq_len = input_ids.shape

        task_embeds = task_embeds.unsqueeze(1).expand(batch_size , seq_len , -1)

        embeddings = token_embeds + pos_embeds + task_embeds

        return embeddings