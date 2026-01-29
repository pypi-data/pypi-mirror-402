from .signals import ExecutionSignal
from ..modeling.baseline import FunctionBaseline
from ..modeling.decay import DecaySignal
import math

class RiskEngine:
    """
    Computes a risk score (0.0 - 1.0) for a function.
    """
    def __init__(self, risk_decay=0.92, max_risk=1.0):
        self.risk_decay = risk_decay
        self.max_risk = max_risk
        # Tracks the intensity/frequency of recent failures
        self.failure_momentum = {} # Map[func_id, DecaySignal]
        self.baselines = {} # Map[func_id, FunctionBaseline]

    def get_baseline(self, func_id: str) -> FunctionBaseline:
        if func_id not in self.baselines:
            self.baselines[func_id] = FunctionBaseline()
        return self.baselines[func_id]

    def _get_momentum(self, func_id: str) -> DecaySignal:
        if func_id not in self.failure_momentum:
            self.failure_momentum[func_id] = DecaySignal(self.risk_decay)
        return self.failure_momentum[func_id]

    def calculate_risk(self, func_id: str) -> float:
        baseline = self.get_baseline(func_id)
        momentum_signal = self._get_momentum(func_id)
        momentum = momentum_signal.get_value()
        
        # We need the baseline failure rate to decay if time has passed
        # This simulates "healing" over time even without new signals
        
        # If momentum has decayed close to zero, we should also allow failure_risk to decay
        if momentum < 0.1:
            baseline.decay(0.98) # Gently decay
            
        failure_risk = baseline.failure_rate
        momentum_risk = min(1.0, momentum / 5.0) # More sensitive momentum
        
        risk = max(failure_risk, momentum_risk)
        return min(self.max_risk, risk)

    def record_signal(self, signal: ExecutionSignal):
        baseline = self.get_baseline(signal.function_id)
        baseline.update_metrics(signal.execution_time, signal.exception is not None)
        
        if signal.exception:
            self._get_momentum(signal.function_id).boost(1.0)
