from dataclasses import dataclass, field
from typing import Type, Optional
import time

@dataclass(frozen=True)
class ExecutionSignal:
    """
    Data container for a single execution cycle.
    """
    function_id: str
    execution_time: float
    exception: Optional[Exception] = None
    timestamp: float = field(default_factory=lambda: time.monotonic())

class SignalBus:
    """
    In-memory bus to record signals. 
    In the simplest form, it just passes signals to subscribers (modeling layer).
    """
    def __init__(self):
        self._subscribers = []

    def subscribe(self, callback):
        self._subscribers.append(callback)

    def emit(self, signal: ExecutionSignal):
        for sub in self._subscribers:
            sub(signal)

# Global signal bus for the SDK
global_bus = SignalBus()
