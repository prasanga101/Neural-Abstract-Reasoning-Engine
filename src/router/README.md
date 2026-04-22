# Router Module

This folder contains the task-routing layer. The router reads a free-form emergency message and predicts the high-level response task families that should drive downstream planning.

The router in this repository is hybrid:

- a supervised DistilBERT multi-label classifier predicts task probabilities
- an RL bandit proposes an action from an abstraction state
- runtime logic merges, filters, and maps those task decisions into executor/planner nodes

## Files

- [task_classifier.py](task_classifier.py): trains and runs the DistilBERT multi-label classifier.
- [router.py](router.py): runtime routing logic that merges classifier and RL outputs.
- [router_utils.py](router_utils.py): model loading and response formatting helpers.
- [config.py](config.py): task-to-node map, router confidence threshold, and fallback behavior.
- [node_mapper.py](node_mapper.py): filters selected tasks and expands them into node names.
- [schemas.py](schemas.py): schema definitions used by the router layer.

## Supported task families

The committed configuration maps messages into these task groups:

- `medical_response`
- `search_and_rescue_operation`
- `resource_allocation`
- `relief_distribution`
- `disaster_event_monitoring`
- `infrastructure_and_route_planning`
- `general_disaster_information`

The canonical mapping lives in [config.py](config.py).

## Runtime behavior

The router flow in [router.py](router.py) is:

1. Build an abstraction state from the incoming message.
2. Predict task labels and confidence scores with the classifier.
3. Ask the RL bandit for one action.
4. Use classifier output as the base if any labels were predicted.
5. Otherwise fall back to the RL action.
6. Inject the RL action if it is not already present.
7. Filter tasks by confidence threshold.
8. Expand final tasks into required nodes.

This gives the system a simple form of hybrid robustness: supervised predictions lead when available, but RL can still propose a plausible fallback or complementary task.

## Training details

[task_classifier.py](task_classifier.py) trains a `DistilBertForSequenceClassification` model in multi-label mode and reports:

- micro F1
- macro F1
- micro precision
- micro recall

Training settings directly visible in code:

- base model: `distilbert-base-uncased`
- max token length: `64`
- epochs: `3`
- batch size: `8`
- best-model metric: `micro_f1`

## Metrics committed in the repository

Router checkpoint trainer state files show the best committed validation metrics:

- micro F1: `0.8023598820`
- macro F1: `0.6748119489`
- micro precision: `0.8266055046`
- micro recall: `0.7794960528`

These values come from committed `trainer_state.json` files under `router_model/checkpoint-*`.

## Model loading

[router_utils.py](router_utils.py) loads both tokenizer and model from the repository's `router_model/` directory and automatically places the model on CUDA when available.

## Important interactions

- The router feeds tasks into the planner in [../planner/run_planner.py](../planner/run_planner.py).
- It also uses the abstraction learner from [../rl/abstraction_learning.py](../rl/abstraction_learning.py).
- Node expansion must remain consistent with executor tool names and planner node vocabulary.
