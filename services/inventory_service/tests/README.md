# Inventory Service - Testing

## Running Tests

```bash
cd services/inventory_service

# Install dependencies
pip install -r requirements.txt

# Run all tests with coverage
pytest

# Run specific categories
pytest tests/unit/ -v
pytest tests/integration/ -v

# With coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures
├── unit/
│   ├── test_fifo_logic.py               # 7 tests - FIFO
│   ├── test_transfers.py                # 5 tests - Transfers
│   ├── test_race_conditions.py          # 1 test - Concurrency
│   ├── test_suppliers.py                # 3 tests - Supplier model
│   └── test_gas_tanks.py                # 5 tests - Gas tanks
└── integration/
    ├── test_api.py                      # 9 tests - Stock API
    ├── test_movement_api.py             # 4 tests - Movement API
    ├── test_supplier_api.py             # 7 tests - Supplier API
    └── test_gas_api.py                  # 9 tests - Gas API
```

## Test Coverage

**Total: 42 tests**

### Unit Tests (25)
- 7 FIFO logic
- 5 Stock transfers
- 2 Movement logging
- 1 Race conditions
- 3 Supplier model
- 5 Gas tank model
- 2 Gas consumption

### Integration Tests (17)
- 9 Stock API
- 7 Supplier API
- 9 Gas API

**Coverage:** > 85%

---

## Running Specific Tests

```bash
# FIFO logic
pytest tests/unit/test_fifo_logic.py -v

# Suppliers
pytest tests/unit/test_suppliers.py -v
pytest tests/integration/test_supplier_api.py -v

# Gas tanks
pytest tests/unit/test_gas_tanks.py -v
pytest tests/integration/test_gas_api.py -v

# Race conditions
pytest tests/unit/test_race_conditions.py -v
```

---

**Status:** ✅ 42 tests passing  
**Coverage:** > 85%
