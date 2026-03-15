import pickle
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification


def load_router_components():
    model = DistilBertForSequenceClassification.from_pretrained("./router_model")
    tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

    with open("./router_model/label_encoder.pkl", "rb") as f:
        le = pickle.load(f)

    return model, tokenizer, le


def get_recommended_tools(task_type):
    if task_type == "medical_response":
        return ["hospital_dispatch", "medical_supply_allocator"]
    elif task_type == "search_and_rescue_operation":
        return ["rescue_team_dispatch", "satellite_scan"]
    elif task_type == "relief_distribution":
        return ["food_distribution_planner", "water_supply_allocator"]
    elif task_type == "infrastructure_and_route_planning":
        return ["route_mapper", "infrastructure_damage_analyzer"]
    elif task_type == "disaster_event_monitoring":
        return ["event_monitor", "severity_estimator"]
    elif task_type == "resource_allocation":
        return ["resource_allocator", "priority_scheduler"]
    else:
        return ["general_disaster_analysis"]


def build_router_response(task_type, confidence, recommended_tools):
    with open("./router_json", "w") as f:
        f.write(str({
            "task_type": task_type,
            "confidence": round(confidence, 4),
            "recommended_tools": recommended_tools
        }))
    return {
        "task_type": task_type,
        "confidence": round(confidence, 4),
        "recommended_tools": recommended_tools
    }