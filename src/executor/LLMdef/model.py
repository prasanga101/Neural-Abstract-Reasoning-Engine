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


class OllamaClient:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", _DEFAULT_OLLAMA_BASE_URL).rstrip("/")
        self.model = os.getenv("OLLAMA_TOOL_MODEL", os.getenv("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL))

    def generate_json(self, prompt: str) -> dict:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=_REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            text = response.json().get("response", "").strip()
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            try:
                return json.loads(text)
            except Exception:
                return {"error": "Invalid JSON", "raw": text}

        except Exception as e:
            logger.warning("Ollama generation failed: %s", e)
            return {"error": f"Ollama unavailable: {e}"}


GeminiClient = OllamaClient
