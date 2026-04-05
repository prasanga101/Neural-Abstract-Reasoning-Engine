from abc import ABC, abstractmethod

class BaseTool(ABC):
    """
    Abstract base class for all tools.

    Every tool must:
    - have a name
    - implement the run(context, env) method
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, context: dict, env):
        """
        Execute the tool logic.

        Parameters:
        - context (dict): Outputs from previously executed nodes
            Example:
            {
                "estimate_number_of_casualties": {"estimated_casualties": 350}
            }

        - env (SimulationEnv): Current system state
            Example:
            env.state = {
                "available_ambulances": 20,
                "available_shelters": 10,
                "injury_severity": "critical"
            }

        Returns:
        - dict: Structured output of this tool
        """
        pass