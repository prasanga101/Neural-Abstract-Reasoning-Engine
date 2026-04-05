class ResourceAllocator:
    def __init__(self, env):
        self.env = env

    def allocate_ambulances(self):
        casualties = self.env.get_state("estimated_casualties") or 0
        available = self.env.get_state("available_ambulances") or 0

        needed = casualties // 10
        allocated = min(needed, available)

        self.env.update_state("available_ambulances", available - allocated)

        return {
            "ambulances_sent": allocated
        }

    def allocate_shelters(self):
        casualties = self.env.get_state("estimated_casualties") or 0
        available = self.env.get_state("available_shelters") or 0

        needed = casualties // 50
        allocated = min(needed, available)

        self.env.update_state("available_shelters", available - allocated)

        return {
            "shelters_allocated": allocated
        }