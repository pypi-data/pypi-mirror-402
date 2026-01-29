import time
import random
from evosentinel import sentinel
from evosentinel.errors import SentinelError

# Observability Hooks
@sentinel.on_state_transition
def handle_transition(func_id, old_state, new_state):
    print(f"DEBUG: [{func_id}] {old_state} -> {new_state}")

@sentinel.on_risk_change
def handle_risk(func_id, score):
    print(f"DEBUG: [{func_id}] Risk Score: {score:.4f}")

@sentinel.on_quarantine
def handle_quarantine(func_id):
    print(f"DEBUG: [{func_id}] !!! QUARANTINED !!!")

@sentinel.on_recovery
def handle_recovery(func_id):
    print(f"DEBUG: [{func_id}] <<< RECOVERED >>>")

# Simulated unstable function
@sentinel.guard("payment.charge")
def unstable_charge():
    # Simulate healing: 70% failure for first 10 calls, then 10% failure
    if not hasattr(unstable_charge, "calls"):
        unstable_charge.calls = 0
    
    unstable_charge.calls += 1
    fail_prob = 0.7 if unstable_charge.calls < 10 else 0.05
    
    if random.random() < fail_prob:
        raise Exception("Service Timeout")
    return "SUCCESS"

def run_simulation(iterations=20):
    print("\n--- Starting Failure Simulation ---\n")
    for i in range(iterations):
        print(f"Iteration {i+1}: ", end="")
        try:
            res = unstable_charge()
            print(f"Result: {res}")
        except SentinelError as e:
            print(f"Sentinel Action: {type(e).__name__}")
        except Exception as e:
            print(f"Unhandled Exception: {e}")
        time.sleep(0.5)

    print("\n--- Simulation Finished ---\n")

if __name__ == "__main__":
    run_simulation(50)
