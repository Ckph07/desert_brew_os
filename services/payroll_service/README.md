# Desert Brew Payroll Service v0.1.0

Employee & Payroll Management for Desert Brew Co.

**Port:** 8006

## Business Context

### Cervecería (Brewery) — 3 Fixed Employees
- Standard weekly/biweekly payroll
- Roles: BREWMASTER, ASSISTANT_BREWER, PACKAGING_OPERATOR
- `employment_type = FIXED`, `monthly_salary = daily × 30`

### Taproom — 3 Fixed + Rotating Temps
- Fixed: weekly payroll with tips + taxi
- Temps: daily pay (`TEMPORARY`), no monthly salary, no benefits
- **Weekly Tip Pool** (Sun-Sat): Total tips ÷ participating members equally
- **Taxi support:** Flat allowance per shift for late-night staff
- Both fixed and temp staff participate in tip pool

## API Endpoints (11 total)

### Employees (4)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/payroll/employees` | Create (FIXED/TEMPORARY) |
| GET | `/api/v1/payroll/employees` | List (filters: dept, role, type) |
| GET | `/api/v1/payroll/employees/{id}` | Get employee |
| PATCH | `/api/v1/payroll/employees/{id}` | Update |

### Payroll Entries (4)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/payroll/entries` | Create entry (auto-calculates totals) |
| GET | `/api/v1/payroll/entries` | List (filters: employee, status, dept) |
| GET | `/api/v1/payroll/entries/{id}` | Get entry |
| PATCH | `/api/v1/payroll/entries/{id}/pay` | Mark as paid |

### Tip Pools (3)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/payroll/tip-pools` | Create weekly distribution |
| GET | `/api/v1/payroll/tip-pools` | List distributions |
| GET | `/api/v1/payroll/tip-pools/{id}` | Get distribution |

## Payroll Calculation

```
base_salary     = daily_salary × days_worked
overtime_amount = overtime_hours × overtime_rate
taxi_total      = taxi_shifts × taxi_allowance_per_shift
total_payment   = base + overtime + tips_share + taxi + bonuses - deductions
```

## Running

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8006
```

## Testing

```bash
pip install pytest httpx
python -m pytest tests/ -v
# 21 tests, ~0.4s
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql://...localhost:5432/desertbrew_payroll | PostgreSQL |
