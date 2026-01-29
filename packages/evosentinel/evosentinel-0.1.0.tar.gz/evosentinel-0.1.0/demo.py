import time
import random
from evosentinel import sentinel
from evosentinel.errors import SentinelError

# Track state for visualization
state_log = []

# Observability Hooks
@sentinel.on_state_transition
def handle_transition(func_id, old_state, new_state):
    msg = f"🔄 STATE: {old_state.value} → {new_state.value}"
    print(msg)
    state_log.append(msg)

@sentinel.on_risk_change
def handle_risk(func_id, score):
    if score > 0.01:  # Only log significant risk
        print(f"⚠️  RISK: {score:.4f}")

@sentinel.on_quarantine
def handle_quarantine(func_id):
    msg = f"🚨 QUARANTINED: {func_id}"
    print(msg)
    state_log.append(msg)

@sentinel.on_recovery
def handle_recovery(func_id):
    msg = f"✅ RECOVERED: {func_id}"
    print(msg)
    state_log.append(msg)

# Simulated service that becomes stable over time
class UnstableService:
    def __init__(self):
        self.calls = 0
        self.phase = "unstable"
    
    @sentinel.guard("payment.charge")
    def charge(self):
        self.calls += 1
        
        # Phase 1: Very unstable (calls 1-8)
        if self.calls <= 8:
            self.phase = "unstable"
            if random.random() < 0.8:
                raise Exception("Service Timeout")
        # Phase 2: Stabilizing (calls 9-15)
        elif self.calls <= 15:
            self.phase = "stabilizing"
            if random.random() < 0.3:
                raise Exception("Intermittent Error")
        # Phase 3: Stable (calls 16+)
        else:
            self.phase = "stable"
            if random.random() < 0.05:
                raise Exception("Rare Error")
        
        return f"SUCCESS (call #{self.calls})"

def run_demo():
    print("=" * 60)
    print("evoSentinel - Self-Healing Runtime Guard Demo")
    print("=" * 60)
    print()
    
    service = UnstableService()
    
    for i in range(1, 41):
        print(f"\n[Iteration {i}] Phase: {service.phase}")
        print("-" * 40)
        
        try:
            result = service.charge()
            print(f"✓ {result}")
        except SentinelError as e:
            print(f"🛡️  Sentinel Protected: {type(e).__name__}")
        except Exception as e:
            print(f"❌ Application Error: {e}")
        
        # Longer sleep to allow decay
        time.sleep(0.8)
    
    print("\n" + "=" * 60)
    print("Demo Complete")
    print("=" * 60)
    print("\nKey Events:")
    for event in state_log:
        print(f"  {event}")

if __name__ == "__main__":
    run_demo()
