import pandas as pd

medical_labels = ["medical_help", "medical_products", "hospitals"]
rescue_labels = ["search_and_rescue", "missing_people"]
relief_labels = ["food", "water", "shelter", "clothing", "aid_centers"]
route_labels = ["transport", "infrastructure_related", "buildings", "other_infrastructure"]
disaster_labels = ["weather_related", "floods", "storm", "fire", "earthquake", "cold", "other_weather"]
resource_labels = ["aid_related", "other_aid", "related"]

ROUTER_TASKS = [
    "medical_response",
    "search_and_rescue_operation",
    "relief_distribution",
    "infrastructure_and_route_planning",
    "disaster_event_monitoring",
    "resource_allocation",
    "general_disaster_information"
]


def map_router_tasks_multilabel(row):
    """
    Returns one binary flag per router task instead of forcing a single class.
    """
    task_map = {
        "medical_response": int(any(row[label] == 1 for label in medical_labels)),
        "search_and_rescue_operation": int(any(row[label] == 1 for label in rescue_labels)),
        "relief_distribution": int(any(row[label] == 1 for label in relief_labels)),
        "infrastructure_and_route_planning": int(any(row[label] == 1 for label in route_labels)),
        "disaster_event_monitoring": int(any(row[label] == 1 for label in disaster_labels)),
        "resource_allocation": int(any(row[label] == 1 for label in resource_labels)),
    }

    # fallback class only if no other task is active
    task_map["general_disaster_information"] = int(sum(task_map.values()) == 0)

    return pd.Series(task_map)


def build_router_dataset(file, op_file):
    df = pd.read_csv(file)

    data = df[["message", "categories"]].copy()
    data["categories"] = data["categories"].apply(lambda x: x.split(";"))

    categories = data["categories"].apply(pd.Series)

    first_row = categories.iloc[0]
    category_names = [x.split("-")[0] for x in first_row]
    categories.columns = category_names

    for column in categories.columns:
        categories[column] = categories[column].apply(lambda x: int(x.split("-")[1]))

    data = pd.concat([data.drop("categories", axis=1), categories], axis=1)

    # build multi-label router targets
    router_labels = data.apply(map_router_tasks_multilabel, axis=1)

    # final dataset
    router_data = pd.concat([data[["message"]], router_labels], axis=1)

    # optional stats
    print("\nLabel counts:")
    for task in ROUTER_TASKS:
        print(f"{task}: {router_data[task].sum()}")

    router_data["num_active_labels"] = router_data[ROUTER_TASKS].sum(axis=1)
    print("\nActive label distribution:")
    print(router_data["num_active_labels"].value_counts().sort_index())

    router_data.to_csv(op_file, index=False)
    print(f"\nMulti-label router dataset saved to: {op_file}")
    print(router_data.head())


if __name__ == "__main__":
    file = "data/processed/disaster_messages_categories.csv"
    op_file = "data/processed/router_multilabel_dataset.csv"
    build_router_dataset(file, op_file)