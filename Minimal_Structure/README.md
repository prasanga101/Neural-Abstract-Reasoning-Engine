# Minimal Structure Prototype

This folder contains an earlier, smaller prototype of the project. It captures the core idea of turning language into a structured plan with validation, but in a lighter and more self-contained way than the main `src/` pipeline.

## Files

- [app.py](app.py): lightweight application entry point.
- [gemini_call.py](gemini_call.py): LLM call logic for structured generation.
- [json_guard.py](json_guard.py): JSON extraction and validation guardrail.
- [mod.py](mod.py): prototype support module.
- [router.py](router.py): prototype router logic.
- [schema.py](schema.py): structured schema definition.
- [sample_plan.json](sample_plan.json): example plan for demo or offline usage.
- [ui_server.py](ui_server.py): prototype UI server.

## Prototype pipeline

The idea here is:

```text
Task text
  -> LLM plan generation
  -> JSON extraction
  -> schema validation
  -> validated structured plan
```

This folder is useful if you want to understand the conceptual beginnings of the system without diving into the full router-planner-SLR-executor-verifier stack.

## When to use this folder

- for quick demos
- for understanding the original structured-output idea
- for UI experimentation around plan visualization
- for comparing the simpler prototype against the newer modular architecture

## Relationship to the main project

The prototype and the production-style `src/` implementation are related, but they are not the same runtime system. The `src/` pipeline is the more complete and modular version.
