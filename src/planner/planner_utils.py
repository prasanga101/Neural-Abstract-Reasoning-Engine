import json
import torch
NODE_SET = set()
def load_data(json_file):
    with open(json_file , "r") as f:
        data = json.load(f)
    texts = [item["message"] for item in data]
    labels = [item["task_type"] for item in data]
    req_nodes = [item["required_nodes"] for item in data]
    return texts, labels, req_nodes

def build_nodes_vocab(req_nodes):
    for nodes in req_nodes:
        NODE_SET.update(nodes)
    node_list = list(NODE_SET)
    node_to_idx ={node:i for i , node in enumerate(node_list)}
    idx_to_node = {i:node for i , node in enumerate(node_list)}
    return node_to_idx , idx_to_node , node_list

def multi_hot_label(req_nodes , node_to_idx):
    multi_hot = torch.zeros(len(req_nodes), len(node_to_idx), dtype=torch.float32)
    for i , nodes in enumerate(req_nodes):
        for node in nodes:
            if node in node_to_idx:
                multi_hot[i][node_to_idx[node]] = 1.0
    return multi_hot

def build_input_text(text , labels):
    return [f"task_type: {label} | query: {text}" for text , label in zip(text , labels)]

def decode_nodes(prediction , idx_to_node):
    nodes = []
    for idx , score in enumerate(prediction):
        if score > 0.5:
            nodes.append(idx_to_node[idx])
    return nodes

