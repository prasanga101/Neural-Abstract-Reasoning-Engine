import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()


class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")

        self.client = genai.Client(api_key=api_key)
        self.model = "models/gemma-3-4b-it"

    def generate_json(self, prompt: str):
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        text = response.text.strip()

        # clean markdown if present
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        try:
            return json.loads(text)
        except Exception:
            return {
                "error": "Invalid JSON",
                "raw": text
            }