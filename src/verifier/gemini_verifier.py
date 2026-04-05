import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()


class GeminiVerifier:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")

        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "models/gemma-3-4b-it"

    def validate(self, message, execution_trace, env_state):
        prompt = f"""
You are a disaster-response verifier.

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

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            text = response.text.strip()

            text = text.replace("```json", "").replace("```", "").strip()

            start = text.find("{")
            end = text.rfind("}")

            if start != -1 and end != -1:
                text = text[start:end + 1]

            return json.loads(text)

        except Exception as e:
            return {
                "valid": False,
                "reason": f"Gemini verification failed: {str(e)}"
            }