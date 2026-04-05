import torch
import torch.nn as nn

#vocab_size = num of  unique tokens
#d_model = embedding size
#(vocab_size , d_model) = (1000,120) => 1000 rows , 128 cols each token ids point to one row

#this gives the set of vectors generally 512 sized for understanding of the word eg {send , some , ambulance} 
#each will have set of vectors assigned to it
class TokenEmbeddings(nn.Module):
    def __init__(self , vocab_size , d_model):
        super().__init__()
        self.embeddings = nn.Embedding(vocab_size , d_model)
    def forward(self , x):
        #output becomes [batch_size , seq_len , d_model]
        return self.embeddings(x)

#"dog bites man" and "man bites dog" same word different order positional embedding changes that
#max_len = length of maximum sentense
#each position has a vectore of size d_model. pos0 -> 1st d_model , pos2 -> 2nd d_model
class PositionalEmbeddings(nn.Module):
    def __init__(self , max_len , d_model):
        super().__init__()
        self.pos_embedding = nn.Embedding(max_len , d_model)
    def forward(self,x):
        #extracts batch_size , seq_len of input [2,5] => 2 sentences in 1 batch and 5 token each
        batch_size , seq_len = x.shape
        #gives us the token tositions , unsqueeze(0) chenges shape from eg [5] to [1,5] , expand is done incase to facilitate more than 1 sentense per batch
        positions = torch.arange(0 , seq_len).unsqueeze(0).expand(batch_size , seq_len).to(x.device)
        #converts pos_id into vectors
        #[batch_size , seq_len , d_model]
        return self.pos_embedding(positions)

#what is the type of task the whole sentence is about disaster monitoring , medical help , legal reasoning , coding?
#tell me what job is the model currently doing? Core Concept for NARE
#creates lookup table for class
'''
0 = disaster_event_monitoring
1 = legal_reasoning
2 = coding_help
3 = medical_emergency
...
our labels are 7 so we have 7 learnable task vectors ie 7 num_tasks
'''
#each task has size d_model
class TaskEmbeddings(nn.Module):
    def __init__(self , num_tasks , d_model):
        super().__init__()
        self.task_embedding = nn.Embedding(num_tasks , d_model)
    def forward(self , task_ids):
        #[batch_size , d_model]
        return self.task_embedding(task_ids)
    
#final embedding = token_embedding + position_embedding + task_embedding
#input_ids [batch_size , seq_len]
#task_ids [batch_size]
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
        #before unsqueeze [batch_size , d_model]
        #after unsqueeze(1) [batch_size , 1 , d_model]
        #after .expand() [batch_size , seq_len , d_model]
        #because every token in the sentense should know the task type
        task_embeds = task_embeds.unsqueeze(1).expand(batch_size , seq_len , -1)

        embeddings = token_embeds + pos_embeds + task_embeds

        return embeddings