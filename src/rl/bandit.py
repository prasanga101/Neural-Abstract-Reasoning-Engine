import numpy as np

class BanditAgent:
    def __init__(self, actions, state_dim=620, alpha=0.01):
        self.actions   = actions
        self.alpha     = alpha
        self.n_actions = len(actions)
        self.state_dim = state_dim

        # Linear weights — one row per action
        # This is what makes it contextual — W @ state
        self.W = np.zeros((self.n_actions, state_dim))
        self.action_index = {a: i for i, a in enumerate(actions)}

    def select_action(self, state, epsilon=0.15):
        # Epsilon greedy exploration
        if np.random.random() < epsilon:
            return np.random.choice(self.actions)

        # Score each action via dot product with state
        scores = self.W @ state  # (n_actions,)
        best_idx = np.argmax(scores)
        return self.actions[best_idx]

    def update_q_value(self, state, action, reward):
        idx = self.action_index[action]
        # Gradient update — move weights toward rewarding state
        prediction = self.W[idx] @ state
        error      = reward - prediction
        self.W[idx] += self.alpha * error * state