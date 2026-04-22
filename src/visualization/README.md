# Visualization Module

This folder contains small adapters that turn raw backend outputs into shapes that are easier for the React frontend to render.

## Files

- [router_viz.py](router_viz.py): formats router predictions and scores.
- [planner_viz.py](planner_viz.py): formats planner node scores and selections.
- [slr_graph_viz.py](slr_graph_viz.py): formats structured graph information.
- [executor_viz.py](executor_viz.py): formats execution trace and outputs.
- [verifier_viz.py](verifier_viz.py): formats overall, rule-based, and model-based verification status.
- [state_viz.py](state_viz.py): formats final environment state.
- [pipeline_viz.py](pipeline_viz.py): pipeline-level visualization helper.
- [attention_viz.py](attention_viz.py): attention-map related formatting.
- [embedding_viz.py](embedding_viz.py): embedding visualization helper.
- [reasoning_graph_viz.py](reasoning_graph_viz.py): reasoning graph formatting helper.
- [reasoning_graph.py](reasoning_graph.py): visualization-side graph support.

## Purpose

These files are important because they keep the core pipeline code focused on reasoning while giving the frontend cleaner, stable payloads for panels and graph views.

Instead of forcing the UI to understand every raw backend structure, the visualization layer provides smaller frontend-ready summaries like:

- selected tasks and top score
- planner node ranking
- execution trace steps
- verification validity flags
- final environment snapshot

## Main integration point

The API service imports these builders inside [../api/server.py](../api/server.py) when constructing the response for `/run` and `/output`.

## Notes

- This folder is presentation-oriented. It does not perform core reasoning or execution.
- Changes here usually affect what the frontend can display, not what the backend decides.
