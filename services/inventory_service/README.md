# Inventory Service - Desert Brew OS

> **Gestión de inventario con FIFO automático, asset tracking, y trazabilidad completa**

**Version:** v0.4.0  
**Port:** 8001  
**Database:** PostgreSQL

---

## 🎯 Features Implementadas

### ✅ Materia Prima (Raw Materials)
- **FIFO Automático** - Rotación first-in-first-out con SQL locking
- **Stock Batches** - Tracking de lotes individuales
- **Movimientos** - Audit trail completo
- **Transfers** - Movimientos entre ubicaciones
- **Categorías:**
  - `MALT` — Maltas (Pale Ale, Munich, Crystal, etc.)
  - `HOPS` — Lúpulos (Cascade, Mosaic, Saaz, etc.)
  - `YEAST` — Levaduras (US-05, 34/70, etc.)
  - `PACKAGING` — Barriles desechables, tapas, etiquetas
  - `BOTTLES` — Botellas de vidrio
  - `CHEMICALS` — Químicos de limpieza/sanitización
  - `LABELS` — Etiquetas
  - `GASES` — CO₂, O₂ (también en Gas Tanks)

### ✅ Proveedores (Suppliers)
- CRUD completo de proveedores
- Ratings y términos de pago
- Tracking de compras por proveedor
- Historial de lotes recibidos

### ✅ Gases (CO2, O2)
- **Asset Tracking** - Tanques individuales
- **Estados:** FULL, IN_USE, EMPTY, RETURNED
- **Consumo tracking** - Por batch de producción
- **Depósitos** - Gestión de tanques rentados

### ✅ Kegs (Barriles)
- **Asset Management** - Tracking individual con UUID
- **FSM (Finite State Machine)** - 10 estados validados
- **QR Code** - Auto-generado para mobile scanning
- **RFID Support** - Opcional para bulk operations
- **Bulk Operations** - Escaneo masivo transaccional
- **Audit Trail** - Historial completo de transiciones
- **At-Risk Reports** - Kegs en clientes > días threshold

### ✅ Producto Terminado (Cold Room) - **v0.4.0** ✨
- **Cerveza propia** (`HOUSE`) — Producción Desert Brew → Transfer Pricing (+15%)
- **Cerveza comercial** (`COMMERCIAL`) — Corona, Modelo, etc. → Passthrough
- **Cerveza invitada** (`GUEST`) — Colaboraciones craft → Passthrough
- **Merchandising** (`MERCHANDISE`) — Gorras, playeras, vasos, growlers
- **Categorías:** `BEER_KEG`, `BEER_BOTTLE`, `BEER_CAN`, `MERCH_CAP`, `MERCH_SHIRT`, `MERCH_GLASS`, `MERCH_GROWLER`
- **Temperature Monitoring** - Alertas automáticas >7°C
- **Stock Summary** - Dashboard por tipo/categoría
- **Slow-Moving Analysis** - Productos sin movimiento
- **Location Tracking** - Cold rooms + shelf positions

---

## 📊 API Endpoints (39 total)

### Stock (8 endpoints)
- `POST /api/v1/inventory/stock` - Crear lote
- `GET /api/v1/inventory/stock` - Listar con filtros
- `GET /api/v1/inventory/stock/{id}` - Detalle
- `PATCH /api/v1/inventory/stock/{id}` - Actualizar
- `DELETE /api/v1/inventory/stock/{id}` - Soft delete
- `POST /api/v1/inventory/movements` - Registrar movimiento
- `GET /api/v1/inventory/movements` - Listar movimientos
- `GET /api/v1/inventory/movements/batch/{id}` - Por lote

### Suppliers (6 endpoints)
- `POST /api/v1/suppliers` - Crear proveedor
- `GET /api/v1/suppliers` - Listar
- `GET /api/v1/suppliers/{id}` - Detalle
- `PATCH /api/v1/suppliers/{id}` - Actualizar
- `DELETE /api/v1/suppliers/{id}` - Soft delete
- `GET /api/v1/suppliers/{id}/batches` - Lotes del proveedor

### Gas Tanks (7 endpoints)
- `POST /api/v1/inventory/gas-tanks` - Registrar tanque
- `GET /api/v1/inventory/gas-tanks` - Listar
- `PATCH /api/v1/inventory/gas-tanks/{id}` - Actualizar
- `POST /api/v1/inventory/gas-tanks/{id}/refill` - Rellenar
- `POST /api/v1/inventory/gas-tanks/{id}/return` - Retornar
- `POST /api/v1/inventory/gas-consumption` - Registrar consumo
- `GET /api/v1/inventory/gas-consumption/batch/{id}` - Por batch

### Kegs (8 endpoints)
- `POST /api/v1/inventory/kegs` - Crear keg (auto-genera QR)
- `GET /api/v1/inventory/kegs` - Listar con filtros
- `GET /api/v1/inventory/kegs/{id}` - Detalle + historial
- `PATCH /api/v1/inventory/kegs/{id}` - Actualizar
- `PATCH /api/v1/inventory/kegs/{id}/transition` - FSM transition
- `POST /api/v1/inventory/kegs/bulk-scan` - Bulk RFID/QR scan
- `POST /api/v1/inventory/kegs/fill-batch` - Embarrillar batch
- `GET /api/v1/inventory/kegs/at-risk` - Kegs en riesgo

### **Finished Products (10 endpoints) - NUEVO ✨**
- `POST /api/v1/inventory/finished-products` - Crear producto
- `GET /api/v1/inventory/finished-products` - Listar (6 filtros)
- `GET /api/v1/inventory/finished-products/summary` - Stock summary
- `GET /api/v1/inventory/finished-products/slow-moving` - Slow-moving report
- `GET /api/v1/inventory/finished-products/own` - Solo cerveza propia
- `GET /api/v1/inventory/finished-products/{id}` - Detalle + movimientos
- `PATCH /api/v1/inventory/finished-products/{id}` - Actualizar
- `POST /api/v1/inventory/finished-products/{id}/move` - Mover producto
- `POST /api/v1/inventory/cold-room/readings` - Registrar temperatura
- `GET /api/v1/inventory/cold-room/status` - Estado de cuartos fríos

---

## 🚀 Quick Start

### 1. Environment Setup
```bash
cp .env.template .env
# Configurar DATABASE_URL
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Migrations
```bash
cd services/inventory_service
alembic upgrade head
```

### 4. Start Service
```bash
python main.py
# Server: http://localhost:8001
# Docs: http://localhost:8001/docs
```

---

## 📝 API Examples

### Crear Cerveza Propia Embotellada

```bash
POST /api/v1/inventory/finished-products
{
  "sku": "BEER-IPA-COAHUI-BTL355",
  "product_name": "IPA Coahuilaceratops 355ml",
  "product_type": "OWN_PRODUCTION",
  "category": "BEER_BOTTLE",
  "production_batch_id": 42,
  "quantity": 240,
  "unit_measure": "BOTTLES",
  "cold_room_id": "COLD_ROOM_A",
  "shelf_position": "A3",
  "unit_cost": 25.50,
  "best_before": "2026-05-01T00:00:00"
}
```

### Registrar Cerveza Comercial

```bash
POST /api/v1/inventory/finished-products
{
  "sku": "BEER-CORONA-BTL355",
  "product_name": "Corona Extra 355ml",
  "product_type": "COMMERCIAL",
  "category": "BEER_BOTTLE",
  "supplier_id": 10,
  "quantity": 480,
  "unit_measure": "BOTTLES",
  "cold_room_id": "COLD_ROOM_B",
  "unit_cost": 15.50
}
```

### Stock Summary Dashboard

```bash
GET /api/v1/inventory/finished-products/summary

Response:
{
  "own_production": {
    "BEER_BOTTLE": {"quantity": 1200, "value": 30600},
    "BEER_KEG": {"quantity": 15, "value": 22500}
  },
  "commercial": {
    "BEER_BOTTLE": {"quantity": 480, "value": 7440}
  },
  "total_items": 1695,
  "total_value": 60540
}
```

### Temperature Monitoring

```bash
POST /api/v1/inventory/cold-room/readings
{
  "cold_room_id": "COLD_ROOM_A",
  "temperature_celsius": 4.5,
  "humidity_percent": 65
}

Response:
{
  "id": 1,
  "cold_room_id": "COLD_ROOM_A",
  "temperature_celsius": 4.5,
  "humidity_percent": 65,
  "alert_triggered": false,
  "alert_reason": null,
  "timestamp": "2026-02-02T23:00:00"
}
```

### Slow-Moving Products Report

```bash
GET /api/v1/inventory/finished-products/slow-moving?days_threshold=30

Response:
{
  "products": [
    {
      "id": 5,
      "sku": "BEER-OLD-STOCK",
      "product_name": "Old Stock Beer",
      "days_without_movement": 45,
      "value": 12000
    }
  ],
  "total_value_at_risk": 12000
}
```

### Keg Bulk Scan (QR/RFID)

```bash
POST /api/v1/inventory/kegs/bulk-scan
{
  "qr_codes": ["KEG-001-ABC123", "KEG-002-DEF456"],
  "new_state": "CLEAN",
  "location": "Washing Station",
  "user_id": 5
}

Response:
{
  "success_count": 2,
  "failed_count": 0,
  "results": [...]
}
```

---

## 🏗️ Architecture

### Models (11 models)

**Stock Management:**
- `StockBatch` - Lotes de materia prima
- `StockMovement` - Audit trail
- `StockTransfer` - Transfers internos

**Assets:**
- `GasTank` - Tanques de gas individuales
- `GasConsumption` - Consumo tracking
- `KegAsset` - Barriles como assets
- `KegTransition` - Audit log FSM
- `KegTransfer` - Transfers de contenido

**Finished Products:**
- `FinishedProductInventory` - **NUEVO** - Producto terminado
- `ColdRoomReading` - **NUEVO** - Temperature monitoring
- `ProductMovement` - **NUEVO** - Movement audit trail

**Suppliers:**
- `Supplier` - Proveedores

### Business Logic

**FIFO Engine:**
```python
from logic.fifo import allocate_fifo

# Automatic FIFO allocation
allocated = allocate_fifo(
    db=db,
    category="MALT_BASE",
    quantity_needed=100.0
)
```

**Keg State Machine:**
```python
from logic.keg_fsm import KegStateMachine

# Validate and apply transition
KegStateMachine.validate_transition(keg, new_state, context)
KegStateMachine.apply_state_changes(keg, new_state, context)
```

**Cold Room Alerts:**
```python
from models.cold_room_reading import ColdRoomReading

# Auto-check alert conditions
reading = ColdRoomReading.create_reading(
    cold_room_id="COLD_ROOM_A",
    temperature=Decimal('8.5')  # Triggers alert
)
# reading.alert_triggered == True
```

---

## 🗄️ Database

### Migrations (6 total)

```bash
# View current migration status
alembic current

# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

**Migration History:**
- `001_create_keg_assets` - Keg asset tracking
- `002_create_keg_transitions` - Keg state audit log
- `003_create_keg_transfers` - Keg content transfers
- `004_create_finished_products` - **NUEVO** - Finished product inventory
- `005_create_cold_room_readings` - **NUEVO** - Temperature monitoring
- `006_create_product_movements` - **NUEVO** - Product movements

### Indexes

**Optimized Queries:**
- Composite indexes para filtrado eficiente
- Time-series indexes para audit trails
- Foreign key indexes para joins

```sql
-- Finished Products
idx_fp_type_category       -- Summary queries
idx_fp_cold_room_status    -- Location filtering
idx_fp_best_before         -- Expiration queries

-- Cold Room
idx_cr_room_time           -- Time-series queries
idx_cr_alerts              -- Alert dashboard
```

---

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Test Coverage

| Module | Unit Tests | Integration Tests | Total |
|--------|-----------|-------------------|-------|
| Stock/FIFO | 17 | - | 17 |
| Movements | 11 | - | 11 |
| Suppliers | 10 | - | 10 |
| Gases | 14 | - | 14 |
| Kegs | 20 | 12 | 32 |
| **Finished Products** | **21** | **-** | **21** |
| **TOTAL** | **93** | **12** | **105** |

---

## 📦 Enums

### Product Types
```python
class ProductType:
    OWN_PRODUCTION   # Cerveza propia
    COMMERCIAL       # Cerveza comercial
    GUEST_CRAFT      # Cerveza guest brewery
    MERCHANDISE      # Merch (cachuchas, playeras)
```

### Product Categories
```python
class ProductCategory:
    # Beer
    BEER_KEG         # Barriles
    BEER_BOTTLE      # Botellas (355ml, 940ml)
    BEER_CAN         # Latas
    
    # Water
    WATER_BOTTLE     # Agua embotellada
    WATER_JUG        # Garrafón
    
    # Merchandise
    MERCH_CAP        # Cachucha
    MERCH_SHIRT      # Playera
    MERCH_GLASS      # Vaso/Copa
    MERCH_GROWLER    # Growler
```

### Keg States (FSM)
```python
class KegState:
    EMPTY           # Vacío, listo para lavar
    DIRTY           # Sucio, necesita lavado
    CLEAN           # Limpio, listo para llenar
    FILLING         # En proceso de llenado
    FULL            # Lleno, listo para enviar
    TAPPED          # Conectado en taproom
    IN_CLIENT       # En ubicación de cliente
    IN_TRANSIT      # En tránsito
    QUARANTINE      # En cuarentena (QA issue)
    RETIRED         # Fuera de servicio
```

---

## 🔐 Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/inventory_db

# Server
PORT=8001
LOG_LEVEL=INFO

# Features
ENABLE_FIFO_LOCKING=true
```

---

## 📊 Version History

- **v0.1.0** - Raw Materials (Sprint 1)
- **v0.2.0** - Suppliers & Gases (Sprint 1.5)
- **v0.3.0** - Keg Asset Management (Sprint 2)
- **v0.4.0** - Cold Room Inventory (Sprint 2.5) ✨

---

## 🎯 Next Steps

### Sprint 3: Sales Service
- Beer Style catalog (70+ estilos Brewers Association)
- Product catalog
- Multi-channel pricing (Taproom, B2B, Direct)
- 12 endpoints

---

## 📝 Documentation

- **API Docs:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc
- **Health:** http://localhost:8001/health

---

**Built with:**
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Pydantic

**Author:** Desert Brew OS Team  
**License:** Private
