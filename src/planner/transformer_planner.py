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
        num_tasks,
        num_heads,
        d_ff,
        num_layers,
        num_nodes,
        max_steps
    ):
        super().__init__()

        self.d_model = d_model
        self.max_steps = max_steps

        self.embeddings = Embeddings(vocab_size, max_len, d_model, num_tasks)

        self.blocks = nn.ModuleList([
            TransformerBlock(d_model, num_heads, d_ff)
            for _ in range(num_layers)
        ])

        self.step_embeddings = nn.Embedding(max_steps, d_model)
        self.step_classifier = nn.Linear(d_model, num_nodes)

    def forward(self, input_ids, task_ids, mask=None):
        x = self.embeddings(input_ids, task_ids)

        attention_maps = []
        for block in self.blocks:
            x, weights = block(x, mask)
            attention_maps.append(weights)

        # context summary of input
        context = x.mean(dim=1)                      # [B, d_model]

        # repeat context for each planning step
        step_context = context.unsqueeze(1).expand(-1, self.max_steps, -1)   # [B, max_steps, d_model]

        # add learned step position embeddings
        batch_size = input_ids.size(0)
        step_positions = torch.arange(self.max_steps, device=input_ids.device)
        step_positions = step_positions.unsqueeze(0).expand(batch_size, self.max_steps)
        step_pos_embeds = self.step_embeddings(step_positions)                # [B, max_steps, d_model]

        planner_states = step_context + step_pos_embeds

        # predict node for each step slot
        step_logits = self.step_classifier(planner_states)                   # [B, max_steps, num_nodes]

        return step_logits, attention_maps