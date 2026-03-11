# router_schema.py (or inside router.py)
ROUTER_SCHEMA = {
    "domain": str,
    "allowed_tools": list,   # list[str] (validated separately)
    "constraints": {
        "max_steps": int,
        "max_tool_calls": int
    }
}