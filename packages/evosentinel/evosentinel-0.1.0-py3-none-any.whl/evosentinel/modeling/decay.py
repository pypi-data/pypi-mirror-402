import time
from typing import Optional

class EWMA:
    """
    Exponentially Weighted Moving Average.
    Provides a way to track a moving average with more weight on recent data.
    """
    def __init__(self, alpha: float):
        if not 0 < alpha <= 1:
            raise ValueError("alpha must be between 0 and 1")
        self.alpha = alpha
        self.value: Optional[float] = None

    def update(self, next_value: float) -> float:
        if self.value is None:
            self.value = next_value
        else:
            self.value = (self.alpha * next_value) + (1.0 - self.alpha) * self.value
        return self.value

def exponential_decay(initial_value: float, decay_rate: float, elapsed_time: float) -> float:
    """
    Calculates the value after exponential decay over time.
    Formula: V = V0 * (rate ^ elapsed_time)
    """
    return initial_value * (decay_rate ** elapsed_time)

class DecaySignal:
    """
    A signal that decays over time unless boosted.
    Useful for tracking recent failures or "momentum".
    """
    def __init__(self, decay_rate: float):
        self.decay_rate = decay_rate
        self.value = 0.0
        self.last_update = time.monotonic()

    def boost(self, amount: float = 1.0):
        self._decay()
        self.value += amount

    def get_value(self) -> float:
        self._decay()
        return self.value

    def _decay(self):
        now = time.monotonic()
        elapsed = now - self.last_update
        self.value = exponential_decay(self.value, self.decay_rate, elapsed)
        self.last_update = now
