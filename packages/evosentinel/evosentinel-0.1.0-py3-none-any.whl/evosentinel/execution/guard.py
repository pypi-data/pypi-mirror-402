import asyncio
import functools
import time
from typing import Callable, Any, Optional
from ..core.signals import ExecutionSignal, global_bus
from ..core.risk_engine import RiskEngine
from ..core.decision_engine import DecisionEngine, Decision
from ..state.state_machine import StateMachine, HealthState
from ..state.quarantine import QuarantineSystem
from ..errors import SentinelBlockedError, SentinelQuarantinedError
from .retry import ProbabilisticRetry
from ..hooks.lifecycle import hooks

class SentinelGuard:
    """
    Orchestrates the guarding logic for a function.
    """
    def __init__(self, 
                 risk_engine: RiskEngine, 
                 decision_engine: DecisionEngine,
                 state_machine: StateMachine,
                 quarantine_system: QuarantineSystem,
                 retry_logic: ProbabilisticRetry):
        self.risk_engine = risk_engine
        self.decision_engine = decision_engine
        self.state_machine = state_machine
        self.quarantine_system = quarantine_system
        self.retry_logic = retry_logic

    def guard(self, func_id: str):
        def decorator(func: Callable):
            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def wrapper(*args, **kwargs):
                    return await self._execute_async(func_id, func, *args, **kwargs)
            else:
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    return self._execute_sync(func_id, func, *args, **kwargs)
            return wrapper
        return decorator

    def _pre_execute(self, func_id: str):
        # 1. Check Quarantine
        if self.quarantine_system.is_quarantined(func_id):
            raise SentinelQuarantinedError(f"Function {func_id} is quarantined.")
        
        # If it was quarantined but the duration expired, ensure state machine reflects it
        if self.state_machine.get_state(func_id) == HealthState.QUARANTINED:
            # Re-evaluate risk to move out of quarantine state
            current_risk = self.risk_engine.calculate_risk(func_id)
            self.state_machine.update_state(func_id, current_risk)
            if self.state_machine.get_state(func_id) != HealthState.QUARANTINED:
                hooks.trigger("on_recovery", func_id)

        # 2. Risk Evaluation
        risk = self.risk_engine.calculate_risk(func_id)
        decision = self.decision_engine.get_decision(func_id, risk)

        if decision == Decision.BLOCK:
            raise SentinelBlockedError(f"Execution of {func_id} blocked. Risk: {risk:.2f}")
        
        return risk

    def _post_execute(self, func_id: str, start_time: float, exception: Optional[Exception]):
        execution_time = time.monotonic() - start_time
        signal = ExecutionSignal(func_id, execution_time, exception)
        
        # Update engines
        self.risk_engine.record_signal(signal)
        new_risk = self.risk_engine.calculate_risk(func_id)
        hooks.trigger("on_risk_change", func_id, new_risk)
        self.state_machine.update_state(func_id, new_risk)
        
        if self.state_machine.get_state(func_id) == HealthState.QUARANTINED:
            self.quarantine_system.quarantine(func_id)
            hooks.trigger("on_quarantine", func_id)
            
        global_bus.emit(signal)

    def _execute_sync(self, func_id: str, func: Callable, *args, **kwargs):
        while True:
            risk = self._pre_execute(func_id)
            start_time = time.monotonic()
            try:
                result = func(*args, **kwargs)
                self._post_execute(func_id, start_time, None)
                return result
            except Exception as e:
                self._post_execute(func_id, start_time, e)
                if self.retry_logic.should_retry(risk):
                    time.sleep(self.retry_logic.get_backoff(risk))
                    continue
                raise

    async def _execute_async(self, func_id: str, func: Callable, *args, **kwargs):
        while True:
            risk = self._pre_execute(func_id)
            start_time = time.monotonic()
            try:
                result = await func(*args, **kwargs)
                self._post_execute(func_id, start_time, None)
                return result
            except Exception as e:
                self._post_execute(func_id, start_time, e)
                if self.retry_logic.should_retry(risk):
                    await asyncio.sleep(self.retry_logic.get_backoff(risk))
                    continue
                raise
