# Planner Module

This folder contains the planning model and its training/inference pipeline. The planner receives the original emergency message plus router-selected tasks, and predicts the set of reasoning nodes that should be activated for downstream execution.

## Files

- [run_planner.py](run_planner.py): loads the saved planner model and runs inference.
- [train_planner.py](train_planner.py): trains the planner on the processed multi-label dataset.
- [transformer_planner.py](transformer_planner.py): top-level planner model.
- [transformer_block.py](transformer_block.py): Transformer block implementation.
- [multi_head_attention.py](multi_head_attention.py): multi-head attention implementation.
- [attention.py](attention.py): attention helper implementation.
- [embeddings.py](embeddings.py): input embeddings.
- [feed_forward.py](feed_forward.py): feed-forward network block.
- [planner_utils.py](planner_utils.py): planner utilities.
- [test_planner.py](test_planner.py): planner test or experiment script.

## Planner input format

The planner builds a single text string in this form:

```text
Tasks: <comma-separated task labels> | Message: <original emergency text>
```

This combines coarse router intent with the original message so the model can predict a more detailed execution set.

## Model artifact details

The committed `planner_model/planner_meta.pkl` shows:

- number of planner nodes: `33`
- max input length: `96`
- model dimension: `128`
- number of attention heads: `8`
- feed-forward dimension: `512`
- number of Transformer layers: `2`

Inference is loaded from:

- `planner_model/planner_model.pt`
- `planner_model/node_to_idx.pkl`
- `planner_model/idx_to_node.pkl`
- `planner_model/planner_meta.pkl`
- tokenizer files in `planner_model/`

## Training data

The training script reads:

- `data/planner/processed/planner_multilabel_dataset.json`

Each record contains:

- `message`
- `active_tasks`
- `required_nodes`

The training code then:

1. builds a node vocabulary
2. converts required nodes into multi-hot labels
3. concatenates tasks and message into model input text
4. splits the dataset into train and validation partitions
5. optimizes `BCEWithLogitsLoss`
6. saves the best checkpoint by validation micro F1

## Metrics computed by the training script

[train_planner.py](train_planner.py) calculates:

- validation loss
- micro F1
- macro F1
- micro precision
- micro recall

No committed planner metrics report was found in the repository, so those values are computed by the code but not yet documented as a saved artifact.

## Runtime output

[run_planner.py](run_planner.py) returns:

- original message
- predicted tasks
- predicted nodes above threshold
- confidence score for every planner node
- attention maps from the model

Those outputs are later transformed by the visualization layer for the frontend.

## Coupling with the rest of the system

- Inputs come from [../router/router.py](../router/router.py).
- Outputs are consumed by [../slr/slr_builder.py](../slr/slr_builder.py).
- Coverage against executor tools can be checked with [../executor/verify_coverage.py](../executor/verify_coverage.py).
