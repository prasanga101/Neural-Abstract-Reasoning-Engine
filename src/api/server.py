from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from src.visualization.pipeline_viz import build_pipeline_viz

app = FastAPI()

# allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    message: str

@app.post("/run")
def run_pipeline(req: RunRequest):
    print("🔥 RUNNING PIPELINE WITH:", req.message)

    result = build_pipeline_viz(req.message)

    print("🔥 RESULT:", result)

    return result