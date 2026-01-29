---
this_file: TESTING.md
---
# Testing Guide

## Running Tests

### Unit Tests
Run the standard test suite:
```bash
python -m pytest
```

With coverage report:
```bash
python -m pytest --cov=. --cov-report=term-missing
```

### Integration Tests
Integration tests make real API calls and are skipped by default to avoid CI complications.

To run integration tests locally:
```bash
export ABERSETZ_INTEGRATION_TESTS=true
python -m pytest tests/test_integration.py -v
```

Some tests require API keys:
```bash
export SILICONFLOW_API_KEY=your-api-key
export ABERSETZ_INTEGRATION_TESTS=true
python -m pytest tests/test_integration.py -v
```

### Test Markers
- `@pytest.mark.integration` - Tests requiring network access
- `@pytest.mark.skipif` - Conditional test execution

### Continuous Testing
Use pytest-watch for automatic test runs:
```bash
uvx pytest-watch -- -xvs
```

## Test Coverage
Current coverage: **91%**

Coverage by module:
- Configuration management: 90%
- Translation pipeline: 97%
- CLI interface: 78%
- Engine abstractions: 82%

## Testing Best Practices
1. Write tests first (TDD)
2. Test edge cases: empty inputs, None values, large inputs
3. Mock external services in unit tests
4. Use integration tests sparingly for API validation
5. Keep tests focused and independent
6. Use descriptive test names: `test_function_when_condition_then_result`