# Desert Brew Production Service

**Version:** 0.1.0 (Sprint 4.5)  
**Purpose:** Manufacturing Execution System (MES) with full ecosystem integration

---

## 📋 Overview

Production Service tracks brewery production from recipe to finished product:
1. **Import recipes** from BeerSmith (.bsmx files)
2. **Track batches** through 6-state lifecycle (PLANNED → COMPLETED)
3. **Allocate costs** via **real FIFO** from Inventory Service StockBatch
4. **Create finished products** in Inventory upon completion
5. **Generate internal transfers** to Finance Service (Factory → Taproom)
6. **Publish events** to RabbitMQ for downstream consumers

**Sprint 4 (Core):** BeerSmith parser, batch FSM, mock FIFO  
**Sprint 4.5 (Integration):** Real FIFO, Finance/Inventory integration, Event Bus

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

## 🔗 Integration Points (Sprint 4.5)

### Inventory Service
**Purpose:** Real FIFO cost allocation from StockBatch

**Endpoints used:**
- `GET /stock-batches` - Query available stock (FIFO order)
- `PATCH /stock-batches/{id}/consume` - Consume quantity from batch
- `POST /finished-products` - Create finished product on completion

**Flow:**
1. `start_brewing` → Query StockBatch for ingredients
2. Allocate from oldest batches first (FIFO)
3. Create `BatchIngredientAllocation` with real stock_batch_id
4. `complete_batch` → Create `FinishedProductInventory`

### Finance Service
**Purpose:** Transfer pricing (Factory → Taproom)

**Endpoints used:**
- `POST /internal-transfers` - Create transfer on batch completion

**Flow:**
1. `complete_batch` → Calculate cost_per_liter
2. Finance applies transfer pricing (HOUSE: cost × 1.15)
3. Creates InternalTransfer record
4. Factory earns 15% margin, Taproom pays transfer price

### Event Bus (RabbitMQ)
**Purpose:** Notify downstream services of production events

**Events published:**
- `production.batch_started` - When brewing begins
- `production.batch_completed` - When batch finishes

**Exchange:** `production` (topic)

---

## 📡 Sprint 4.5 Features

### 1. Real FIFO Integration ✅
- **Removed:** Mock data with fixed prices
- **Added:** HTTP client for Inventory Service
- **Logic:** `CostAllocator` queries real StockBatch, consumes via API
- **Error handling:** `InsufficientStockError`, `ServiceUnavailableError`

**Example allocation:**
```python
# Production needs 5kg Maris Otter
# Inventory has:
#   - Batch #1: 3kg @ $15/kg (oldest)
#   - Batch #2: 5kg @ $18/kg

# FIFO consumes: 3kg from Batch #1 + 2kg from Batch #2
# Cost: (3 × $15) + (2 × $18) = $45 + $36 = $81
```

### 2. Finance Integration ✅
```bash
# When batch completes:
POST /api/v1/production/batches/1/complete
{
  "actual_volume_liters": 20.0
}

# Production Service:
# 1. Updates cost_per_liter = $420 / 20L = $21/L
# 2. Calls Inventory: POST /finished-products
#    → Creates FinishedProductInventory (#456)
# 3. Calls Finance: POST /internal-transfers
#    → Creates InternalTransfer with transfer_price = $21 × 1.15 = $24.15/L
# 4. Publishes: production.batch_completed event
```

### 3. Event Publishing ✅
**Batch Started Event:**
```json
{
  "batch_id": 1,
  "batch_number": "IPA-2026-001",
  "recipe_name": "American IPA",
  "planned_volume_liters": 20.0,
  "total_cost": 420.00,
  "cost_breakdown": {
    "malt_cost": 75.00,
    "hops_cost": 45.00,
    "yeast_cost": 15.00,
    "water_cost": 15.00,
    "labor_cost": 50.00,
    "overhead_cost": 30.00
  }
}
```

**Batch Completed Event:**
```json
{
  "batch_id": 1,
  "batch_number": "IPA-2026-001",
  "actual_volume_liters": 19.5,
  "cost_per_liter": 21.54,
  "finished_product_id": 456,
  "internal_transfer_id": 789,
  "actual_abv": 6.96
}
```

---

## 🧪 Testing

**Test Coverage:** 40+ tests

**Unit Tests:**
- `test_beersmith_parser.py` (6 tests) - XML parsing
- `test_batch_state_machine.py` (7 tests) - FSM transitions
- `test_inventory_client.py` (7 tests) - HTTP client mocking

**Integration Tests:**
- `test_production_api.py` (15 tests) - Full batch lifecycle
- `test_sprint_4_5_integration.py` (8 tests) - FIFO, Finance, Events

**Run tests:**
```bash
cd services/production_service
pytest -v
pytest --cov=. --cov-report=term-missing
```

---

## 📝 Configuration

**Environment Variables:**
```bash
# Production Service
DATABASE_URL=postgresql://user:pass@localhost/production_db
PORT=8004

# Service URLs (Sprint 4.5)
INVENTORY_SERVICE_URL=http://localhost:8001
FINANCE_SERVICE_URL=http://localhost:8005
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Feature Flags
ENABLE_REAL_FIFO=true  # Sprint 4.5
ENABLE_EVENTS=true     # Sprint 4.5
```

---

## 📊 Metrics

**Sprint 4 (Core):**
- 12 endpoints
- 3 models
- 20 tests
- BeerSmith parser operational

**Sprint 4.5 (Integration):**
- +3 HTTP clients (Inventory, Finance, EventPublisher)
- +2 endpoints (Inventory Service)
- +15 tests
- Real FIFO operational
- Finance integration complete
- Event bus operational

**Total:**
- 12 Production endpoints
- 3 core models
- 3 client modules
- 40+ tests
- Full ecosystem integration

---

**Status:** ✅ Sprint 4.5 COMPLETE  
**Version:** 0.1.0  
**Next:** Sprint 5 (CMMS & Water Treatment)
