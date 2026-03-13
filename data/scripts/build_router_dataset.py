import pandas as pd
import os

medical_labels = ["medical_help", "medical_products", "hospitals"]
rescue_labels = ["search_and_rescue", "missing_people"]
relief_labels = ["food", "water", "shelter", "clothing", "aid_centers"]
route_labels = ["transport", "infrastructure_related", "buildings", "other_infrastructure"]
disaster_labels = ["weather_related", "floods", "storm", "fire", "earthquake", "cold", "other_weather"]
resource_labels = ["aid_related", "other_aid", "related"]


def map_router_task(row):
    if any(row[label] == 1 for label in medical_labels):
        return 'medical_response'
    elif any(row[label] == 1 for label in rescue_labels):
        return 'search_and_rescue_operation'
    elif any(row[label] == 1 for label in relief_labels):
        return 'relief_distribution'
    elif any(row[label] == 1 for label in route_labels):
        return 'infrastructure_and_route_planning'
    elif any(row[label] == 1 for label in disaster_labels):
        return 'disaster_event_monitoring'
    elif any(row[label] == 1 for label in resource_labels):
        return 'resource_allocation'
    else:
        return 'general_disaster_information'


def build_router_dataset(file, op_file):

    df = pd.read_csv(file)

    data = df[['message', 'categories']].copy()

    data['categories'] = data['categories'].apply(lambda x: x.split(';'))

    categories = data['categories'].apply(pd.Series)

    row = categories.iloc[0]
    category_names = [x.split('-')[0] for x in row]
    categories.columns = category_names

    for column in categories:
        categories[column] = categories[column].apply(lambda x: int(x.split('-')[1]))

    data = pd.concat([data.drop('categories', axis=1), categories], axis=1)

    # create router label
    data["task_type"] = data.apply(map_router_task, axis=1)

    # keep only final columns
    router_data = data[["message", "task_type"]]

    # save router dataset
    router_data.to_csv(op_file, index=False)

    print("Router dataset created successfully.")
    print(router_data.head())


if __name__ == "__main__":

    file = "data/processed/disaster_messages_categories.csv"
    op_file = "data/processed/router_dataset.csv"

    build_router_dataset(file, op_file)