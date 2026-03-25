def build_executor_viz(execution_result):
    timeline = []

    for step in execution_result["execution_trace"]:
        status = step["status"]

        # detect skipped
        if "output" in step and isinstance(step["output"], dict):
            if step["output"].get("status") == "skipped":
                status = "skipped"

        timeline.append({
            "step": step["step"],
            "node": step["node"],
            "status": status
        })

    return {
        "status": execution_result["status"],
        "timeline": timeline
    }