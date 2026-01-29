import numpy as np

class MaxNet:
    """
    MaxNet Competitive Neural Network
    Implements winner-take-all using lateral inhibition
    """

    def __init__(self, epsilon=0.1, max_iter=100):
        self.epsilon = epsilon
        self.max_iter = max_iter

    def run(self, inputs):
        x = np.array(inputs, dtype=float)

        if np.any(x < 0):
            raise ValueError("Inputs must be non-negative")

        for _ in range(self.max_iter):
            x_new = x.copy()

            for i in range(len(x)):
                inhibition = self.epsilon * (np.sum(x) - x[i])
                x_new[i] = x[i] - inhibition

            x_new[x_new < 0] = 0

            if np.count_nonzero(x_new) == 1:
                break

            x = x_new

        return int(np.argmax(x))
