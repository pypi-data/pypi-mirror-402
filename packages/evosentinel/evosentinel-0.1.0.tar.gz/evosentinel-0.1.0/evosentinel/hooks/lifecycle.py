from typing import Callable, List, Dict

class HookRegistry:
    """
    Registry for SDK lifecycle events.
    """
    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {
            "on_risk_change": [],
            "on_state_transition": [],
            "on_quarantine": [],
            "on_recovery": []
        }

    def register(self, event: str, callback: Callable):
        if event in self._hooks:
            self._hooks[event].append(callback)

    def trigger(self, event: str, *args, **kwargs):
        if event in self._hooks:
            for hook in self._hooks[event]:
                hook(*args, **kwargs)

# Global hook registry
hooks = HookRegistry()
