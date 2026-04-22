import random

class BanditAgent:
    def __init__(self, actions):
        self.actions = actions
        self.q_values = {}        # {state: {action: value}}
        self.action_counts = {}   # {state: {action: count}}

    def _get_state_key(self, state):

        return tuple(state.nonzero()[0])

    def select_action(self, state):
        state_key = self._get_state_key(state)

 
        if state_key not in self.q_values:
            self.q_values[state_key] = {a: 0.0 for a in self.actions}
            self.action_counts[state_key] = {a: 0 for a in self.actions}

        q_vals = self.q_values[state_key]

        confidence = max(q_vals.values())
        confidence = max(0, min(1, confidence))  # clamp

        exploration_prob = 1 - confidence

        if random.random() < exploration_prob:
            return random.choice(self.actions)

        max_q = max(q_vals.values())
        best_actions = [a for a, q in q_vals.items() if q == max_q]

        return random.choice(best_actions)

    def update_q_value(self, state, action, reward):
        state_key = self._get_state_key(state)

        if state_key not in self.q_values:
            self.q_values[state_key] = {a: 0.0 for a in self.actions}
            self.action_counts[state_key] = {a: 0 for a in self.actions}

        self.action_counts[state_key][action] += 1
        n = self.action_counts[state_key][action]

        alpha = 1 / n

        self.q_values[state_key][action] += alpha * (
            reward - self.q_values[state_key][action]
        )