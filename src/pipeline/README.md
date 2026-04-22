# Pipeline Module

This folder contains the top-level orchestration logic that wires the router, planner, SLR builder, executor, and verifier into one callable pipeline.

## Files

- [reasoning_pipeline.py](reasoning_pipeline.py): primary end-to-end pipeline class.
- [test_pl.py](test_pl.py): pipeline test or experiment entry point.

## Main class

[reasoning_pipeline.py](reasoning_pipeline.py) defines `ReasoningPipeline`, which performs the system in five major stages:

1. Router
2. Planner
3. Structured latent representation build
4. Execution
5. Verification

## Detailed run order

### Router stage

Loads router model/tokenizer and calls:

- `load_router_components()`
- `route_query()`

Outputs:

- predicted tasks
- task confidence scores

### Planner stage

Calls `predict_plan()` with:

- original message
- predicted tasks
- runtime threshold

Outputs:

- predicted nodes
- node confidence scores

### SLR stage

Uses `SLRBuilder.build()` to create a dependency-complete reasoning graph.

### Execution stage

Creates:

- `SimulationEnv`
- `ResourceAllocator`
- `Executor`

Then runs `executor.execute()`.

### Verification stage

Calls `Verifier.verify()` with:

- original message
- execution result
- environment

## Returned structure

The pipeline returns a single dictionary containing:

- `message`
- `router_result`
- `planner_result`
- `slr_result`
- `execution_result`
- `verification_result`
- `final_environment_state`

This is the main payload later consumed by the API layer and transformed again for visualization.

## Why this folder matters

If you want to understand the whole project quickly, start here. This folder shows the exact contract between all major modules without getting lost in training code or frontend wiring.
