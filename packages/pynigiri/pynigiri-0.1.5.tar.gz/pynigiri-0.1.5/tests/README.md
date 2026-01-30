# PyNigiri Tests

This directory contains unit tests for the PyNigiri Python bindings.

## Running Tests

Install test dependencies:
```bash
pip install pytest pytest-cov
```

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=pynigiri --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_types.py
```

Run with verbose output:
```bash
pytest -v
```

## Test Structure

- `test_types.py`: Tests for basic types and data structures
- `test_loader.py`: Tests for data loading functionality
- `test_routing.py`: Tests for routing functionality
- `test_rt.py`: Tests for real-time update functionality

## Integration Tests

Some tests require actual GTFS data to run. These are commented out in the test files but can be enabled if you have test data available. To use them:

1. Place test GTFS data in a `test_data/` directory
2. Uncomment the relevant test functions
3. Update paths to point to your test data

## Writing Tests

When adding new functionality to PyNigiri, please add corresponding tests following the existing patterns.
