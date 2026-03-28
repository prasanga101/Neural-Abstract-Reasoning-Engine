from src.slr.node_representation import ReasoningNode


class ReasoningGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = []

    def add_node(self, node: ReasoningNode):
        if node.name in self.nodes:
            raise ValueError(f"Node with name {node.name} already exists")
        self.nodes[node.name] = node

    def add_edge(self, from_node: str, to_node: str):
        if from_node not in self.nodes:
            raise ValueError(f"From node {from_node} does not exist")
        if to_node not in self.nodes:
            raise ValueError(f"To node {to_node} does not exist")

        if (from_node, to_node) in self.edges:
            return

        self.edges.append((from_node, to_node))

    def build_from_dependencies(self):
        for node in self.nodes.values():
            for dependency in node.dependencies:
                self.add_edge(dependency, node.name)

    def validate_graph(self):
        for from_node, to_node in self.edges:
            if from_node not in self.nodes:
                raise ValueError(f"From node {from_node} does not exist")
            if to_node not in self.nodes:
                raise ValueError(f"To node {to_node} does not exist")

    def get_execution_order(self):
        in_degree = {node_name: 0 for node_name in self.nodes}

        for from_node, to_node in self.edges:
            in_degree[to_node] += 1

        queue = [node_name for node_name, degree in in_degree.items() if degree == 0]
        execution_order = []

        while queue:
            current = queue.pop(0)
            execution_order.append(current)

            for from_node, to_node in self.edges:
                if from_node == current:
                    in_degree[to_node] -= 1
                    if in_degree[to_node] == 0:
                        queue.append(to_node)

        if len(execution_order) != len(self.nodes):
            raise ValueError("Graph contains a cycle")

        return execution_order