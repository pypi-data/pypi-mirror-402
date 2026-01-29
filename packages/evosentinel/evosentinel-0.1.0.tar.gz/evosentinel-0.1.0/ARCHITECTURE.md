# evoSentinel Architecture

**Author**: Daksha Dubey

---

## Design Principles

### 1. Separation of Concerns

Each layer has a **single responsibility**:

- **Signal Capture**: Observe, don't decide
- **Behavioral Modeling**: Build context, don't act
- **Risk Scoring**: Quantify, don't control
- **Decision Engine**: Control, don't observe

This separation allows each layer to be:
- Tested independently
- Optimized separately
- Replaced without affecting others

### 2. No Global Mutable State

All state is:
- Scoped to function IDs
- Protected by locks where necessary
- Immutable where possible

This ensures **thread safety** and **predictable behavior** in concurrent environments.

### 3. Time-Aware Algorithms

Unlike traditional approaches that use counters, evoSentinel uses **time-based decay**:

```python
# Traditional (counter-based)
if failure_count > 5:
    block()

# evoSentinel (time-based)
risk = baseline.failure_rate + momentum.get_value()
if risk > threshold:
    block()
```

Time-based approaches naturally handle:
- Variable request rates
- Bursty traffic patterns
- Long-tail latencies

### 4. Probabilistic Decision Making

Deterministic thresholds create **cliff effects**. evoSentinel uses **probability distributions**:

```python
# Retry probability decreases smoothly with risk
P(retry) = (1 - risk)²

# At risk=0.0: P=1.00 (always retry)
# At risk=0.5: P=0.25 (25% chance)
# At risk=0.9: P=0.01 (1% chance)
```

This creates **graceful degradation** instead of hard cutoffs.

---

## Component Deep Dive

### Signal Capture Layer

**Location**: `evosentinel/core/signals.py`

**Responsibility**: Collect raw execution data

**Key Metrics**:
- Execution time (monotonic clock)
- Exception type (if any)
- Timestamp

**Design Notes**:
- Zero decision logic
- Immutable signal objects
- Event bus for extensibility

### Behavioral Modeling Layer

**Location**: `evosentinel/modeling/`

**Algorithms**:

1. **EWMA (Exponentially Weighted Moving Average)**
   ```python
   V_new = α × V_current + (1 - α) × V_previous
   ```
   - α = 0.1 for latency (slow adaptation)
   - α = 0.05 for failure rate (very slow)

2. **Variance Tracking**
   ```python
   jitter = EWMA(|latency - avg_latency|)
   ```

3. **Decay Function**
   ```python
   V(t) = V₀ × (decay_rate ^ elapsed_time)
   ```

**Why EWMA?**
- O(1) time and space complexity
- Adapts to changing baselines
- More weight on recent data
- No need to store history

### Risk Scoring Engine

**Location**: `evosentinel/core/risk_engine.py`

**Risk Calculation**:

```python
risk = max(
    baseline.failure_rate,
    momentum / sensitivity
)
```

**Components**:
1. **Baseline Risk**: Long-term failure rate (EWMA)
2. **Momentum Risk**: Recent failure burst intensity (decay signal)

**Self-Healing Mechanism**:
```python
if momentum < 0.1:
    baseline.decay(0.98)  # Gradually reduce baseline risk
```

This allows the system to **forget** old failures when stability returns.

### Decision Engine

**Location**: `evosentinel/core/decision_engine.py`

**State Transitions**:

```
risk < 0.5:  ALLOW
0.5 ≤ risk < 0.8:  THROTTLE
risk ≥ 0.8:  BLOCK
```

**Hysteresis**:
To prevent rapid state flapping, we add a **hysteresis band**:

```python
# To step down from BLOCK to THROTTLE:
# Risk must drop below (block_threshold - hysteresis)
if last_decision == BLOCK and risk > (0.8 - 0.05):
    decision = BLOCK  # Stay blocked
```

### Health State Machine

**Location**: `evosentinel/state/state_machine.py`

**States**:
- **HEALTHY**: risk < 0.4
- **DEGRADED**: 0.4 ≤ risk < 0.8
- **CRITICAL**: 0.8 ≤ risk < 0.95
- **QUARANTINED**: risk ≥ 0.95

**Thread Safety**:
```python
with self._lock:
    old_state = self.get_state(func_id)
    new_state = calculate_new_state(risk)
    if new_state != old_state:
        self._states[func_id] = new_state
        trigger_callback(func_id, old_state, new_state)
```

### Quarantine System

**Location**: `evosentinel/state/quarantine.py`

**Adaptive Cooldown**:
```python
# First quarantine: 2 seconds
# Second quarantine: 2.6 seconds
# Third quarantine: 3.38 seconds
# Capped at 10 seconds

cooldown = min(current * 1.3, 10.0)
```

**Recovery Check**:
```python
if time.monotonic() - start > cooldown:
    # Allow re-evaluation
    return False  # Not quarantined
```

### Execution Guard

**Location**: `evosentinel/execution/guard.py`

**Execution Flow**:

```
1. Pre-execution:
   ├─ Check quarantine status
   ├─ Calculate current risk
   └─ Get decision (ALLOW/THROTTLE/BLOCK)

2. Execution:
   └─ Run protected function

3. Post-execution:
   ├─ Record signal
   ├─ Update risk
   ├─ Update state machine
   └─ Trigger hooks
```

**Async Support**:
```python
if asyncio.iscoroutinefunction(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await self._execute_async(...)
```

### Probabilistic Retry

**Location**: `evosentinel/execution/retry.py`

**Retry Decision**:
```python
retry_prob = (1 - risk_score) ** 2
return random.random() < retry_prob
```

**Adaptive Backoff**:
```python
multiplier = 1.0 / max(0.01, (1 - risk_score))
jitter = random.uniform(0.8, 1.2)
backoff = base_backoff * multiplier * jitter
```

**Why This Works**:
- High risk → low retry probability → fewer wasted attempts
- High risk → long backoff → reduced system pressure
- Jitter prevents thundering herd

---

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Signal capture | O(1) | Direct field access |
| EWMA update | O(1) | Single multiplication |
| Risk calculation | O(1) | Two EWMA lookups |
| Decision | O(1) | Threshold comparison |
| State transition | O(1) | Lock + dict update |

**Total overhead per guarded call**: **O(1)**

### Space Complexity

Per guarded function:
- Baseline: 3 EWMA objects × 16 bytes = 48 bytes
- Momentum: 1 DecaySignal × 24 bytes = 24 bytes
- State: 1 enum value = 8 bytes
- Quarantine: 2 floats = 16 bytes

**Total**: ~96 bytes per function

For 1000 guarded functions: **~96 KB**

---

## Concurrency Model

### Thread Safety Guarantees

1. **State Machine**: Protected by `threading.Lock`
2. **Risk Engine**: Per-function state, no shared mutation
3. **Quarantine**: Atomic time comparisons
4. **EWMA**: Single-threaded per function (safe due to GIL)

### Async Support

- Detects coroutine functions automatically
- Uses `asyncio.sleep()` for backoff
- No blocking calls in async path

---

## Extension Points

### Custom Risk Factors

```python
class CustomRiskEngine(RiskEngine):
    def calculate_risk(self, func_id: str) -> float:
        base_risk = super().calculate_risk(func_id)
        
        # Add custom factors
        latency_risk = self.calculate_latency_risk(func_id)
        
        return max(base_risk, latency_risk)
```

### Custom Decision Logic

```python
class CustomDecisionEngine(DecisionEngine):
    def get_decision(self, func_id: str, risk: float) -> Decision:
        # Custom business logic
        if is_critical_time():
            return Decision.ALLOW  # Always allow during critical hours
        return super().get_decision(func_id, risk)
```

---

## Testing Strategy

### Unit Tests

- Test each algorithm in isolation
- Verify EWMA convergence
- Validate decay functions
- Check probability distributions

### Integration Tests

- Full guard lifecycle
- State transitions
- Hook triggering
- Error propagation

### Concurrency Tests

- Thread safety under load
- Async/sync interop
- Race condition detection

### Property-Based Tests

- Risk scores always in [0, 1]
- State transitions are monotonic (during degradation)
- Retry probability decreases with risk

---

## Future Enhancements

### Potential Additions

1. **Latency-based risk scoring**
   - Track P50, P95, P99 latencies
   - Detect latency inflation

2. **Concurrency limits**
   - Per-function semaphores
   - Adaptive concurrency control

3. **Distributed coordination**
   - Share risk scores across instances
   - Cluster-wide quarantine

4. **Machine learning**
   - Anomaly detection
   - Predictive risk modeling

### Non-Goals

- ❌ External dependencies (keep core zero-dependency)
- ❌ Distributed tracing (use hooks to integrate)
- ❌ Metrics storage (use hooks to export)

---

**This architecture prioritizes correctness, performance, and maintainability over feature bloat.**
