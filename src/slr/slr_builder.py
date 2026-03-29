from src.slr.node_representation import ReasoningNode
from src.slr.reasoning_graph import ReasoningGraph

class SLRBuilder:
    def build(self , message , task_type, confidence , predicted_nodes):
        clean_nodes = []
        for node in predicted_nodes:
            if node == "<END>":
                break
            if node and node not in clean_nodes:
                clean_nodes.append(node)
        if not clean_nodes:
            raise ValueError("No valid nodes found in the predicted sequence")
            
        reasoning_graph = ReasoningGraph()

        reasoning_graph.message = message
        reasoning_graph.task_type = task_type
        reasoning_graph.confidence = confidence

        previous_node = None
        for i, node_name in enumerate(clean_nodes):
            # Assign dependency (sequential for now)
            dependencies = [previous_node.name] if previous_node else []

            node = ReasoningNode(
                name=node_name,
                node_type="action",
                description="",
                inputs=[],
                outputs=[],
                dependencies=dependencies,
                priority=i + 1,
                status="pending"
            )

            # Add node to graph
            reasoning_graph.add_node(node)

            # Update previous node
            previous_node = node

        # -----------------------------
        # Step 4: Build edges
        # -----------------------------
        reasoning_graph.build_from_dependencies()

        # -----------------------------
        # Step 5: Validate graph
        # -----------------------------
        reasoning_graph.validate_graph()

        return reasoning_graph
    
if __name__ == "__main__":
    # -----------------------------
    # Mock planner output (test case)
    # -----------------------------
    message = "There is a tsunami in India, hundreds of people are displaced with critical injuries"
    task_type = "medical_response"
    confidence = 0.75

    predicted_nodes = [
        "assess_injury_severity",
        "estimate_number_of_casualties",
        "identify_nearest_hospitals",
        "dispatch_ambulances",
        "allocate_temporary_shelters",
        "<END>"
    ]

    # -----------------------------
    # Build SLR graph
    # -----------------------------
    builder = SLRBuilder()
    graph = builder.build(message, task_type, confidence, predicted_nodes)

    # -----------------------------
    # Print results
    # -----------------------------
    print("\n--- SLR GRAPH TEST ---")

    print("\nMessage:")
    print(graph.message)

    print("\nTask Type:", graph.task_type)
    print("Confidence:", graph.confidence)

    print("\nNodes:")
    for node_name, node in graph.nodes.items():
        print(f"  {node_name} | dependencies: {node.dependencies}")

    print("\nEdges:")
    for edge in graph.edges:
        print(f"  {edge[0]} -> {edge[1]}")

    print("\nExecution Order:")
    execution_order = graph.get_execution_order()
    for i, step in enumerate(execution_order, start=1):
        print(f"  Step {i}: {step}")