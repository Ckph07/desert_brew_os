# Desert Brew Production Service

**Version:** 0.2.0  
**Purpose:** Manufacturing Execution System (MES) with BeerSmith integration + Cost Management

---

## 📋 Overview

Production Service tracks brewery production from recipe to finished product:
1. **Create recipes** manually or import from BeerSmith (.bsmx files)
2. **Track batches** through 6-state lifecycle (PLANNED → COMPLETED)
3. **Allocate costs** via **real FIFO** from Inventory Service StockBatch
4. **Manage fixed costs** ($57,900/mo → $32.17/L real overhead)
5. **Create finished products** in Inventory upon completion
6. **Generate internal transfers** to Finance Service (Factory → Taproom)
7. **Publish events** to RabbitMQ for downstream consumers

---

## 🏗️ Architecture

### Models (6)

| Model | Purpose |
|-------|---------|
| `Recipe` | BeerSmith or manual recipe data |
| `ProductionBatch` | 6-state FSM (PLANNED → COMPLETED) |
| `BatchIngredientAllocation` | FIFO cost tracing per ingredient |
| `IngredientPrice` | Reference pricing for production ingredients |
| `FixedMonthlyCost` | Monthly overhead categories ($57,900 total) |
| `ProductionTarget` | Monthly volume target for per-liter calc |

---

## 🔌 API Endpoints (26)

### Recipes (6)

**1. Create Recipe (Manual)**
```http
POST /api/v1/production/recipes
Content-Type: application/json

{
  "name": "Desértica Blonde Ale",
  "style": "Blonde Ale",
  "brewer": "Carlos",
  "batch_size_liters": 40.0,
  "fermentables": [
    {"name": "Malta Pale Ale / Pilsen", "amount_kg": 7.0, "color_srm": 2.0, "type": "Grain"},
    {"name": "Malta Munich", "amount_kg": 1.0, "color_srm": 9.0, "type": "Grain"}
  ],
  "hops": [
    {"name": "Saaz", "amount_g": 30.0, "time_min": 60, "use": "Boil", "alpha_acid": 3.5}
  ],
  "yeast": [
    {"name": "SafAle US-05", "lab": "Fermentis", "type": "Ale"}
  ],
  "mash_steps": [
    {"step": "Mash In", "temp_c": 67.0, "time_min": 60}
  ],
  "expected_og": 1.048,
  "expected_fg": 1.010,
  "expected_abv": 4.98,
  "ibu": 20.0,
  "brewhouse_efficiency": 75.0,
  "notes": "Receta para 40L, fermentar a 18°C"
}
```

**Required fields:** `name`, `batch_size_liters`, `fermentables` (min 1), `yeast` (min 1)

**2. Import BeerSmith Recipe**
```http
POST /api/v1/production/recipes/import
Content-Type: multipart/form-data

file: sample_ipa.bsmx
```

**3. Update Recipe**
```http
PATCH /api/v1/production/recipes/{id}
Content-Type: application/json

{"style": "West Coast IPA", "ibu": 75.0}
```

**4-6. List / Get / Delete Recipes**
```http
GET /api/v1/production/recipes
GET /api/v1/production/recipes/{id}
DELETE /api/v1/production/recipes/{id}
```

---

### Production Batches (6)

| # | Method | Endpoint | Description |
|---|--------|----------|-------------|
| 7 | POST | `/batches` | Create batch (PLANNED) |
| 8 | GET | `/batches` | List batches (filter by status) |
| 9 | GET | `/batches/{id}` | Get batch details |
| 10 | PATCH | `/batches/{id}/start-brewing` | PLANNED → BREWING + FIFO allocation |
| 11 | PATCH | `/batches/{id}/start-fermenting` | BREWING → FERMENTING |
| 12 | PATCH | `/batches/{id}/complete` | → COMPLETED + FinishedProduct + InternalTransfer |

---

### Cost Allocation (2)

| # | Method | Endpoint | Description |
|---|--------|----------|-------------|
| 13 | GET | `/batches/{id}/cost-breakdown` | FIFO cost breakdown per ingredient |

---

### Ingredient Prices (6)

Reference pricing for production ingredients.

| # | Method | Endpoint | Description |
|---|--------|----------|-------------|
| 14 | POST | `/ingredients` | Create ingredient price |
| 15 | GET | `/ingredients` | List (filter by category, search) |
| 16 | GET | `/ingredients/summary` | Count by category |
| 17 | GET | `/ingredients/{id}` | Get ingredient details |
| 18 | PATCH | `/ingredients/{id}` | Update price |
| 19 | DELETE | `/ingredients/{id}` | Soft-delete (is_active=false) |

**Categories:** `MALT`, `HOP`, `YEAST`, `ADJUNCT`, `CHEMICAL`, `PACKAGING`, `OTHER`

---

### Fixed Monthly Costs (6)

Monthly overhead tracking → per-liter cost calculation.

| # | Method | Endpoint | Description |
|---|--------|----------|-------------|
| 20 | POST | `/costs/fixed` | Create fixed cost |
| 21 | GET | `/costs/fixed` | List fixed costs |
| 22 | PATCH | `/costs/fixed/{id}` | Update amount |
| 23 | DELETE | `/costs/fixed/{id}` | Soft-delete |
| 24 | POST | `/costs/target` | Set production target (auto-calc $/L) |
| 25 | GET | `/costs/target` | Get current target |
| 26 | GET | `/costs/summary` | Consolidated cost summary |

**Desert Brew Real Costs:**
```
Gasolina           $2,000
Energía            $8,000
Agua               $2,500
Recursos Humanos   $25,000
Operación Planta   $9,500
Gas y CO₂          $7,500
Comunicaciones     $900
Desgaste Vehicular $2,500
──────────────────────────
TOTAL              $57,900 / 1,800L = $32.17/L
```

---

## 🧮 Business Logic

### Recipe Creation
- **Manual:** Full JSON body with validated ingredient sub-schemas (`FermentableInput`, `HopInput`, `YeastInput`, `MashStepInput`)
- **BeerSmith:** Upload .bsmx XML file, auto-parsed

### Cost Allocation (Real FIFO)
```python
# 1. Query Inventory Service for StockBatch (oldest first)
# 2. Consume from oldest batches (FIFO)
# 3. Create BatchIngredientAllocation records
# 4. Calculate overhead from FixedMonthlyCost + ProductionTarget
# 5. overhead_cost = fixed_cost_per_liter × batch_volume_liters
```

### Batch Completion Flow
```
complete_batch() →
  1. Update actual volume, OG, FG, ABV
  2. Recalculate cost_per_liter
  3. Create FinishedProductInventory (Inventory Service)
  4. Create InternalTransfer Factory→Taproom (Finance Service)
  5. Publish production.batch_completed (RabbitMQ)
```

---

## 🌱 Setup

```bash
cd services/production_service
pip install -r requirements.txt
uvicorn main:app --reload --port 8004
```

## 🧪 Testing

```bash
pip install -r requirements-test.txt
pytest tests/ -v
```

**Current:** 53 tests, 0.78s  
**Coverage:** Recipes (8), Batches (5), FIFO (4), Finance (1), State Machine (7), Parser (5), Inventory Client (7), Cost Management (17)

---

## 🔗 Inter-Service Dependencies

| Service | Purpose | Client |
|---------|---------|--------|
| Inventory (8001) | FIFO StockBatch, FinishedProduct | `InventoryServiceClient` |
| Finance (8005) | InternalTransfer (Factory→Taproom) | `FinanceServiceClient` |
| RabbitMQ (5672) | Event publishing | `EventPublisher` |

---

## 📂 File Structure

```
production_service/
├── main.py                    # FastAPI app (v0.2.0)
├── database.py                # PostgreSQL config
├── exceptions.py              # InsufficientStock, ServiceUnavailable
├── api/
│   ├── production_routes.py   # Recipes + Batches (14 endpoints)
│   ├── ingredient_price_routes.py  # Ingredient CRUD (6 endpoints)
│   └── fixed_cost_routes.py   # Fixed costs + target (6 endpoints)
├── models/
│   ├── recipe.py              # Recipe model
│   ├── production_batch.py    # BatchStatus FSM
│   ├── batch_ingredient_allocation.py
│   ├── ingredient_price.py    # Reference pricing
│   └── fixed_monthly_cost.py  # FixedMonthlyCost + ProductionTarget
├── schemas/
│   ├── production.py          # Recipe/Batch/Cost schemas
│   └── cost_management.py     # Ingredient/Fixed cost schemas
├── logic/
│   ├── beersmith_parser.py    # .bsmx XML parser
│   ├── batch_state_machine.py # FSM transitions
│   └── cost_allocator.py      # Real FIFO + overhead
├── clients/
│   ├── inventory_client.py    # HTTP → Inventory Service
│   └── finance_client.py      # HTTP → Finance Service
├── events/
│   └── publisher.py           # RabbitMQ publisher
└── tests/
    ├── conftest.py            # SQLite + mock overrides
    ├── fixtures/
    │   └── sample_ipa.bsmx
    ├── integration/
    │   ├── test_production_api.py
    │   ├── test_sprint_4_5_integration.py
    │   └── test_cost_management.py
    └── unit/
        ├── test_beersmith_parser.py
        ├── test_batch_state_machine.py
        └── test_inventory_client.py
```
