import logging
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger("nare.api")
logging.basicConfig(level=logging.INFO)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
ROUTER_MODEL_DIR = REPO_ROOT / "router_model"
PLANNER_MODEL_DIR = REPO_ROOT / "planner_model"
REQUIRED_ROUTER_FILES = [
    "config.json",
    "model.safetensors",
    "tokenizer_config.json",
    "vocab.txt",
]
REQUIRED_PLANNER_FILES = [
    "node_to_idx.pkl",
    "idx_to_node.pkl",
    "planner_meta.pkl",
    "planner_model.pt",
    "tokenizer_config.json",
    "vocab.txt",
]
REQUIRED_VERIFIER_ENV_VARS = ["GEMINI_API_KEY"]
REQUIRED_EXECUTOR_ENV_VARS = ["GEMINI_API_KEY", "GEOAPIFY_API_KEY"]
DEFAULT_TEST_PROMPT = (
    "A major earthquake has struck Pokhara, Nepal. Thousands of people have been "
    "displaced, critical injuries are being reported across multiple areas, and "
    "immediate medical response, shelter allocation, and route coordination are "
    "urgently needed."
)


def get_cors_origins():
    raw_value = os.getenv("NARE_CORS_ORIGINS", "")
    if not raw_value.strip():
        return DEFAULT_CORS_ORIGINS

    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


def missing_files(base_dir: Path, required_files: list[str]):
    return [name for name in required_files if not (base_dir / name).exists()]


def missing_env_vars(required_env_vars: list[str]):
    return [name for name in required_env_vars if not os.getenv(name)]


def get_runtime_readiness():
    router_missing = missing_files(ROUTER_MODEL_DIR, REQUIRED_ROUTER_FILES)
    planner_missing = missing_files(PLANNER_MODEL_DIR, REQUIRED_PLANNER_FILES)
    verifier_missing = missing_env_vars(REQUIRED_VERIFIER_ENV_VARS)
    executor_missing = missing_env_vars(REQUIRED_EXECUTOR_ENV_VARS)

    components = {
        "router": {
            "ready": not router_missing,
            "model_dir": str(ROUTER_MODEL_DIR),
            "missing_files": router_missing,
        },
        "planner": {
            "ready": not planner_missing,
            "model_dir": str(PLANNER_MODEL_DIR),
            "missing_files": planner_missing,
        },
        "slr": {
            "ready": True,
            "missing_files": [],
            "missing_env": [],
        },
        "executor": {
            "ready": not executor_missing,
            "missing_env": executor_missing,
        },
        "verifier": {
            "ready": not verifier_missing,
            "missing_env": verifier_missing,
        },
    }

    return {
        "router_missing": router_missing,
        "planner_missing": planner_missing,
        "executor_missing": executor_missing,
        "verifier_missing": verifier_missing,
        "components": components,
        "ready": all(component["ready"] for component in components.values()),
    }

def build_pipeline_response(pipeline, message: str, threshold: float = 0.5):
    from src.visualization.executor_viz import build_executor_viz
    from src.visualization.planner_viz import build_planner_viz
    from src.visualization.router_viz import build_router_viz
    from src.visualization.slr_graph_viz import build_slr_viz
    from src.visualization.state_viz import build_state_viz
    from src.visualization.verifier_viz import build_verifier_viz

    result = pipeline.run(message, threshold=threshold)

    return {
        "message": message,
        "router": build_router_viz(result["router_result"]),
        "planner": build_planner_viz(result["planner_result"]),
        "slr": build_slr_viz(result["slr_result"]),
        "executor": build_executor_viz(result["execution_result"]),
        "verifier": build_verifier_viz(result["verification_result"]),
        "state": build_state_viz(result["final_environment_state"]),
    }


def ensure_pipeline_ready():
    readiness = get_runtime_readiness()
    app.state.runtime_readiness = readiness

    if app.state.pipeline is None:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Pipeline is not available.",
                "startup_error": app.state.startup_error,
            },
        )

    if not readiness["ready"]:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Pipeline assets are not ready yet.",
                "router_missing": readiness["router_missing"],
                "planner_missing": readiness["planner_missing"],
                "executor_missing": readiness["executor_missing"],
                "verifier_missing": readiness["verifier_missing"],
                "components": readiness["components"],
            },
        )

    return readiness


def execute_pipeline(message: str, threshold: float = 0.5):
    started_at = perf_counter()

    try:
        payload = build_pipeline_response(app.state.pipeline, message, threshold)
    except Exception as exc:
        logger.exception("Pipeline execution failed")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Pipeline execution failed.",
                "error": str(exc),
            },
        ) from exc

    duration_ms = round((perf_counter() - started_at) * 1000, 2)
    logger.info("Pipeline run completed in %sms", duration_ms)

    return {
        "prompt": message,
        "threshold": threshold,
        "duration_ms": duration_ms,
        "output": payload,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pipeline = None
    app.state.startup_error = None
    app.state.runtime_readiness = get_runtime_readiness()

    try:
        logger.info("Initializing NARE reasoning pipeline...")
        from src.pipeline.reasoning_pipeline import ReasoningPipeline

        app.state.pipeline = ReasoningPipeline()
        logger.info("NARE reasoning pipeline ready.")
    except Exception as exc:
        app.state.startup_error = str(exc)
        logger.exception("Failed to initialize reasoning pipeline")

    yield


app = FastAPI(
    title="NARE API",
    description="Backend API for the Neural Abstract Reasoning Engine frontend.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Emergency message to run through the pipeline.")
    threshold: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Probability threshold applied to router and planner selection.",
    )


@app.get("/")
def root():
    readiness = get_runtime_readiness()
    app.state.runtime_readiness = readiness

    return {
        "name": "NARE API",
        "status": "ready" if app.state.pipeline and readiness["ready"] else "degraded",
        "docs": "/docs",
        "planner_missing": readiness["planner_missing"],
        "router_missing": readiness["router_missing"],
        "executor_missing": readiness["executor_missing"],
        "verifier_missing": readiness["verifier_missing"],
        "components": readiness["components"],
    }


@app.get("/health")
def health():
    readiness = get_runtime_readiness()
    app.state.runtime_readiness = readiness

    return {
        "ok": app.state.pipeline is not None and readiness["ready"],
        "pipeline_loaded": app.state.pipeline is not None,
        "startup_error": app.state.startup_error,
        "router_missing": readiness["router_missing"],
        "planner_missing": readiness["planner_missing"],
        "executor_missing": readiness["executor_missing"],
        "verifier_missing": readiness["verifier_missing"],
        "components": readiness["components"],
    }


@app.get("/output")
def output(message: str = DEFAULT_TEST_PROMPT, threshold: float = 0.5):
    prompt = message.strip()

    if not prompt:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    ensure_pipeline_ready()
    payload = execute_pipeline(prompt, threshold)
    return Response(
        content=json.dumps(payload, indent=2, ensure_ascii=False),
        media_type="application/json",
    )


@app.post("/run")
def run_pipeline(req: RunRequest):
    message = req.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    ensure_pipeline_ready()
    return execute_pipeline(message, req.threshold)
