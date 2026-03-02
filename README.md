## Major Modules

-   Language-Guided Planning
-   Structured Latent Representation
-   Execution
-   Verifier
-   Repair Loop
-   Abstraction Learning

------------------------------------------------------------------------

## Project Structure

    NEURAL_ABSTRACT_REASONING_ENGINE/
    ├─ Algorith/
    │  ├─ .obsidian/
    │  ├─ Abstraction  Learning.md
    │  ├─ Execution.md
    │  ├─ Language-Guided Planning.md
    │  ├─ Neural Abstract Reasonine Engine.md
    │  ├─ Repair Loop.md
    │  ├─ Structured Latent Representation.md
    │  └─ Verifier.md
    │
    ├─ Minimal_Structure/
    │  ├─ __pycache__/
    │  ├─ app.py
    │  ├─ gemini_call.py
    │  ├─ json_guard.py
    │  ├─ mod.py
    │  ├─ sample_plan.json
    │  ├─ schema.py
    │  └─ ui_server.py
    │
    ├─ .env
    ├─ .gitignore
    └─ README.md

------------------------------------------------------------------------

## Minimal_Structure (Phase 1 Foundation)

The `Minimal_Structure/` folder is the first working foundation of the
engine.

Pipeline:

    Task (language) → LLM Plan (JSON) → JSON Extract → Schema Validate → Validated Plan (dict)

### File Responsibilities

**gemini_call.py** - Calls the model with strict structured prompt -
Implements retry repair loop - Returns validated structured plan

**schema.py** - Defines required structured latent representation schema

**json_guard.py** - Extracts JSON from raw LLM output - Validates
structure and types - Acts as Verifier layer

**sample_plan.json** - Demo plan (0 API calls) - Used when rate-limited

**ui_server.py** - Interactive graph visualization - Draggable nodes -
Step animation - Demo + Live mode

------------------------------------------------------------------------

## Running the UI

``` bash
cd Minimal_Structure
python ui_server.py
```

Open:

    http://127.0.0.1:5000

### Demo Mode

Loads `sample_plan.json`\
Zero API usage.

### Live Mode

Uses model quota via `generate_plan()`.

------------------------------------------------------------------------

## Example

**Input Grid**

    🟥 🟥
    🟥 🟥

**Output Grid**

    🟥 🟥
    🟥 🟥
    🟥 🟥
    🟥 🟥

It doubled the shape vertically.

------------------------------------------------------------------------

## Conceptual Flow

1.  Thinks and writes JSON plan
2.  Structures allowed moves
3.  Executes steps
4.  Verifies results
5.  Repairs if needed
6.  Learns reusable abstractions