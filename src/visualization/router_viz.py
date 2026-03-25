def build_router_viz(router_result):
    confidence_scores = router_result["confidence_scores"]

    sorted_scores = sorted(
        confidence_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return {
        "tasks": router_result["predicted_tasks"],
        "scores": [
            {"task": task, "score": round(score, 4)}
            for task, score in sorted_scores
        ],
        "top": sorted_scores[0][0] if sorted_scores else None
    }