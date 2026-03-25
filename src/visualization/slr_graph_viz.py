def build_slr_viz(slr_result):
    return {
        "nodes": slr_result["graph_nodes"],
        "edges": [
            {"source": s, "target": t}
            for s, t in slr_result["graph_edges"]
        ],
        "order": slr_result["execution_order"]
    }