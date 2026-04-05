import pickle
from src.executor.tool_registry import ToolRegistry

PLANNER_MODEL_DIR = "planner_model"


def load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def main():
    node_to_idx = load_pickle(f"{PLANNER_MODEL_DIR}/node_to_idx.pkl")
    planner_nodes = set(node_to_idx.keys())

    registry = ToolRegistry()
    executor_nodes = set(registry.tools.keys())

    missing_in_registry = sorted(planner_nodes - executor_nodes)
    extra_in_registry = sorted(executor_nodes - planner_nodes)

    print("\n=== COVERAGE REPORT ===\n")

    print(f"Planner node count: {len(planner_nodes)}")
    print(f"Executor tool count: {len(executor_nodes)}")

    if not missing_in_registry:
        print("\nAll planner nodes are covered by executor tools.")
    else:
        print("\nMissing in executor registry:")
        for node in missing_in_registry:
            print(f"  - {node}")

    if not extra_in_registry:
        print("\nNo extra tools found in executor registry.")
    else:
        print("\nExtra tools in executor registry (not currently used by planner):")
        for node in extra_in_registry:
            print(f"  - {node}")

    print("\n=== END OF REPORT ===\n")


if __name__ == "__main__":
    main()