# Contributing to evoSentinel

**Author**: Daksha Dubey

First off, thank you for considering contributing to evoSentinel! This document provides guidelines for contributing to this project.

---

## Code of Conduct

Be respectful, professional, and constructive in all interactions.

---

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Python version and OS**
- **Code sample** (if applicable)

**Example**:

```markdown
**Title**: Risk score not decaying after quarantine

**Description**: After a function is quarantined, the risk score remains at 1.0 even after the cooldown period expires.

**Steps to Reproduce**:
1. Create a function that fails 10 times
2. Wait for quarantine cooldown
3. Check risk score

**Expected**: Risk should decay to < 0.95
**Actual**: Risk stays at 1.0

**Environment**:
- Python 3.10
- Ubuntu 22.04
- evoSentinel v0.1.0
```

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:

- **Use case**: Why is this needed?
- **Proposed solution**: How should it work?
- **Alternatives considered**: What other approaches did you think about?

### Pull Requests

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add tests** for new functionality
5. **Update documentation**
6. **Commit**: Use conventional commit messages
7. **Push**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

---

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/evoSentinel.git
cd evoSentinel

# Add upstream remote
git remote add upstream https://github.com/dakshdubey/evoSentinel.git

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Install dev dependencies
pip install pytest pytest-asyncio pytest-cov black mypy
```

---

## Coding Standards

### Python Style

- Follow **PEP 8**
- Use **type hints** for all functions
- Maximum line length: **100 characters**
- Use **descriptive variable names**

### Code Formatting

We use `black` for formatting:

```bash
# Format all files
black evosentinel/

# Check formatting
black --check evosentinel/
```

### Type Checking

We use `mypy` for type checking:

```bash
mypy evosentinel/
```

### Example

```python
from typing import Optional

def calculate_risk(
    func_id: str,
    baseline_risk: float,
    momentum: float
) -> float:
    """
    Calculate risk score for a function.
    
    Args:
        func_id: Unique function identifier
        baseline_risk: Long-term failure rate
        momentum: Recent failure intensity
        
    Returns:
        Risk score between 0.0 and 1.0
    """
    return max(baseline_risk, min(1.0, momentum / 5.0))
```

---

## Testing Requirements

All new features must include tests.

### Test Structure

```
tests/
├── test_core/
│   ├── test_signals.py
│   ├── test_risk_engine.py
│   └── test_decision_engine.py
├── test_modeling/
│   ├── test_ewma.py
│   └── test_decay.py
├── test_state/
│   ├── test_state_machine.py
│   └── test_quarantine.py
└── test_integration/
    └── test_guard_lifecycle.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage (aim for >80%)
pytest --cov=evosentinel --cov-report=html

# Run specific test
pytest tests/test_core/test_risk_engine.py -v
```

### Writing Tests

```python
import pytest
from evosentinel.modeling.decay import EWMA

def test_ewma_initialization():
    """EWMA should initialize with None value."""
    ewma = EWMA(alpha=0.1)
    assert ewma.value is None

def test_ewma_first_update():
    """First update should set value directly."""
    ewma = EWMA(alpha=0.1)
    result = ewma.update(10.0)
    assert result == 10.0
    assert ewma.value == 10.0

def test_ewma_convergence():
    """EWMA should converge to constant input."""
    ewma = EWMA(alpha=0.1)
    for _ in range(100):
        ewma.update(10.0)
    assert abs(ewma.value - 10.0) < 0.01
```

---

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Brief description of what the function does.
    
    Longer description if needed. Explain the algorithm,
    edge cases, or important implementation details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param2 is negative
        
    Example:
        >>> my_function("test", 5)
        True
    """
```

### Updating Documentation

When adding features, update:

- [ ] `README.md` - User-facing documentation
- [ ] `ARCHITECTURE.md` - Technical details
- [ ] `DEVELOPER.md` - Developer guide
- [ ] Inline docstrings
- [ ] Code comments (for complex logic)

---

## Commit Message Guidelines

Use **Conventional Commits**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Maintenance tasks

### Examples

```
feat(risk-engine): add latency-based risk scoring

Implement P95 latency tracking and incorporate into risk
calculation. Risk increases when P95 exceeds 2x average.

Closes #42
```

```
fix(quarantine): correct cooldown duration calculation

Cooldown was not resetting properly after recovery.
Changed to use monotonic time for accuracy.

Fixes #38
```

---

## Performance Guidelines

### Critical Requirements

- **O(1) execution overhead** - No loops in hot path
- **Constant memory** per function - No unbounded growth
- **Thread-safe** - All shared state protected
- **No blocking I/O** - Keep execution fast

### Before Submitting

Run performance benchmarks:

```python
import time
from evosentinel import sentinel

@sentinel.guard("perf.test")
def fast_function():
    return "success"

# Measure overhead
iterations = 10000
start = time.perf_counter()
for _ in range(iterations):
    fast_function()
end = time.perf_counter()

overhead_per_call = (end - start) / iterations
print(f"Overhead: {overhead_per_call * 1000:.3f} ms")

# Should be < 1ms per call
assert overhead_per_call < 0.001
```

---

## Review Process

### What We Look For

✅ **Correctness**: Does it work as intended?  
✅ **Tests**: Are there comprehensive tests?  
✅ **Performance**: Does it meet performance requirements?  
✅ **Documentation**: Is it well-documented?  
✅ **Style**: Does it follow coding standards?  
✅ **Backwards compatibility**: Does it break existing APIs?

### Review Timeline

- Initial review: Within 3 days
- Follow-up: Within 1 day of updates
- Merge: After approval from maintainer

---

## Release Process

Maintainers will handle releases, but here's the process:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag -a v0.2.0 -m "Release v0.2.0"`
4. Build: `python -m build`
5. Upload to PyPI: `twine upload dist/*`

---

## Questions?

- **Issues**: https://github.com/dakshdubey/evoSentinel/issues
- **Discussions**: https://github.com/dakshdubey/evoSentinel/discussions
- **Email**: Contact Daksha Dubey

---

## Recognition

Contributors will be recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- Project README

---

**Thank you for contributing to evoSentinel!** 🎉

**Author**: Daksha Dubey
