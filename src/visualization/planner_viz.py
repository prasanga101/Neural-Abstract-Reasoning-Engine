def build_planner_viz(planner_result):
    node_scores = planner_result["node_confidence_scores"]

    sorted_nodes = sorted(
        node_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return {
        "nodes": planner_result["predicted_nodes"],
        "scores": [
            {"node": node, "score": round(score, 4)}
            for node, score in sorted_nodes
        ],
        "top": sorted_nodes[0][0] if sorted_nodes else None
    }