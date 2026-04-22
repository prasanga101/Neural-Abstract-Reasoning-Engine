# Data Directory

This folder holds datasets and data-preparation scripts used by the router and planner parts of the project.

## Main subdirectories

- `raw/`: source disaster message and category data used by abstraction learning.
- `processed/`: processed router dataset artifacts.
- `planner/processed/`: processed planner dataset artifacts.
- `scripts/`: helper scripts for merging and dataset generation.

## Important files referenced in code

- `processed/router_multilabel_dataset.csv`: router training dataset used by the classifier and RL trainer.
- `planner/processed/planner_multilabel_dataset.json`: planner multi-label training dataset.
- `raw/disaster_messages.csv`: raw message dataset used by abstraction learning.
- `raw/disaster_categories.csv`: raw category labels used by abstraction learning.

## Dataset-backed facts visible in the repository

- `router_multilabel_dataset.csv` contains `26,386` data rows plus a header line.
- `planner_multilabel_dataset.json` contains `26,386` message entries.

## Scripts

- [scripts/build_router_dataset.py](scripts/build_router_dataset.py): prepares or rebuilds the router dataset.
- [scripts/generate_planner_dataset.py](scripts/generate_planner_dataset.py): generates the planner dataset.
- [scripts/merge.py](scripts/merge.py): merges related CSV files.

## How this data is used

### Router and RL

Used by:

- [../src/router/task_classifier.py](../src/router/task_classifier.py)
- [../src/rl/trainer.py](../src/rl/trainer.py)

### Planner

Used by:

- [../src/planner/train_planner.py](../src/planner/train_planner.py)

### Abstraction learning

Used by:

- [../src/rl/abstraction_learning.py](../src/rl/abstraction_learning.py)

## Notes

- The data directory is central to reproducibility, but the repository currently does not include a single top-level dataset build command documented in code comments or a root automation script.
- When changing task or node vocabularies, the processed datasets, planner artifacts, and executor coverage should be checked together.
