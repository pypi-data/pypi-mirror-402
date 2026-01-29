import time
from typing import Dict

class QuarantineSystem:
    """
    Handles function isolation and cooldown.
    """
    def __init__(self, recovery_confidence: float = 0.75):
        self.recovery_confidence = recovery_confidence
        self._quarantine_start = {} # Map[func_id, float]
        self._cooldown_duration = {} # Map[func_id, float]

    def quarantine(self, func_id: str):
        self._quarantine_start[func_id] = time.monotonic()
        # Start with a short cooldown, increase if quarantined repeatedly
        current_duration = self._cooldown_duration.get(func_id, 2.0)
        self._cooldown_duration[func_id] = min(current_duration * 1.3, 10.0)

    def is_quarantined(self, func_id: str) -> bool:
        if func_id not in self._quarantine_start:
            return False
            
        start = self._quarantine_start[func_id]
        duration = self._cooldown_duration[func_id]
        
        if time.monotonic() - start > duration:
            # Cooldown passed, but we might need a "stability proof"
            # For now, we'll allow a transition out of quarantine
            return False
        return True

    def reset_cooldown(self, func_id: str):
        if func_id in self._cooldown_duration:
            del self._cooldown_duration[func_id]
        if func_id in self._quarantine_start:
            del self._quarantine_start[func_id]
