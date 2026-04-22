# Executor Module

This folder contains the execution layer that runs planned reasoning nodes against a shared environment using domain-specific tools.

## Files

- [executor.py](executor.py): executes graph nodes in topological order and records the execution trace.
- [tool_registry.py](tool_registry.py): maps node names to concrete tool implementations.
- [simulation_env.py](simulation_env.py): mutable shared environment state.
- [resource_allocator.py](resource_allocator.py): simple ambulance and shelter allocation helpers.
- [base_tools.py](base_tools.py): abstract tool interface.
- [verify_coverage.py](verify_coverage.py): checks planner node coverage against executor tools.
- [LLMdef/model.py](LLMdef/model.py): model-related executor support.
- [LLMdef/population_details.py](LLMdef/population_details.py): population-related executor support.
- [tools/assessment_tools.py](tools/assessment_tools.py): assessment-focused tool implementations.
- [tools/allocation_tools.py](tools/allocation_tools.py): allocation-focused tool implementations.
- [tools/monitoring_tools.py](tools/monitoring_tools.py): monitoring-focused tool implementations.
- [tools/response_tools.py](tools/response_tools.py): response-focused tool implementations.
- [tools/routing_tools.py](tools/routing_tools.py): routing and path-related tool implementations.

## Execution model

[executor.py](executor.py) performs the following loop:

1. ask the reasoning graph for execution order
2. resolve each node name through the registry
3. run the tool with the shared `context` and `env`
4. store outputs in the context
5. mark node status
6. append a structured execution trace record

If any tool raises an exception, execution stops early and the partial trace is returned with `status = "failed"`.

## Shared state

[simulation_env.py](simulation_env.py) initializes the environment with:

- `message`
- `injury_severity`
- `estimated_casualties`
- `available_ambulances`
- `available_hospitals`
- `available_shelters`

Tools can read and update this state throughout the run.

## Tool registry

[tool_registry.py](tool_registry.py) is the central contract between planner node names and executable functionality. It includes registered implementations for areas such as:

- event context analysis
- injury and casualty assessment
- route and blockage detection
- hospital and rescue response
- resource analysis and allocation
- disaster monitoring and reporting

If a tool name is missing, the registry falls back to a `DummyTool` that returns a structured "not implemented yet" response instead of crashing immediately at lookup time.

## Coverage checking

[verify_coverage.py](verify_coverage.py) compares:

- planner node names from `planner_model/node_to_idx.pkl`
- executor tool names from the registry

This is a useful consistency check whenever planner vocabulary or executor capabilities change.

## Resource allocation helper

[resource_allocator.py](resource_allocator.py) currently includes simple heuristics:

- ambulances needed = casualties divided by `10`
- shelters needed = casualties divided by `50`

The allocator then caps allocation by current availability and writes the updated counts back into the environment.

## Integration points

- Input graph from [../slr/reasoning_graph.py](../slr/reasoning_graph.py)
- Verification by [../verifier/verifier.py](../verifier/verifier.py)
- Orchestration by [../pipeline/reasoning_pipeline.py](../pipeline/reasoning_pipeline.py)
