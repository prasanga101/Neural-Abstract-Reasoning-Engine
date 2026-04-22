# Neural Abstract Reasoning Engine

Neural Abstract Reasoning Engine, or `NARE`, is a multi-stage disaster-response reasoning system that turns a natural-language emergency message into a structured execution graph, runs tool-backed response steps, and verifies the result before returning a final state.

At a high level, the repository combines:

- A multi-label router that predicts disaster-response task families.
- A planner that expands those tasks into executable reasoning nodes.
- A structured latent representation (`SLR`) graph builder with dependency closure.
- An executor that runs domain tools against a shared simulation environment.
- A verifier that combines rule-based checks with an LLM-based review step.
- An RL-assisted abstraction layer that can inject fallback or complementary routing decisions.
- A FastAPI backend and a React frontend for interactive inspection.

## End-to-end flow

```text
User message
  -> Router (DistilBERT + RL fallback/injection)
  -> Planner (Transformer multi-label node prediction)
  -> SLR Builder (dependency-complete DAG)
  -> Executor (tool registry + simulation state)
  -> Verifier (rule checks + Gemini/Gemma validation)
  -> Visualization payload / API response
```

The main orchestration entry point is [src/pipeline/reasoning_pipeline.py](src/pipeline/reasoning_pipeline.py).

## Repository map

The most important directories are:

- [src/api/README.md](src/api/README.md): FastAPI service and readiness checks.
- [src/router/README.md](src/router/README.md): task routing and RL-assisted hybrid selection.
- [src/planner/README.md](src/planner/README.md): Transformer planner training and inference.
- [src/slr/README.md](src/slr/README.md): reasoning node and graph construction.
- [src/executor/README.md](src/executor/README.md): tool execution, shared state, and coverage checks.
- [src/verifier/README.md](src/verifier/README.md): deterministic and model-based validation.
- [src/rl/README.md](src/rl/README.md): abstraction learning, bandit routing support, and diagnostics.
- [src/pipeline/README.md](src/pipeline/README.md): end-to-end pipeline composition.
- [src/visualization/README.md](src/visualization/README.md): payload shaping for the UI.
- [src/frontend/README.md](src/frontend/README.md): React/Vite visualization client.
- [data/README.md](data/README.md): datasets and dataset scripts.
- [Minimal_Structure/README.md](Minimal_Structure/README.md): earlier prototype implementation.

## Main components

### 1. Router

The router predicts one or more high-level task families from an emergency message:

- `medical_response`
- `search_and_rescue_operation`
- `relief_distribution`
- `infrastructure_and_route_planning`
- `disaster_event_monitoring`
- `resource_allocation`
- `general_disaster_information`

The classifier is implemented in [src/router/task_classifier.py](src/router/task_classifier.py). The runtime routing logic in [src/router/router.py](src/router/router.py) blends:

- classifier predictions,
- a reinforcement-learning action from `src/rl/bandit.pkl`,
- threshold filtering,
- task-to-node expansion through [src/router/config.py](src/router/config.py).

If the classifier produces no confident labels, the RL action becomes the base fallback. If the RL action differs from the classifier output, it can also be injected as an extra candidate.

### 2. Planner

The planner consumes the original message and the router task set, then predicts reasoning nodes using a custom Transformer model defined across:

- [src/planner/transformer_planner.py](src/planner/transformer_planner.py)
- [src/planner/transformer_block.py](src/planner/transformer_block.py)
- [src/planner/multi_head_attention.py](src/planner/multi_head_attention.py)
- [src/planner/embeddings.py](src/planner/embeddings.py)
- [src/planner/feed_forward.py](src/planner/feed_forward.py)

Inference is handled by [src/planner/run_planner.py](src/planner/run_planner.py). The committed planner artifact metadata in `planner_model/planner_meta.pkl` indicates:

- `33` planner nodes
- max input length `96`
- model width `128`
- `8` attention heads
- feed-forward size `512`
- `2` Transformer layers

### 3. Structured Latent Representation

The SLR stage converts predicted nodes into a dependency-complete graph. [src/slr/slr_builder.py](src/slr/slr_builder.py) recursively pulls in prerequisite nodes from a dependency map, then constructs a DAG using:

- [src/slr/node_representation.py](src/slr/node_representation.py)
- [src/slr/reasoning_graph.py](src/slr/reasoning_graph.py)

The resulting graph determines the execution order.

### 4. Executor

The executor runs tools in topological order over a shared simulation environment:

- [src/executor/executor.py](src/executor/executor.py)
- [src/executor/tool_registry.py](src/executor/tool_registry.py)
- [src/executor/simulation_env.py](src/executor/simulation_env.py)
- [src/executor/resource_allocator.py](src/executor/resource_allocator.py)

Each node is resolved to a tool implementation. Successful outputs are stored in execution context and the environment. Failures stop execution and return the partial trace.

### 5. Verifier

The verifier merges two validation strategies:

- [src/verifier/rule_checker.py](src/verifier/rule_checker.py): deterministic checks on environment state, expected outputs, and dependency preconditions.
- [src/verifier/gemini_verifier.py](src/verifier/gemini_verifier.py): LLM-based review that asks a Gemini-compatible client to return strict JSON containing a validity decision and reason.

These are combined in [src/verifier/verifier.py](src/verifier/verifier.py).

### 6. RL Abstraction Layer

The RL support layer builds a `620`-dimensional normalized state representation in [src/rl/abstraction_learning.py](src/rl/abstraction_learning.py):

- `384` dimensions from `all-MiniLM-L6-v2` sentence embeddings
- `200` dimensions from TF-IDF projected with PCA
- `36` dimensions from label co-occurrence PCA

That state is used by the bandit agent in [src/rl/bandit.py](src/rl/bandit.py) to select a routing action.

## Data and model artifacts

Committed assets referenced by the codebase include:

- `router_model/`: saved DistilBERT router weights and tokenizer files
- `router_model/checkpoint-*`: training checkpoints with trainer state and metrics
- `planner_model/`: saved planner weights, tokenizer, and metadata
- `src/rl/bandit.pkl`: persisted bandit policy
- `data/processed/router_multilabel_dataset.csv`: router dataset
- `data/planner/processed/planner_multilabel_dataset.json`: planner dataset

Repo-backed dataset counts visible from the committed files:

- Router dataset: `26,386` training rows plus header line in CSV
- Planner dataset: `26,386` message entries in JSON

## Metrics found in the repository

This section only includes metrics that are directly visible in committed artifacts or logs.

### Router metrics

The best committed router checkpoint state in `router_model/checkpoint-5278/trainer_state.json` and `router_model/checkpoint-7917/trainer_state.json` shows:

- Best validation micro F1: `0.8023598820`
- Validation macro F1: `0.6748119489`
- Validation micro precision: `0.8266055046`
- Validation micro recall: `0.7794960528`

The router training script computes:

- micro F1
- macro F1
- micro precision
- micro recall

### RL training log

The committed RL log at [src/rl/training_log.csv](src/rl/training_log.csv) contains `10` logged epochs. The recorded training accuracy ranges from roughly `60.63%` to `62.80%`.

Important note: this is the bandit's training-time action accuracy against router labels, not end-to-end pipeline accuracy.

### Planner metrics

[src/planner/train_planner.py](src/planner/train_planner.py) computes:

- validation loss
- micro F1
- macro F1
- micro precision
- micro recall

But a persisted planner evaluation summary file is not committed in this repository, so the README intentionally does not invent planner numbers.

## API surface

The FastAPI service in [src/api/server.py](src/api/server.py) exposes:

- `GET /`: service status and component readiness
- `GET /health`: health and startup diagnostics
- `GET /output`: run the pipeline with query parameters
- `POST /run`: run the pipeline with JSON body

Readiness checks verify:

- router model files
- planner model files
- `GEMINI_API_KEY` for the verifier
- `GEMINI_API_KEY` and `GEOAPIFY_API_KEY` for executor dependencies

## Running the project

### Backend only

From the repository root:

```bash
python3 -m uvicorn src.api.server:app --reload --host 127.0.0.1 --port 8000
```

Then open:

- API docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

### Frontend + backend together

The frontend package already defines a combined dev script in [src/frontend/package.json](src/frontend/package.json):

```bash
cd src/frontend
npm install
npm run dev
```

That script starts:

- the FastAPI backend on port `8000`
- the Vite frontend on port `5173`

### Environment variables

At minimum, the backend expects:

```bash
GEMINI_API_KEY=...
GEOAPIFY_API_KEY=...
```

Optional:

```bash
NARE_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Example output structure

The orchestrated response produced by [src/pipeline/reasoning_pipeline.py](src/pipeline/reasoning_pipeline.py) contains:

- original message
- router result
- planner result
- SLR graph summary
- executor result
- verification result
- final environment state

The API wraps that into visualization-friendly payloads for the frontend.

## Notes and current limitations

- There is no committed Python `requirements.txt` or `pyproject.toml` in the root, so Python dependencies are inferred from imports.
- The verifier currently depends on an external model call and will not be ready without `GEMINI_API_KEY`.
- Some executor nodes still rely on registry coverage and dummy-tool fallback behavior if a node is missing.
- The RL bandit uses sparse state-keying based on non-zero indices, which is simple and fast but also fairly coarse.
- Planner metrics are computed in training code, but a committed planner validation report is not currently present.

## Where to go next

If you are navigating the project for the first time, the most useful reading order is:

1. [src/pipeline/README.md](src/pipeline/README.md)
2. [src/router/README.md](src/router/README.md)
3. [src/planner/README.md](src/planner/README.md)
4. [src/slr/README.md](src/slr/README.md)
5. [src/executor/README.md](src/executor/README.md)
6. [src/verifier/README.md](src/verifier/README.md)
