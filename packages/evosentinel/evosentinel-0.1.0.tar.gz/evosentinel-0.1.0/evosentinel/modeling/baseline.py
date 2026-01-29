from dataclasses import dataclass, field
from .decay import EWMA
import math

@dataclass
class FunctionBaseline:
    """
    Maintains a statistical profile of a specific function's behavior.
    """
    latency_ewma: EWMA = field(default_factory=lambda: EWMA(alpha=0.1))
    latency_variance_ewma: EWMA = field(default_factory=lambda: EWMA(alpha=0.1))
    failure_rate_ewma: EWMA = field(default_factory=lambda: EWMA(alpha=0.05))
    
    def update_metrics(self, latency: float, is_failure: bool):
        # Update latency baseline
        avg_latency = self.latency_ewma.update(latency)
        
        # Update variance (jitter analysis)
        diff = abs(latency - avg_latency)
        self.latency_variance_ewma.update(diff)
        
        # Update failure rate
        self.failure_rate_ewma.update(1.0 if is_failure else 0.0)

    def decay(self, factor: float = 0.95):
        if self.failure_rate_ewma.value is not None:
            self.failure_rate_ewma.value *= factor
        if self.latency_variance_ewma.value is not None:
            self.latency_variance_ewma.value *= factor

    @property
    def avg_latency(self) -> float:
        return self.latency_ewma.value or 0.0

    @property
    def latency_jitter(self) -> float:
        return self.latency_variance_ewma.value or 0.0

    @property
    def failure_rate(self) -> float:
        return self.failure_rate_ewma.value or 0.0
