# Desert Brew Finance Service

**Version:** 0.2.0  
**Port:** 8005  
**Purpose:** Transfer Pricing, Income/Expense Tracking & Balance Sheet

---

## 📋 Overview

Finance Service handles the financial backbone of Desert Brew:
1. **Transfer Pricing** — Factory sells to Taproom at cost + margin (P&L segregation)
2. **Income Tracking** — Notas de venta pagadas, ventas en efectivo, B2B
3. **Expense Tracking** — Proveedores, nóminas, servicios, compras
4. **Balance General** — Ingresos vs egresos con desglose por categoría y profit center
5. **Cashflow** — Flujo de efectivo mensual

---

## 🔌 API Endpoints (19)

### Transfer Pricing (5)

| # | Method | Endpoint | Descripción |
|---|--------|----------|-------------|
| 1 | GET | `/pricing-rules` | Reglas de pricing activas |
| 2 | POST | `/calculate-transfer-price` | Calcular precio de transferencia |
| 3 | POST | `/internal-transfers` | Crear transfer Factory→Taproom |
| 4 | GET | `/internal-transfers` | Listar transfers (filtros) |
| 5 | GET | `/profit-center/{pc}/summary` | P&L por profit center |

### Income (6)

| # | Method | Endpoint | Descripción |
|---|--------|----------|-------------|
| 6 | POST | `/incomes` | Registrar ingreso |
| 7 | GET | `/incomes` | Listar (tipo, categoría, profit center, método pago, días) |
| 8 | GET | `/incomes/summary` | Resumen por período/categoría |
| 9 | GET | `/incomes/{id}` | Detalle |
| 10 | PATCH | `/incomes/{id}` | Actualizar |
| 11 | DELETE | `/incomes/{id}` | Eliminar |

**Income Types:** `sales_note`, `cash_sale`, `b2b_invoice`, `other`  
**Categories:** `beer_sales`, `merch_sales`, `food_sales`, `event`, `other`

### Expenses (6)

| # | Method | Endpoint | Descripción |
|---|--------|----------|-------------|
| 12 | POST | `/expenses` | Registrar egreso |
| 13 | GET | `/expenses` | Listar (tipo, categoría, profit center, proveedor, días) |
| 14 | GET | `/expenses/summary` | Resumen por período/categoría |
| 15 | GET | `/expenses/{id}` | Detalle |
| 16 | PATCH | `/expenses/{id}` | Actualizar |
| 17 | DELETE | `/expenses/{id}` | Eliminar |

**Expense Types:** `supplier_payment`, `payroll`, `purchase`, `utility`, `rent`, `tax`, `maintenance`, `other`  
**Categories:** `raw_materials`, `packaging`, `payroll`, `energy`, `water`, `gas`, `rent`, `maintenance`, `transport`, `marketing`, `communications`, `taxes`, `other`

### Balance & Cashflow (2)

| # | Method | Endpoint | Descripción |
|---|--------|----------|-------------|
| 18 | GET | `/balance` | Balance general: ingresos vs egresos |
| 19 | GET | `/cashflow` | Flujo de efectivo mensual |

**Balance Response:**
```json
{
  "total_income": 85000.00,
  "total_expenses": 57900.00,
  "net_profit": 27100.00,
  "profit_margin_percentage": 31.88,
  "income_by_category": {"beer_sales": 72000, "merch_sales": 13000},
  "expenses_by_category": {"raw_materials": 15000, "payroll": 25000, "energy": 8000, ...},
  "income_by_profit_center": {"taproom": 85000},
  "expenses_by_profit_center": {"factory": 32900, "general": 25000}
}
```

---

## 🏗️ Models (4)

| Model | Registros | Propósito |
|-------|-----------|-----------|
| `TransferPricingRule` | HOUSE +15%, GUEST 0%, MERCH +25% | Reglas de pricing |
| `InternalTransfer` | Factory→Taproom Shadow Ledger | P&L segregation |
| `Income` | Notas pagadas, ventas directas | Revenue tracking |
| `Expense` | Proveedores, nómina, servicios | Cost tracking |

---

## 🧪 Testing

```bash
cd services/finance_service
pip install -r requirements-test.txt
pytest tests/ -v
```

**40 tests, 0.98s:**
- Transfer pricing: 12 (5 integration + 7 unit)
- Income: 8
- Expense: 8
- Balance/Cashflow: 4
- Internal transfer model: 8

---

## 📂 File Structure

```
finance_service/
├── main.py                          # v0.2.0
├── database.py
├── api/
│   ├── finance_routes.py            # Pricing + Transfers + Balance (7)
│   ├── income_routes.py             # Income CRUD + summary (6)
│   └── expense_routes.py            # Expense CRUD + summary (6)
├── models/
│   ├── transfer_pricing_rule.py
│   ├── internal_transfer.py
│   ├── income.py                    # NEW
│   └── expense.py                   # NEW
├── schemas/
│   ├── finance.py                   # Transfer pricing schemas
│   └── cashflow.py                  # Income/Expense/Balance schemas (NEW)
├── logic/
│   ├── transfer_pricing_engine.py
│   └── balance_calculator.py        # NEW
└── tests/
    ├── conftest.py
    ├── integration/
    │   ├── test_finance_api.py
    │   ├── test_income_api.py       # NEW
    │   ├── test_expense_api.py      # NEW
    │   └── test_balance.py          # NEW
    └── unit/
        ├── test_internal_transfer.py
        └── test_transfer_pricing_engine.py
```
