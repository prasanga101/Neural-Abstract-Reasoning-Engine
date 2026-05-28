# Reinforcement Learning Module

This folder contains the abstraction-learning and bandit-routing support used by the router. Its purpose is not to replace the classifier, but to provide an additional decision signal built from a richer abstract state.

## Files

- [abstraction_learning.py](abstraction_learning.py): builds the hybrid state representation and fits its feature transforms.
- [bandit.py](bandit.py): contextual bandit-like action-value agent.
- [epsilon_greedy.py](epsilon_greedy.py): exploration helper.
- [trainer.py](trainer.py): trains the bandit using the router dataset.
- [eval_orthogonality.py](eval_orthogonality.py): diagnostic script for feature-layer independence.
- [bandit.pkl](bandit.pkl): saved trained agent used at runtime (full mode).
- [training_log.csv](training_log.csv): saved RL training log.

---

## Ablation Study

### What is being ablated

The `extract()` method in [abstraction_learning.py](abstraction_learning.py) accepts a `mode` argument that enables isolated evaluation of each feature layer:

| Mode | Layers active | State dimension |
|---|---|---|
| `tfidf_only` | TF-IDF PCA | 200 |
| `sbert_only` | SBERT sentence embedding | 384 |
| `full` | SBERT + TF-IDF + Label co-occurrence | 620 |

### How to run

Set `ABLATION_MODE` at the top of [trainer.py](trainer.py) before each run:

```bash
# Run 1 — TF-IDF only
# Set ABLATION_MODE = "tfidf_only" in trainer.py
python -m src.rl.trainer
# → saves bandit_tfidf_only.pkl + training_log_tfidf_only.csv

# Run 2 — SBERT only
# Set ABLATION_MODE = "sbert_only" in trainer.py
python -m src.rl.trainer
# → saves bandit_sbert_only.pkl + training_log_sbert_only.csv

# Run 3 — Full system
# Set ABLATION_MODE = "full" in trainer.py
python -m src.rl.trainer
# → saves bandit_full.pkl + training_log_full.csv
```

Each run uses 100 epochs over 3,000 samples (configurable via `MAX_SAMPLES`).

### Results

| Configuration | State dim | Final accuracy | Avg reward (final epoch) |
|---|---|---|---|
| TF-IDF only | 200 | — | — |
| SBERT only | 384 | — | — |
| Full system | 620 | — | — |

> Fill in after running all three training runs. Expected outcome: `full > sbert_only > tfidf_only`.

### Interpretation guide

- **Full > SBERT only**: the label co-occurrence layer adds signal beyond semantics alone.
- **SBERT only > TF-IDF only**: semantic embeddings capture intent better than surface lexical features.
- **Full > all others**: confirms that all three layers contribute independently — the paper's core claim.

If the ordering is not as expected, run [eval_orthogonality.py](eval_orthogonality.py) to check whether layers are redundant (high CKA = overlapping signal).

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
