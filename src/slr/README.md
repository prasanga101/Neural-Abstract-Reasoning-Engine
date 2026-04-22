# Structured Latent Representation Module

This folder defines the structured latent representation, or `SLR`, used between planning and execution. Its purpose is to turn planner-selected node names into a validated reasoning graph with explicit dependencies and an executable order.

## Files

- [node_representation.py](node_representation.py): `ReasoningNode` data object and validation rules.
- [reasoning_graph.py](reasoning_graph.py): graph storage, edge management, validation, and topological ordering.
- [slr_builder.py](slr_builder.py): dependency-aware graph builder.

## Core concepts

### ReasoningNode

Each node includes:

- `name`
- `node_type`
- `description`
- `inputs`
- `outputs`
- `dependencies`
- `priority`
- `status`

Allowed node types:

- `action`
- `decision`
- `input`
- `output`

Allowed statuses:

- `pending`
- `completed`
- `failed`

### ReasoningGraph

The graph stores:

- `nodes` as a name-to-node mapping
- `edges` as `(from_node, to_node)` tuples

It supports:

- adding nodes
- adding edges
- generating edges from node dependency lists
- validation that all referenced nodes exist
- topological execution ordering

If a cycle is present, `get_execution_order()` raises an error.

## Dependency expansion

[slr_builder.py](slr_builder.py) contains the central dependency map for planner/executor actions. When predicted nodes arrive from the planner, the builder:

1. starts from the predicted node set
2. recursively pulls in all transitive dependencies
3. creates `ReasoningNode` instances
4. builds graph edges from the dependencies
5. validates the graph

This is important because the planner may predict a node that requires other prerequisites not explicitly selected at inference time.

## Why this folder matters

The SLR layer is the boundary between "what should happen" and "what can be executed safely." It gives the executor:

- a dependency-complete action graph
- a deterministic execution order
- a place to encode domain knowledge outside the neural model weights

## Key integration points

- Upstream: [../planner/run_planner.py](../planner/run_planner.py)
- Downstream: [../executor/executor.py](../executor/executor.py)
- Root orchestration: [../pipeline/reasoning_pipeline.py](../pipeline/reasoning_pipeline.py)
