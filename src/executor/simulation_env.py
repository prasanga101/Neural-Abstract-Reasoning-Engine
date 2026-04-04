class SimulationEnv:
    def __init__(self , message:str):
        self.state = {
            "message": message,
            "injury_severity": None,
            "estimated_casualties": None,
            "available_ambulances": 20,
            "available_hospitals": [],
            "available_shelters": 10
        }
    '''
    key , value used here are the parameters that reads a value from the environment
    env.get_state("available_ambulances"). usage of key
    env.update_state("estimated_casualties", 350) usage of key and value
    env.get_full_state() usage of getting the full state of the environment
    '''
    def get_state(self , key):
        return self.state.get(key)

    def update_state(self, key, value):
        self.state[key] = value
    
    def get_full_state(self):
        return self.state
    