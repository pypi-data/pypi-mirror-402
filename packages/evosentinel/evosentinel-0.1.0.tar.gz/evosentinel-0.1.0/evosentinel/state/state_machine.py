from enum import Enum
import threading

class HealthState(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    QUARANTINED = "QUARANTINED"

class StateMachine:
    """
    Manages health states for guarded units.
    Ensures thread-safe transitions.
    """
    def __init__(self):
        self._states = {} # Map[func_id, HealthState]
        self._lock = threading.Lock()
        self._on_transition = None

    def set_on_transition_callback(self, callback):
        self._on_transition = callback

    def get_state(self, func_id: str) -> HealthState:
        return self._states.get(func_id, HealthState.HEALTHY)

    def update_state(self, func_id: str, risk_score: float):
        with self._lock:
            old_state = self.get_state(func_id)
            
            if risk_score >= 0.95:
                new_state = HealthState.QUARANTINED
            elif risk_score >= 0.8:
                new_state = HealthState.CRITICAL
            elif risk_score >= 0.4:
                new_state = HealthState.DEGRADED
            else:
                new_state = HealthState.HEALTHY

            if new_state != old_state:
                self._states[func_id] = new_state
                if self._on_transition:
                    self._on_transition(func_id, old_state, new_state)
