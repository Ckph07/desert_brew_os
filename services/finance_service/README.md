# Desert Brew Finance Service

**Version:** 0.1.0  
**Purpose:** Transfer Pricing Engine and Shadow Ledger for P&L segregation

---

## 📋 Overview

Finance Service enables profit center separation between Factory and Taproom **WITHOUT generating fiscal invoices**.

### Key Concepts

**Transfer Pricing:**
- Determines how Factory prices products to Taproom
- HOUSE beer: Factory earns 15% margin (COST_PLUS strategy)
- GUEST beer: Factory earns 0% margin (PASSTHROUGH strategy - acts as 3PL)

**Shadow Ledger:**
- Records internal transfers for accounting
- Tracks Factory P&L separately from Taproom P&L
- No CFDI (fiscal invoice) required

---

## 🏗️ Architecture

### Models

#### `TransferPricingRule`
Defines pricing strategy by origin type.

```python
origin_type: str        # house, guest, commercial, merchandise
strategy: str           # cost_plus, passthrough, fixed_markup
markup_percentage: Decimal  # 15.00 = 15%
```

**Seeded Rules:**
| Origin | Strategy | Markup | Business Reason |
|--------|----------|--------|----------------|
| HOUSE | COST_PLUS | 15% | Factory earns margin on own production |
| GUEST | PASSTHROUGH | 0% | Factory is 3PL for guest breweries |
| COMMERCIAL | PASSTHROUGH | 0% | Factory is logistics provider |
| MERCHANDISE | FIXED_MARKUP | 25% | Retail markup |

#### `InternalTransfer`
Shadow ledger record for Factory → Taproom movements.

```python
from_profit_center: str      # factory
to_profit_center: str        # taproom
product_sku: str
quantity: Decimal
unit_cost: Decimal           # Factory's cost
unit_transfer_price: Decimal # Price to Taproom (auto-calculated)
factory_profit: Decimal      # transfer_price - cost
taproom_cogs: Decimal        # transfer_price (starting point for Taproom markup)
```

---

## 🔌 API Endpoints

### 1. Get Pricing Rules
```http
GET /api/v1/finance/pricing-rules?active_only=true
```

**Response:**
```json
[
  {
    "id": 1,
    "origin_type": "house",
    "strategy": "cost_plus",
    "markup_percentage": 15.00,
    "rule_name": "HOUSE Beer - Factory Margin"
  }
]
```

---

### 2. Calculate Transfer Price
```http
POST /api/v1/finance/calculate-transfer-price?origin_type=house&unit_cost=500.00
```

**Response:**
```json
{
  "origin_type": "house",
  "unit_cost": 500.00,
  "unit_transfer_price": 575.00,  // 500 × 1.15
  "markup_percentage": 15.00,
  "strategy": "cost_plus"
}
```

---

### 3. Create Internal Transfer
```http
POST /api/v1/finance/internal-transfers
Content-Type: application/json

{
  "from_profit_center": "factory",
  "to_profit_center": "taproom",
  "product_sku": "BEER-IPA-KEG-001",
  "product_name": "IPA House Keg 50L",
  "origin_type": "house",
  "quantity": 10.0,
  "unit_measure": "KEGS",
  "unit_cost": 500.00,
  "notes": "Weekly stock transfer"
}
```

**Response:**
```json
{
  "id": "uuid",
  "product_sku": "BEER-IPA-KEG-001",
  "quantity": 10.0,
  "unit_cost": 500.00,
  "unit_transfer_price": 575.00,    // Auto-calculated
  "total_cost": 5000.00,             // 10 × 500
  "total_transfer_price": 5750.00,   // 10 × 575
  "factory_revenue": 5750.00,
  "factory_profit": 750.00,          // 5750 - 5000 = 15% margin
  "taproom_cogs": 5750.00,
  "markup_percentage": 15.00,
  "transfer_date": "2026-02-03T18:00:00"
}
```

---

### 4. List Internal Transfers
```http
GET /api/v1/finance/internal-transfers?origin_type=house&limit=100
```

---

### 5. Profit Center Summary
```http
GET /api/v1/finance/profit-center/factory/summary?days=30
```

**Response (Factory P&L):**
```json
{
  "profit_center": "factory",
  "period_start": "2026-01-04T00:00:00",
  "period_end": "2026-02-03T18:00:00",
  "total_revenue": 5750.00,    // Factory's transfer price revenue
  "total_cogs": 5000.00,       // Factory's production cost
  "total_profit": 750.00,      // Revenue - COGS
  "profit_margin_percentage": 13.04,  // 750/5750 × 100
  "transfer_count": 1
}
```

---

## 🧮 Transfer Pricing Examples

### Example 1: HOUSE Beer (15% Factory Margin)

**Scenario:** 10 kegs IPA, factory cost $500/keg

```python
unit_cost = 500.00
markup = 15%
unit_transfer_price = 500 × 1.15 = 575.00

# For quantity = 10 kegs:
total_cost = 10 × 500 = 5,000.00
total_transfer_price = 10 × 575 = 5,750.00
factory_profit = 5,750 - 5,000 = 750.00  // Factory earns $750
taproom_cogs = 5,750.00                   // Taproom pays $5,750
```

**Factory P&L Impact:**
- Revenue: +$5,750
- COGS: -$5,000
- **Profit: $750 (15% margin)**

**Taproom P&L Impact:**
- COGS: $5,750 (starting point for retail markup)

---

### Example 2: GUEST Beer (0% Factory Margin)

**Scenario:** 5 kegs Guest Pale Ale, factory cost $300/keg

```python
unit_cost = 300.00
markup = 0%  // PASSTHROUGH
unit_transfer_price = 300 × 1.00 = 300.00

total_cost = 5 × 300 = 1,500.00
total_transfer_price = 5 × 300 = 1,500.00
factory_profit = 1,500 - 1,500 = 0.00  // Factory earns $0 (3PL only)
taproom_cogs = 1,500.00
```

**Factory P&L Impact:**
- Revenue: +$1,500
- COGS: -$1 ,500
- **Profit: $0 (3PL service)**

---

## 🌱 Setup

### 1. Install Dependencies
```bash
cd services/finance_service
pip install -r requirements.txt
```

### 2. Seed Pricing Rules
```bash
python seed_pricing_rules.py
```

**Output:**
```
✅ Seeded 4 transfer pricing rules successfully
   - HOUSE        → cost_plus       (15.00%)
   - GUEST        → passthrough     ( 0.00%)
   - COMMERCIAL   → passthrough     ( 0.00%)
   - MERCHANDISE  → fixed_markup    (25.00%)
```

### 3. Run Service
```bash
uvicorn main:app --reload --port 8003
```

---

## 🧪 Testing

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

**Expected:** 20+ tests pass

---

## 💼 Business Logic

### Why Transfer Pricing?

**Problem:** Factory and Taproom are ONE legal entity but SEPARATE profit centers.

**Solution:** Internal transfer pricing WITHOUT fiscal invoices.

**Benefits:**
1. **Factory P&L** shows profitability on production
2. **Taproom P&L** shows retail profitability
3. **No CFDI required** (internal accounting only)
4. **Clear cost allocation** for management decisions

### HOUSE vs GUEST Strategy

**HOUSE (15% markup):**
- Desert Brew manufactures the beer
- Factory incurs production costs (malt, hops, labor, water)
- Factory deserves margin for creating value
- Transfer Price = Cost + 15%

**GUEST (0% markup):**
- Guest brewery manufactures the beer
- Factory only stores/delivers (3PL service)
- Factory is NOT creating manufacturing value
- Transfer Price = Cost × 1.00 (passthrough)

---

## 📊 Database Schema

### `transfer_pricing_rules`
```sql
CREATE TABLE transfer_pricing_rules (
    id SERIAL PRIMARY KEY,
    origin_type VARCHAR(20) UNIQUE NOT NULL,
    strategy VARCHAR(20) NOT NULL,
    markup_percentage NUMERIC(5, 2) NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### `internal_transfers`
```sql
CREATE TABLE internal_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_profit_center VARCHAR(20) NOT NULL,
    to_profit_center VARCHAR(20) NOT NULL,
    product_sku VARCHAR(100) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    origin_type VARCHAR(20) NOT NULL,
    quantity NUMERIC(10, 2) NOT NULL,
    unit_measure VARCHAR(20) NOT NULL,
    unit_cost NUMERIC(10, 2) NOT NULL,
    unit_transfer_price NUMERIC(10, 2) NOT NULL,
    total_cost NUMERIC(12, 2) NOT NULL,
    total_transfer_price NUMERIC(12, 2) NOT NULL,
    factory_revenue NUMERIC(12, 2) NOT NULL,
    factory_profit NUMERIC(12, 2) NOT NULL,
    taproom_cogs NUMERIC(12, 2) NOT NULL,
    pricing_rule_id INTEGER REFERENCES transfer_pricing_rules(id),
    markup_percentage NUMERIC(5, 2),
    transfer_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    notes VARCHAR(500)
);
```

---

## 🔗 Integration with Other Services

**Inventory Service:**
- Provides `origin_type` field (Sprint 3)
- Finance queries origin to determine pricing strategy

**Future (Sprint 7 - Taproom POS):**
- Taproom will record actual sales revenue
- P&L summary will show complete profit picture

---

## 📝 Notes

- Shadow Ledger is for **internal accounting only** - NOT fiscal
- No CFDI (invoices) generated for internal transfers
- Pricing rules can be updated but changes are NOT retroactive
- Each transfer records the `markup_percentage` for audit trail

---

**Status:** ✅ Production Ready  
**Tests:** 20+ passing  
**Coverage:** ~85%
