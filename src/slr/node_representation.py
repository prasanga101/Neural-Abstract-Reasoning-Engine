class ReasoningNode:
    def __init__(
            self,
            name : str,
            node_type : str = "action",
            description : str = "",
            inputs : list = None,
            outputs : list = None,
            dependencies: list = None,
            priority : int = 0 ,
            status: str = "pending",
            ):
        if not name:
            raise ValueError("Node must have a name")
        self.name = name.strip()
        self.node_type = node_type.lower()
        self.description = description
        self.inputs = inputs if inputs is not None else []
        self.outputs = outputs if outputs is not None else []
        self.dependencies = dependencies if dependencies is not None else []
        self.priority = priority
        self.status = status.lower()

        self._validate()

    def _validate(self):
        allowed_types = ['action', 'decision', 'input' , 'output']
        allowed_status = ['pending', 'completed', 'failed']

        if self.node_type not in allowed_types:
            raise ValueError(f"Invalid node type: {self.node_type}")
        
        if self.status not in allowed_status:
            raise ValueError(f"Invalid status: {self.status}")
        
        if not isinstance(self.inputs , list):
            raise ValueError("The input must be a list")
        
        if not isinstance(self.outputs, list):
            raise ValueError("The outputs must be a list")
        
        if not isinstance(self.dependencies, list):
            raise ValueError("The dependency must be a list")
        


            

