# API Module

This folder contains the FastAPI backend for the Neural Abstract Reasoning Engine. Its job is to load the reasoning pipeline, check that required model artifacts and environment variables exist, execute the pipeline, and reshape raw pipeline output into frontend-friendly JSON.

Main file:

- [server.py](server.py): FastAPI application, startup lifecycle, readiness validation, and HTTP endpoints.

## Responsibilities

- Create and hold a singleton `ReasoningPipeline` instance during app lifespan.
- Validate runtime readiness before allowing requests to run.
- Expose health and execution endpoints.
- Convert raw pipeline results into visualization payloads using the `src/visualization` helpers.
- Measure request execution time and return it alongside the output.

## Endpoints

### `GET /`

Returns service metadata and component readiness, including whether router, planner, executor, verifier, and SLR are currently ready.

### `GET /health`

Returns a detailed health payload with:

- `ok`
- `pipeline_loaded`
- `startup_error`
- missing router files
- missing planner files
- missing executor environment variables
- missing verifier environment variables

### `GET /output`

Runs the pipeline using query parameters:

- `message`
- `threshold`

This endpoint returns formatted JSON as a raw `Response`.

### `POST /run`

Runs the pipeline using a JSON body:

```json
{
  "message": "A major earthquake has struck Pokhara, Nepal...",
  "threshold": 0.5
}
```

## Runtime readiness model

The API checks four categories before declaring the service ready:

- Router model files in `router_model/`
- Planner model files in `planner_model/`
- `GEMINI_API_KEY` for verifier calls
- `GEMINI_API_KEY` and `GEOAPIFY_API_KEY` for executor dependencies

If the pipeline object exists but assets are incomplete, the API returns `503` with a structured readiness report instead of silently failing.

## Output shaping

The `build_pipeline_response()` helper imports and uses:

- `build_router_viz`
- `build_planner_viz`
- `build_slr_viz`
- `build_executor_viz`
- `build_verifier_viz`
- `build_state_viz`

This keeps the backend response aligned with the UI panels rather than exposing only raw internal objects.

## Useful files outside this folder

- [../pipeline/reasoning_pipeline.py](../pipeline/reasoning_pipeline.py): orchestration logic the API calls.
- [../visualization/README.md](../visualization/README.md): explains the visualization payload builders.
- [../../README.md](../../README.md): top-level project overview.
