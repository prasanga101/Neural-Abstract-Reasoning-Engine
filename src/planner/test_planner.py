import torch

from transformer_planner import TransformerPlanner

# dummy parameters
vocab_size = 1000
max_len = 50
d_model = 128
num_tasks = 5
num_heads = 8
d_ff = 512
num_layers = 2
num_classes = 4

# create model
model = TransformerPlanner(
    vocab_size,
    max_len,
    d_model,
    num_tasks,
    num_heads,
    d_ff,
    num_layers,
    num_classes
)

# dummy input
batch_size = 2
seq_len = 10

input_ids = torch.randint(0, vocab_size, (batch_size, seq_len))
task_ids = torch.randint(0, num_tasks, (batch_size,))

# run forward pass
logits, attention_maps = model(input_ids, task_ids)

print("Logits shape:", logits.shape)
print("Attention layers:", len(attention_maps))