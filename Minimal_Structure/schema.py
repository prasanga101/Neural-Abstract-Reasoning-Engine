PLAN_SCHEMA = {
    "task": str,
    "reasoning_steps": [
        {
            "step_id": int,
            "step_description": str,
            "required_tools": list,
            "produced_content": list
        }
    ],
    "final_output": str
}