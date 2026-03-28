import json
from typing import List, Dict, Tuple


def load_data(json_file: str) -> Tuple[List[str], List[str], List[List[str]]]:
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = [item["message"] for item in data]
    task_types = [item["task_type"] for item in data]
    required_nodes = [item["required_nodes"] for item in data]

    return texts, task_types, required_nodes


def build_task_vocab(task_types: List[str]) -> Tuple[Dict[str, int], Dict[int, str]]:
    unique_tasks = sorted(set(task_types))

    task_to_idx = {task: i for i, task in enumerate(unique_tasks)}
    idx_to_task = {i: task for task, i in task_to_idx.items()}

    return task_to_idx, idx_to_task


def build_nodes_vocab(required_nodes: List[List[str]]) -> Tuple[Dict[str, int], Dict[int, str], List[str]]:
    node_set = set()

    for nodes in required_nodes:
        for node in nodes:
            node_set.add(node)

    node_list = sorted(list(node_set))

    # special tokens
    node_list.append("<END>")
    node_list.append("<PAD>")

    node_to_idx = {node: i for i, node in enumerate(node_list)}
    idx_to_node = {i: node for node, i in node_to_idx.items()}

    return node_to_idx, idx_to_node, node_list


def get_max_steps(required_nodes: List[List[str]]) -> int:
    # +1 for <END>
    return max(len(nodes) for nodes in required_nodes) + 1


def encode_node_sequence(
    nodes: List[str],
    node_to_idx: Dict[str, int],
    max_steps: int
) -> List[int]:
    encoded = [node_to_idx[node] for node in nodes]

    # add END token
    encoded.append(node_to_idx["<END>"])

    # trim if too long
    encoded = encoded[:max_steps]

    # pad if too short
    while len(encoded) < max_steps:
        encoded.append(node_to_idx["<PAD>"])

    return encoded


def encode_all_node_sequences(
    required_nodes: List[List[str]],
    node_to_idx: Dict[str, int],
    max_steps: int
) -> List[List[int]]:
    return [
        encode_node_sequence(nodes, node_to_idx, max_steps)
        for nodes in required_nodes
    ]


def encode_task_ids(task_types: List[str], task_to_idx: Dict[str, int]) -> List[int]:
    return [task_to_idx[task] for task in task_types]


def build_input_text(texts: List[str], task_types: List[str]) -> List[str]:
    return [
        f"task_type: {task_type} | query: {text}"
        for text, task_type in zip(texts, task_types)
    ]


def decode_node_sequence(
    prediction_ids: List[int],
    idx_to_node: Dict[int, str]
) -> List[str]:
    decoded = []

    for idx in prediction_ids:
        node = idx_to_node[idx]

        if node == "<END>":
            break

        if node == "<PAD>":
            continue

        decoded.append(node)

    return decoded


def decode_batch_sequences(
    batch_prediction_ids: List[List[int]],
    idx_to_node: Dict[int, str]
) -> List[List[str]]:
    return [
        decode_node_sequence(prediction_ids, idx_to_node)
        for prediction_ids in batch_prediction_ids
    ]