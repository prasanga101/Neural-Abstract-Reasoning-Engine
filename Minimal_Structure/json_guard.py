from schema import PLAN_SCHEMA
import json
def validate_plan(plan: dict):

    if not isinstance(plan, dict):
        raise ValueError("Plan must be a dictionary.")

    # ---- Top-level keys ----
    required_keys = ["task", "reasoning_steps", "final_output"]

    for key in required_keys:
        if key not in plan:
            raise ValueError(f"Missing required key: {key}")

    if not isinstance(plan["task"], str):
        raise ValueError("task must be string")

    if not isinstance(plan["final_output"], str):
        raise ValueError("final_output must be string")

    if not isinstance(plan["reasoning_steps"], list):
        raise ValueError("reasoning_steps must be a list")

    if len(plan["reasoning_steps"]) == 0:
        raise ValueError("reasoning_steps cannot be empty")


    for step in plan["reasoning_steps"]:

        if not isinstance(step, dict):
            raise ValueError("Each reasoning step must be a dictionary")

        step_keys = ["step_id", "step_description", "required_tools", "produced_content"]

        for key in step_keys:
            if key not in step:
                raise ValueError(f"Missing '{key}' in reasoning step")

        if not isinstance(step["step_id"], int):
            raise ValueError("step_id must be int")

        if not isinstance(step["step_description"], str):
            raise ValueError("step_description must be string")

        if not isinstance(step["required_tools"], list):
            raise ValueError("required_tools must be list")

        if not isinstance(step["produced_content"], list):
            raise ValueError("produced_content must be list")

        # Validate produced_content structure
        for item in step["produced_content"]:
            if not isinstance(item, dict):
                raise ValueError("produced_content items must be dictionaries")

            if "type" not in item or "value" not in item:
                raise ValueError("produced_content items must contain 'type' and 'value'")

            if not isinstance(item["type"], str):
                raise ValueError("produced_content.type must be string")

            if not isinstance(item["value"], str):
                raise ValueError("produced_content.value must be string")

    return plan



#Extraxtion process
def extraxt_json(text : str)-> dict:
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    
    cleaned = text.strip() #"\n   hello   \n".strip() → "hello
    cleaned = cleaned.replace("```json","").replace("```","").strip() # remove code block markers if present
    try:
        return json.loads(cleaned) #tries to parse the cleansed string as JSON
    except json.JSONDecodeError:
        pass
    start = cleaned.find("{")
    if start == -1:
        raise ValueError("No JSON object found in the input")
    brace_count = 0
    for i in range(start , len(cleaned)):
        if cleaned[i] == "{":
            brace_count += 1
        elif cleaned[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                candidate = cleaned[start:i+1] #0 huda it means we have matched the { and }
                try:
                    return json.loads(candidate) #tries to parse the candidate substring as JSON
                except json.JSONDecodeError:
                    pass
    raise ValueError("No valid JSON object found in the input")
                   
def guard(text: str) -> dict:
    extracted = extraxt_json(text)
    validated = validate_plan(extracted)
    return validated