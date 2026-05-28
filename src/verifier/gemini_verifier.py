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
        prompt = f"""
You are a disaster-response verifier.

Validation rules:
- Treat dispatched ambulances and allocated shelters as successful resource use, not as failure.
- It is valid for available_ambulances to become 0 if ambulances_dispatched is present and no count is negative.
- It is valid for available_shelters to decrease if shelters_allocated is present and no count is negative.
- Do not compare available_shelters to relief_resources_allocated; they are different units.
- Only mark invalid for contradictions, missing required emergency outputs, negative resource counts, impossible routes/hospitals, or unsafe recommendations.

Scenario:
{message}

Execution Trace:
{execution_trace}

Final Environment State:
{env_state}

Return ONLY valid JSON in this format:
{{
  "valid": true,
  "reason": "explanation"
}}
"""

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
