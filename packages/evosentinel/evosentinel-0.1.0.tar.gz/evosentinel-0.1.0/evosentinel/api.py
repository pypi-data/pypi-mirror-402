from .core.signals import global_bus
from .core.risk_engine import RiskEngine
from .core.decision_engine import DecisionEngine
from .state.state_machine import StateMachine
from .state.quarantine import QuarantineSystem
from .execution.retry import ProbabilisticRetry
from .execution.guard import SentinelGuard
from .hooks.lifecycle import hooks

class Sentinel:
    """
    Main SDK entry point.
    """
    def __init__(self,
                 observation_window: int = 120,
                 risk_decay: float = 0.92,
                 max_risk: float = 0.85,
                 quarantine_threshold: float = 0.95,
                 recovery_confidence: float = 0.75):
        
        self.risk_engine = RiskEngine(risk_decay=risk_decay)
        self.decision_engine = DecisionEngine(block_threshold=max_risk)
        self.state_machine = StateMachine()
        self.quarantine_system = QuarantineSystem(recovery_confidence=recovery_confidence)
        self.retry_logic = ProbabilisticRetry()
        
        self._guard_orchestrator = SentinelGuard(
            risk_engine=self.risk_engine,
            decision_engine=self.decision_engine,
            state_machine=self.state_machine,
            quarantine_system=self.quarantine_system,
            retry_logic=self.retry_logic
        )

    def guard(self, func_id: str):
        """Decorator and context manager entry point."""
        return self._guard_orchestrator.guard(func_id)

    def on_risk_change(self, callback):
        hooks.register("on_risk_change", callback)

    def on_state_transition(self, callback):
        hooks.register("on_state_transition", callback)
        self.state_machine.set_on_transition_callback(callback)

    def on_quarantine(self, callback):
        hooks.register("on_quarantine", callback)

    def on_recovery(self, callback):
        hooks.register("on_recovery", callback)

# Default instance
sentinel = Sentinel()
