import os
from dotenv import load_dotenv
from google import genai
from json_guard import guard
import json
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not set")

client = genai.Client(api_key=api_key)

SYSTEM_PROMPT = """
You are a planning module for Neural Abstract Reasoning Engine (NARE).

You MUST return ONLY a single valid JSON object.
No markdown. No extra text. No code fences.

REQUIRED top-level keys (must all exist):
- task (string)
- reasoning_steps (list)
- final_output (string)

If any required key is missing, your output is invalid.

JSON schema:

{
  "task": "string",
  "reasoning_steps": [
    {
      "step_id": 1,
      "step_description": "string",
      "required_tools": ["string"],
      "produced_content": [
        {"type": "string", "value": "string"}
      ]
    }
  ],
  "final_output": "string"
}
""".strip()

def generate_plan(task:str, retries: int =3)->dict:
    last_error = None
    for i in range(1 , retries+1):
        resp = client.models.generate_content(
            model="models/gemma-3-1b-it",
            contents = [
                {
                    "role": "user",
                    "parts":[
                    {"text": SYSTEM_PROMPT},
                    {"text": f"Task: {task}"}
                    ]
                }
            ]
        )
        raw = resp.text or ""
        try:
            return guard(raw)
        except Exception as e:
            last_error = e
            print(f"Attempt {i} failed: {e}")

        task = (
    f"{task}\n\n"
    f"The previous output was INVALID because: {last_error}.\n"
    f"You MUST fix the JSON and include all required keys.\n"
    f"Return full valid JSON only."
        )
    raise ValueError(f"All {retries} attempts failed. Last error: {last_error}")


if __name__ == "__main__":
    user_task = "Sort these in Ascending Order: 5, 2, 9, 1"
    plan = generate_plan(user_task, retries=3)
    print(json.dumps(plan, indent=2))