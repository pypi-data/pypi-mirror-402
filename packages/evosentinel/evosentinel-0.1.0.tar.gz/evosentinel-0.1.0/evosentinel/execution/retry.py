import random
import time
import math

class ProbabilisticRetry:
    """
    Decides whether to retry based on current risk.
    Retry probability P(retry) = (1 - risk) ^ 2
    Backoff duration = base_backoff * (1 / (1 - risk))
    """
    def __init__(self, base_backoff: float = 0.5):
        self.base_backoff = base_backoff

    def should_retry(self, risk_score: float) -> bool:
        # If risk is too high, probability of retry is low
        # If risk = 0, prob = 1.0
        # If risk = 0.5, prob = 0.25
        # If risk = 0.9, prob = 0.01
        retry_prob = (1.0 - risk_score) ** 2
        return random.random() < retry_prob

    def get_backoff(self, risk_score: float) -> float:
        # Higher risk -> longer backoff
        # risk = 0 -> backoff = base
        # risk = 0.5 -> backoff = base * 2
        # risk = 0.9 -> backoff = base * 10
        multiplier = 1.0 / max(0.01, (1.0 - risk_score))
        jitter = random.uniform(0.8, 1.2)
        return self.base_backoff * multiplier * jitter
