from enum import Enum, auto

class Decision(Enum):
    ALLOW = auto()
    THROTTLE = auto()
    BLOCK = auto()

class DecisionEngine:
    """
    Translates risk scores into execution decisions.
    Uses hysteresis to prevent rapid switching between states.
    """
    def __init__(self, throttle_threshold=0.5, block_threshold=0.8, hysteresis=0.05):
        self.throttle_threshold = throttle_threshold
        self.block_threshold = block_threshold
        self.hysteresis = hysteresis
        self._last_decisions = {} # Map[func_id, Decision]

    def get_decision(self, func_id: str, risk_score: float) -> Decision:
        last_decision = self._last_decisions.get(func_id, Decision.ALLOW)
        
        # Upper thresholds
        if risk_score >= self.block_threshold:
            decision = Decision.BLOCK
        elif risk_score >= self.throttle_threshold:
            decision = Decision.THROTTLE
        else:
            decision = Decision.ALLOW

        # Hysteresis: Only step down if risk has dropped significantly below the threshold
        if last_decision == Decision.BLOCK and risk_score > (self.block_threshold - self.hysteresis):
            decision = Decision.BLOCK
        elif last_decision == Decision.THROTTLE and risk_score > (self.throttle_threshold - self.hysteresis):
            # If we were throttling and risk didn't drop enough to ALLOW, 
            # and it's not high enough to BLOCK, keep THROTTLE
            if decision != Decision.BLOCK:
                decision = Decision.THROTTLE

        self._last_decisions[func_id] = decision
        return decision
