# Reinforcement Learning Module

This folder contains the abstraction-learning and bandit-routing support used by the router. Its purpose is not to replace the classifier, but to provide an additional decision signal built from a richer abstract state.

## Files

- [abstraction_learning.py](abstraction_learning.py): builds the hybrid state representation and fits its feature transforms.
- [bandit.py](bandit.py): contextual bandit-like action-value agent.
- [epsilon_greedy.py](epsilon_greedy.py): exploration helper.
- [trainer.py](trainer.py): trains the bandit using the router dataset.
- [eval_orthogonality.py](eval_orthogonality.py): diagnostic script for feature-layer independence.
- [bandit.pkl](bandit.pkl): saved trained agent used at runtime.
- [training_log.csv](training_log.csv): saved RL training log.

## Abstraction state design

[abstraction_learning.py](abstraction_learning.py) constructs a `620`-dimensional state vector:

- `384` dimensions: SBERT sentence embedding from `all-MiniLM-L6-v2`
- `200` dimensions: TF-IDF features reduced by PCA
- `36` dimensions: nearest-label co-occurrence representation reduced by PCA

The final vector is normalized before use.

This design gives the RL layer access to:

- semantic meaning
- lexical surface cues
- label-structure information from the dataset

## Training data

The abstraction layer initializes from:

- `data/raw/disaster_messages.csv`
- `data/raw/disaster_categories.csv`

The bandit training loop in [trainer.py](trainer.py) uses:

- `data/processed/router_multilabel_dataset.csv`

## Bandit behavior

[bandit.py](bandit.py) stores:

- action-value estimates per abstract state
- action counts per abstract state

Action selection is confidence-adaptive:

- higher learned confidence reduces exploration
- lower confidence increases random exploration

Updates use an incremental average with:

```text
alpha = 1 / n
```

where `n` is the number of times a state-action pair has been updated.

## Logged metrics found in the repository

The committed [training_log.csv](training_log.csv) records `10` epochs. Within that log:

- lowest recorded training accuracy: about `60.63%`
- highest recorded training accuracy: `62.80%`

The training script also logs average reward per epoch.

Important note: this accuracy is specific to the RL training loop and should not be interpreted as overall system accuracy or API-level correctness.

## Orthogonality diagnostic

[eval_orthogonality.py](eval_orthogonality.py) evaluates representational overlap using:

- CKA between SBERT, TF-IDF, and label layers
- residualized CKA after regressing out TF-IDF

This is useful for checking whether the three abstraction layers provide genuinely different information instead of repeating the same signal.

## How the RL layer is used at runtime

[../router/router.py](../router/router.py) loads `bandit.pkl`, extracts an abstraction state, requests an RL action, and then merges that action with classifier predictions before downstream planning.
