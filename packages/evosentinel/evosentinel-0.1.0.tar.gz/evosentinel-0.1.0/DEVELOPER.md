# Developer Documentation

**Author**: Daksha Dubey

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Project Architecture](#project-architecture)
4. [Code Style Guidelines](#code-style-guidelines)
5. [Testing](#testing)
6. [Adding New Features](#adding-new-features)
7. [Performance Considerations](#performance-considerations)
8. [Debugging](#debugging)
9. [Release Process](#release-process)

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment tool (venv, virtualenv, or conda)

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/dakshdubey/evoSentinel.git
cd evoSentinel

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies (optional)
pip install pytest pytest-asyncio pytest-cov black mypy
```

---

## Development Setup

### Project Structure

```
evoSentinel/
├── evosentinel/           # Main package
│   ├── core/             # Core engines (signals, risk, decision)
│   ├── modeling/         # Statistical algorithms (EWMA, decay)
│   ├── state/            # State machine and quarantine
│   ├── execution/        # Guard and retry logic
│   ├── hooks/            # Observability hooks
│   ├── api.py            # Public API
│   └── errors.py         # Custom exceptions
├── tests/                # Test suite (to be created)
├── docs/                 # Additional documentation
├── demo.py               # Interactive demo
├── test_sdk.py          # Verification script
└── pyproject.toml       # Package configuration
```

### Running the Demo

```bash
python demo.py
```

This simulates a service that transitions through different health states.

---

## Project Architecture

### Core Design Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **No Global Mutable State**: All state is scoped and protected
3. **Time-Based Algorithms**: Use decay functions instead of counters
4. **Probabilistic Decisions**: Avoid hard thresholds

### Data Flow

```
User Function Call
    ↓
[Execution Guard]
    ↓
Pre-execution Check → Risk Engine → Decision Engine
    ↓
Execute Function (if allowed)
    ↓
Post-execution → Signal Capture → Update Models → State Machine
    ↓
Trigger Hooks
```

### Key Components

#### 1. Signal Capture Layer (`core/signals.py`)

**Purpose**: Observe execution without making decisions

```python
@dataclass(frozen=True)
class ExecutionSignal:
    function_id: str
    execution_time: float
    exception: Optional[Exception] = None
    timestamp: float = field(default_factory=lambda: time.monotonic())
```

**When to modify**: Adding new signal types (e.g., memory usage, CPU time)

#### 2. Behavioral Modeling (`modeling/`)

**Purpose**: Build statistical profiles of function behavior

**Key Algorithms**:
- EWMA for latency tracking
- Exponential decay for momentum
- Variance analysis for jitter

**When to modify**: Improving baseline accuracy, adding new metrics

#### 3. Risk Engine (`core/risk_engine.py`)

**Purpose**: Compute continuous risk scores (0.0 - 1.0)

**Formula**:
```python
risk = max(baseline.failure_rate, momentum / sensitivity)
```

**When to modify**: Adding new risk factors (latency, concurrency)

#### 4. Decision Engine (`core/decision_engine.py`)

**Purpose**: Convert risk scores into actions

**States**:
- `ALLOW`: risk < 0.5
- `THROTTLE`: 0.5 ≤ risk < 0.8
- `BLOCK`: risk ≥ 0.8

**When to modify**: Changing thresholds, adding new decision types

#### 5. State Machine (`state/state_machine.py`)

**Purpose**: Track function health

**States**:
- `HEALTHY`: risk < 0.4
- `DEGRADED`: 0.4 ≤ risk < 0.8
- `CRITICAL`: 0.8 ≤ risk < 0.95
- `QUARANTINED`: risk ≥ 0.95

**When to modify**: Adding new states, changing transition logic

---

## Code Style Guidelines

### Python Style

Follow PEP 8 with these specifics:

```python
# Good: Clear, descriptive names
def calculate_risk_score(func_id: str) -> float:
    baseline = self.get_baseline(func_id)
    return baseline.failure_rate

# Bad: Unclear abbreviations
def calc_rs(fid: str) -> float:
    bl = self.get_bl(fid)
    return bl.fr
```

### Type Hints

Always use type hints:

```python
# Good
def update_metrics(self, latency: float, is_failure: bool) -> None:
    ...

# Bad
def update_metrics(self, latency, is_failure):
    ...
```

### Docstrings

Use docstrings for public APIs:

```python
class RiskEngine:
    """
    Computes continuous risk scores for guarded functions.
    
    Risk is calculated from:
    - Baseline failure rate (EWMA)
    - Recent failure momentum (decay signal)
    """
    
    def calculate_risk(self, func_id: str) -> float:
        """
        Calculate current risk score for a function.
        
        Args:
            func_id: Unique identifier for the function
            
        Returns:
            Risk score between 0.0 and 1.0
        """
```

### Comments

Comment **why**, not **what**:

```python
# Good: Explains reasoning
if momentum < 0.1:
    baseline.decay(0.98)  # Allow healing when no recent failures

# Bad: States the obvious
if momentum < 0.1:
    baseline.decay(0.98)  # Call decay with 0.98
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=evosentinel --cov-report=html

# Run specific test file
pytest tests/test_risk_engine.py
```

### Writing Tests

#### Unit Tests

Test individual components in isolation:

```python
def test_ewma_convergence():
    ewma = EWMA(alpha=0.1)
    
    # Feed constant values
    for _ in range(100):
        ewma.update(10.0)
    
    # Should converge to the constant
    assert abs(ewma.value - 10.0) < 0.01
```

#### Integration Tests

Test component interactions:

```python
def test_guard_lifecycle():
    sentinel = Sentinel()
    
    @sentinel.guard("test.func")
    def unstable_func():
        raise Exception("Simulated failure")
    
    # Should eventually quarantine
    for _ in range(10):
        try:
            unstable_func()
        except:
            pass
    
    # Verify state
    state = sentinel.state_machine.get_state("test.func")
    assert state in [HealthState.CRITICAL, HealthState.QUARANTINED]
```

#### Async Tests

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_guard():
    sentinel = Sentinel()
    
    @sentinel.guard("async.func")
    async def async_func():
        await asyncio.sleep(0.1)
        return "success"
    
    result = await async_func()
    assert result == "success"
```

---

## Adding New Features

### Example: Adding Latency-Based Risk

1. **Update Signal Capture** (if needed):
```python
# core/signals.py - already captures execution_time
```

2. **Update Baseline**:
```python
# modeling/baseline.py
def update_metrics(self, latency: float, is_failure: bool):
    # ... existing code ...
    
    # Add latency percentile tracking
    self.latency_p95_ewma.update(latency)
```

3. **Update Risk Engine**:
```python
# core/risk_engine.py
def calculate_risk(self, func_id: str) -> float:
    baseline = self.get_baseline(func_id)
    
    # Existing risk factors
    failure_risk = baseline.failure_rate
    momentum_risk = min(1.0, momentum / 5.0)
    
    # New: Latency inflation risk
    if baseline.avg_latency > 0:
        latency_inflation = baseline.latency_p95 / baseline.avg_latency
        latency_risk = min(1.0, (latency_inflation - 1.0) / 2.0)
    else:
        latency_risk = 0.0
    
    return max(failure_risk, momentum_risk, latency_risk)
```

4. **Add Tests**:
```python
# tests/test_latency_risk.py
def test_latency_inflation_increases_risk():
    engine = RiskEngine()
    
    # Simulate slow executions
    for _ in range(10):
        signal = ExecutionSignal("test", execution_time=5.0)
        engine.record_signal(signal)
    
    risk = engine.calculate_risk("test")
    assert risk > 0.3  # Should detect latency issue
```

---

## Performance Considerations

### Critical Paths

The execution guard is on the **hot path** for every guarded function call. Keep it fast:

- ✅ O(1) operations only
- ✅ Minimal allocations
- ✅ No I/O in critical sections
- ❌ No loops over unbounded collections
- ❌ No blocking calls

### Memory Management

Each guarded function maintains:
- ~96 bytes of state
- No unbounded growth

**Bad Example**:
```python
# Don't store all signals
self.all_signals = []  # Unbounded!
self.all_signals.append(signal)
```

**Good Example**:
```python
# Use EWMA instead
self.failure_rate_ewma.update(1.0 if is_failure else 0.0)
```

### Profiling

```bash
# Profile the demo
python -m cProfile -o profile.stats demo.py

# Analyze results
python -m pstats profile.stats
> sort cumulative
> stats 20
```

---

## Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Attach debug hooks
@sentinel.on_risk_change
def debug_risk(func_id, risk):
    logging.debug(f"[{func_id}] Risk: {risk:.4f}")

@sentinel.on_state_transition
def debug_state(func_id, old, new):
    logging.debug(f"[{func_id}] {old} → {new}")
```

### Common Issues

#### Issue: Function never recovers from quarantine

**Cause**: Risk not decaying fast enough

**Solution**: Increase decay rate or reduce quarantine threshold
```python
sentinel = Sentinel(
    risk_decay=0.85,  # Faster decay
    quarantine_threshold=0.98  # Higher threshold
)
```

#### Issue: Too many false positives

**Cause**: Thresholds too aggressive

**Solution**: Increase max_risk
```python
sentinel = Sentinel(max_risk=0.90)
```

---

## Release Process

### Version Bumping

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` (create if needed)
3. Tag the release:
```bash
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

### Building for PyPI

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# Check the build
twine check dist/*

# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

### Pre-release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version bumped
- [ ] CHANGELOG updated
- [ ] Demo runs successfully
- [ ] No performance regressions

---

## Contributing Guidelines

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Add tests
5. Ensure all tests pass
6. Update documentation
7. Submit PR with clear description

### Commit Messages

Follow conventional commits:

```
feat: add latency-based risk scoring
fix: correct EWMA initialization bug
docs: update developer guide
test: add concurrency stress tests
perf: optimize risk calculation
```

---

## Questions?

**Author**: Daksha Dubey  
**Repository**: https://github.com/dakshdubey/evoSentinel  
**Issues**: https://github.com/dakshdubey/evoSentinel/issues

---

**Happy coding! 🚀**
