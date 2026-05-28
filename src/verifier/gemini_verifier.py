import os
import json
import logging
from dotenv import load_dotenv
import requests

load_dotenv()

logger = logging.getLogger(__name__)

_DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
_DEFAULT_OLLAMA_MODEL = "llama3.2"
_REQUEST_TIMEOUT = 120


class OllamaVerifier:
    def __init__(self, api_key=None):
        self.base_url = os.getenv("OLLAMA_BASE_URL", _DEFAULT_OLLAMA_BASE_URL).rstrip("/")
        self.model_name = os.getenv("OLLAMA_VERIFIER_MODEL", os.getenv("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL))

    def validate(self, message, execution_trace, env_state):
        # Build a concise summary of key outputs to avoid overwhelming the model
        state_summary = {
            "hospitals_found": len(env_state.get("nearby_hospitals") or env_state.get("available_hospitals") or []),
            "routes_found": len(env_state.get("alternative_routes") or []),
            "best_route": env_state.get("optimized_route"),
            "ambulances_remaining": env_state.get("available_ambulances"),
            "ambulances_dispatched": env_state.get("ambulances_dispatched", 0),
            "shelters_remaining": env_state.get("available_shelters"),
            "shelters_allocated": env_state.get("shelters_allocated", 0),
            "injury_severity": env_state.get("injury_severity"),
            "estimated_casualties": env_state.get("estimated_casualties"),
            "rescue_teams_allocated": env_state.get("rescue_teams_allocated"),
            "relief_resources_allocated": env_state.get("relief_resources_allocated", 0),
            "blocked_routes": env_state.get("blocked_routes", []),
        }

        completed_steps = [
            step["node"] for step in (execution_trace or [])
            if step.get("status") == "completed"
        ]

        prompt = f"""You are a disaster-response pipeline verifier. Assess whether the pipeline produced a valid emergency response.

Mark VALID if:
- At least one hospital was identified, OR at least one route was computed
- No resource count is negative
- Ambulances being 0 after dispatch is acceptable (resources were used)
- Internal computation fields (injury_severity, damage_assessment, etc.) having any value or None is acceptable

Mark INVALID only if:
- A resource count is negative
- The best_route is to a location that makes no sense for the scenario
- A critical step clearly failed and left the state in an unsafe condition

Scenario: {message}

Completed steps: {completed_steps}

Key state summary:
{json.dumps(state_summary, indent=2, default=str)}

Return ONLY valid JSON:
{{
  "valid": true,
  "reason": "one sentence explanation"
}}"""

        last_error = None

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=_REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            text = response.json().get("response", "").strip()
            text = text.replace("```json", "").replace("```", "").strip()

            start = text.find("{")
            end = text.rfind("}")

            if start != -1 and end != -1:
                text = text[start:end + 1]

            return json.loads(text)

        except Exception as e:
            last_error = e
            logger.warning("Ollama verification failed: %s", e)

        return {
            "valid": None,
            "reason": f"Ollama verification unavailable: {last_error}",
        }


GeminiVerifier = OllamaVerifier
