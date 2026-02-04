# Desert Brew Production Service

**Version:** 0.1.0  
**Purpose:** Manufacturing Execution System (MES) with BeerSmith integration

---

## 📋 Overview

Production Service tracks brewery production from recipe to finished product:
1. **Import recipes** from BeerSmith (.bsmx files)
2. **Track batches** through 6-state lifecycle
3. **Allocate costs** via FIFO from raw materials
4. **Link to Finance** for transfer pricing

---

## 🏗️ Architecture

### Models (3)

#### `Recipe`
BeerSmith recipe data (parsed from .bsmx XML).

```python
name: str
batch_size_liters: Decimal
fermentables: JSON  # [{"name": "Maris Otter", "amount_kg": 5.0}]
hops: JSON          # [{"name": "Cascade", "amount_g": 50.0, "time_min": 60}]
yeast: JSON         # [{"name": "US-05", "lab": "Fermentis"}]
expected_og/fg/abv: Decimal
```

#### `ProductionBatch` (6-state FSM)
Batch lifecycle tracking.

**States:**
```
PLANNED → BREWING → FERMENTING → CONDITIONING → PACKAGING → COMPLETED
            ↓           ↓               ↓
        CANCELLED   CANCELLED       CANCELLED
```

**Cost fields:**
```python
total_cost: Decimal          # FIFO allocated
malt_cost: Decimal
hops_cost: Decimal
yeast_cost: Decimal
water_cost: Decimal
labor_cost: Decimal
overhead_cost: Decimal
cost_per_liter: Decimal
```

#### `BatchIngredientAllocation`
FIFO cost tracing (links to StockBatch from Sprint 1).

```python
production_batch_id: int
stock_batch_id: int          # FK to inventory_service.stock_batches
ingredient_name: str
quantity_consumed: Decimal
unit_cost: Decimal           # From StockBatch
total_cost: Decimal
```

---

## 🔌 API Endpoints (12)

### Recipes (4)

**1. Import BeerSmith Recipe**
```http
POST /api/v1/production/recipes/import
Content-Type: multipart/form-data

file: sample_ipa.bsmx
```

**Response:**
```json
{
  "id": 1,
  "name": "American IPA",
  "batch_size_liters": 20.0,
  "fermentables": [{"name": "Maris Otter", "amount_kg": 5.0}],
  "hops": [{"name": "Cascade", "amount_g": 50.0, "time_min": 60}],
  "yeast": [{"name": "US-05"}],
  "expected_og": 1.065,
  "expected_abv": 6.96
}
```

**2-4. List/Get/Delete Recipes**
```http
GET /api/v1/production/recipes
GET /api/v1/production/recipes/{id}
DELETE /api/v1/production/recipes/{id}
```

---

### Production Batches (6)

**5. Create Batch (PLANNED)**
```http
POST /api/v1/production/batches
Content-Type: application/json

{
  "recipe_id": 1,
  "batch_number": "IPA-2026-001",
  "planned_volume_liters": 20.0,
  "notes": "First batch of the year"
}
```

**6. List Batches**
```http
GET /api/v1/production/batches?status=brewing
```

**7. Get Batch Details**
```http
GET /api/v1/production/batches/{id}
```

**8. Start Brewing (PLANNED → BREWING)**
```http
PATCH /api/v1/production/batches/{id}/start-brewing
```

**Effect:**
- Status → BREWING
- Timestamp: `brewing_started_at`
- **Costs allocated via FIFO** (CostAllocator runs automatically)

**Response:**
```json
{
  "batch_id": 1,
  "batch_number": "IPA-2026-001",
  "previous_status": "planned",
  "new_status": "brewing",
  "message": "Batch started brewing. Total cost allocated: $500.00"
}
```

**9. Start Fermenting (BREWING → FERMENTING)**
```http
PATCH /api/v1/production/batches/{id}/start-fermenting
```

**10. Complete Batch (→ COMPLETED)**
```http
PATCH /api/v1/production/batches/{id}/complete
Content-Type: application/json

{
  "actual_volume_liters": 19.5,
  "actual_og": 1.064,
  "actual_fg": 1.011
}
```

**Effect:**
- Status → COMPLETED
- `cost_per_liter` recalculated with actual volume
- ABV calculated: `(OG - FG) × 131.25`
- TODO Sprint 4.5: Create FinishedProductInventory
- TODO Sprint 4.5: Create InternalTransfer (Factory → Taproom)

---

### Cost Allocation (2)

**11. Get Cost Breakdown**
```http
GET /api/v1/production/batches/{id}/cost-breakdown
```

**Response:**
```json
{
  "batch_id": 1,
  "batch_number": "IPA-2026-001",
  "total_cost": 500.00,
  "cost_per_liter": 25.64,
  "breakdown": {
    "malt": 200.00,
    "hops": 75.00,
    "yeast": 15.00,
    "water": 50.00,
    "labor": 50.00,
    "overhead": 30.00
  },
  "allocations": [
    {
      "ingredient": "Maris Otter",
      "quantity": 5.0,
      "unit": "KG",
      "unit_cost": 15.00,
      "total_cost": 75.00,
      "stock_batch": "MOCK-BATCH-001"
    }
  ]
}
```

---

## 🧮 Business Logic

### BeerSmith Parser

**Supported:** BeerSmith 3 .bsmx XML format

**Parses:**
- Recipe metadata (name, style, batch size)
- Fermentables (malts) → JSON array
- Hops (boil + dry hop) → JSON array (converts kg → grams)
- Yeast → JSON array
- Calculated values (OG, FG, ABV, IBU, color)

**Example XML:**
```xml
<Recipes>
  <Recipe>
    <F_R_NAME>American IPA</F_R_NAME>
    <F_R_BATCH_SIZE>20.0</F_R_BATCH_SIZE>
    <Grain>
      <F_G_NAME>Maris Otter</F_G_NAME>
      <F_G_AMOUNT>5.0</F_G_AMOUNT>
    </Grain>
  </Recipe>
</Recipes>
```

---

### Cost Allocation (FIFO)

**Sprint 4 Status:** Mock implementation  
**Sprint 4.5 Plan:** Real FIFO integration with Inventory Service StockBatch

**Current Logic:**
```python
# Mock allocation (Sprint 4)
malt_cost = required_kg × $15/kg (fixed)
hops_cost = required_g × $0.03/g (fixed)
yeast_cost = $15/packet (fixed)
water_cost = batch_liters × 1.5 × $0.50/L (placeholder)
labor_cost = $50/batch (fixed)
overhead_cost = $30/batch (fixed)
```

**Sprint 4.5 Real FIFO:**
```python
# Real FIFO (planned)
1. Query StockBatch for ingredient (e.g., "Maris Otter")
2. Order by created_at ASC (oldest first)
3. Deduct from oldest batches first
4. Create BatchIngredientAllocation records
5. Raise InsufficientStockError if not enough inventory
```

---

## 🌱 Setup

### 1. Install Dependencies
```bash
cd services/production_service
pip install -r requirements.txt
```

### 2. Run Service
```bash
uvicorn main:app --reload --port 8004
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

**Test Structure:**
- `tests/fixtures/sample_ipa.bsmx` - Sample BeerSmith file
- `tests/unit/test_beersmith_parser.py` - Parser tests (6 tests)
- `tests/unit/test_batch_state_machine.py` - State machine tests (7 tests)
- `tests/integration/test_production_api.py` - API tests (8+ tests)

**Expected:** 20+ tests passing

---

## 📊 Example Workflow

### 1. Import Recipe
```bash
curl -X POST "http://localhost:8004/api/v1/production/recipes/import" \
  -F "file=@my_ipa.bsmx"
```

### 2. Create Batch
```bash
curl -X POST "http://localhost:8004/api/v1/production/batches" \
  -H "Content-Type: application/json" \
  -d '{
    "recipe_id": 1,
    "batch_number": "IPA-2026-001",
    "planned_volume_liters": 20.0
  }'
```

### 3. Start Brewing (costs allocated)
```bash
curl -X PATCH "http://localhost:8004/api/v1/production/batches/1/start-brewing"
```

**Result:**
- Status: PLANNED → BREWING
- Costs allocated:
  * Malt: $200
  * Hops: $75
  * Yeast: $15
  * Water: $50
  * Labor: $50
  * Overhead: $30
- **Total: $420**

### 4. Move to Fermenter
```bash
curl -X PATCH "http://localhost:8004/api/v1/production/batches/1/start-fermenting"
```

### 5. Complete Batch
```bash
curl -X PATCH "http://localhost:8004/api/v1/production/batches/1/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "actual_volume_liters": 19.5,
    "actual_og": 1.064,
    "actual_fg": 1.011
  }'
```

**Result:**
- Status: → COMPLETED
- Cost/Liter: $420 / 19.5L = **$21.54/L**
- ABV: (1.064 - 1.011) × 131.25 = **6.96%**

---

## 🔗 Integration Points

**Inventory Service (Sprint 1):**
- StockBatch (FIFO cost allocation) - Sprint 4.5

**Finance Service (Sprint 3.5):**
- InternalTransfer (on completion) - Sprint 4.5

**Future (Sprint 5 - CMMS):**
- WaterProductionRun (real water costs)

---

## 📝 Notes

**Sprint 4 Limitations:**
- Cost allocation uses mock data (fixed prices)
- No FinishedProductInventory creation
- No InternalTransfer to Finance
- No event publishing (RabbitMQ infrastructure pending)

**Sprint 4.5 Enhancements:**
- Real FIFO integration with StockBatch
- Finished product creation on completion
- Transfer pricing integration
- Event bus (RabbitMQ)

---

**Status:** ✅ Core MES operational  
**Tests:** 20+ passing  
**Next:** Sprint 4.5 (Real FIFO + Finance integration)
