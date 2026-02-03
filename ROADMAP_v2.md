# Desert Brew OS - Roadmap Completo

> **Planificación actualizada con Cold Room Inventory y Sales Service**

---

## ✅ COMPLETADO

### Sprint 1: Infraestructura & Materia Prima (v0.1.0)
**Duración:** 2 semanas  
**Completado:** Enero 2026

**Logros:**
- ✅ Docker Compose con 5 servicios
- ✅ Inventory Service base
- ✅ FIFO automático con locking
- ✅ Audit trail completo
- ✅ 28 tests

### Sprint 1.5: Proveedores & Gases (v0.2.0)
**Duración:** 3 días  
**Completado:** Enero 2026

**Logros:**
- ✅ Sistema de proveedores (6 endpoints)
- ✅ Tracking de gases CO2/O2 (7 endpoints)
- ✅ 42 tests totales
- ✅ Coverage > 85%

**Inventory Service v0.2.0:**
- 21 endpoints API
- 7 modelos completos
- Production-ready para materia prima

### Sprint 2: Keg Asset Management (v0.3.0)
**Duración:** 2 semanas  
**Completado:** Febrero 2026

**Logros:**
- ✅ Modelo `KegAsset` con FSM (10 estados)
- ✅ QR Code auto-generado por keg
- ✅ RFID support opcional
- ✅ Bulk operations (transaccional)
- ✅ Sistema de transfers (barril→barril, barril→embotellado)
- ✅ At-risk reports (kegs >N días en clientes)
- ✅ 8 endpoints API
- ✅ 32 tests (20 unit + 12 integration)
- ✅ 3 Alembic migrations

**Inventory Service v0.3.0:**
- 29 endpoints API (+8)
- 10 modelos
- 74 tests totales

### Sprint 2.5: Cold Room Inventory (v0.4.0)
**Duración:** 1 semana  
**Completado:** Febrero 2026

**Logros:**
- ✅ Modelo `FinishedProductInventory` (3 tipos: Own, Commercial, Guest)
- ✅ Temperature monitoring con alertas automáticas (>7°C)
- ✅ Stock summary por tipo/categoría
- ✅ Slow-moving analysis (>30 días sin movimiento)
- ✅ Location tracking (cold_room + shelf_position)
- ✅ Partial moves (split inventory)
- ✅ Complete audit trail (`ProductMovement`)
- ✅ 10 endpoints API
- ✅ 21 tests unitarios
- ✅ 3 Alembic migrations

**Inventory Service v0.4.0:**
- 39 endpoints API (+10)
- 13 modelos (+3)
- 95 tests totales (+21)
- 6 migrations totales

**Estado Actual:** Production-ready para inventario completo (materia prima + producto terminado + assets)

---

## 🚧 EN PROGRESO / PLANEADO

---

### Sprint 3: Sales Service - Product Catalog
**Duración:** 2 semanas
**Service:** Sales Service (nuevo)

**Objetivos:**

**Setup Base:**
- [ ] FastAPI service base
- [ ] PostgreSQL para catálogo
- [ ] MongoDB para clientes/órdenes
- [ ] Service structure

**Product Catalog (Marketing View):**
- [ ] Modelo `BeerStyle`
  - Datos comerciales: ABV, IBU, SRM
  - Tagline, descripción, flavor profile
  - Link a Production Service (recipe_id)
- [ ] Modelo `Product`
  - SKUs vendibles (botellas, barriles, merch)
  - Soporte multi-producto (cerveza, agua, merch)
  - Categorización completa
- [ ] Beer-specific fields
- [ ] Merch-specific fields

**Multi-Channel Pricing:**
- [ ] Modelo `ProductPrice`
- [ ] 3 canales principales:
  - TAPROOM (B2C, mayor margen)
  - B2B_RESTAURANT (mayoreo, menor margen)
  - DIRECT_TAKEAWAY (intermedio)
- [ ] Cálculo automático IEPS/IVA
- [ ] Márgenes diferenciados por canal
- [ ] Descuentos por volumen (B2B)

**Brewers Association Integration:**
- [ ] Seed database con 70+ estilos BA
- [ ] Modelo `BAStyleCatalog` (read-only)
- [ ] Validación de rangos (OG, FG, IBU, SRM)
- [ ] Referencia `ba_style_id` en BeerStyle

**CRUD & APIs:**
- [ ] POST /beer-styles
- [ ] GET /beer-styles
- [ ] POST /products
- [ ] GET /products (filtros: category, channel, available)
- [ ] PATCH /products/{id}
- [ ] POST /products/{id}/prices
- [ ] GET /products/{id}/prices (por canal)

**Business Model:**
- [ ] Documentación de 3 canales de venta
- [ ] Matriz de pricing
- [ ] Estrategia de márgenes

**Entregables:**
- 12 endpoints
- 20+ tests
- Catálogo completo multi-canal

---

### Sprint 3.5: Aguas Minerales
**Duración:** 1 semana
**Services:** Sales + Production

**Objetivos:**

**Product Line Extension:**
- [ ] Enum `WaterType` (SPARKLING, STILL, FLAVORED)
- [ ] Categorías: WATER_BOTTLE, WATER_GARRAFON, WATER_CAN
- [ ] SKUs:
  - WATER-SPARK-NATURAL-500ML
  - WATER-SPARK-LIMON-500ML
  - WATER-STILL-GARRAFON-20L
- [ ] Flavors: Limón, Toronja, Jamaica

**Production Model:**
- [ ] Modelo `WaterProductionBatch`
  - pH, TDS (Total Dissolved Solids)
  - CO2 usage tracking (sparkling)
  - QA checks (calidad del agua)
- [ ] Simplified costing vs. cerveza

**Pricing Strategy:**
- [ ] Multi-canal pricing:
  - Taproom: $25/500ml
  - Venta Directa: $20/500ml
  - B2B: $15/500ml (caja 24)
- [ ] Garrafón 20L: $80

**Integration:**
- [ ] Inventory: CO2 consumption para carbonatación
- [ ] Production: batch tracking
- [ ] Sales: productos en catálogo

**Entregables:**
- 6 endpoints
- 10+ tests
- Nueva línea de productos lista

---

### Sprint 4-5: Production Service
**Duración:** 3-4 semanas
**Service:** Production Service (nuevo)

**Objetivos:**

**Recetas Técnicas (Technical View):**
- [ ] Modelo `Recipe`
  - OG/FG en °Brix (conversión a SG automática)
  - pH inicial/final (macerado, cerveza terminada)
  - Temperaturas de fermentación
  - Tiempos de macerado/hervor
  - Perfil de agua (Ca, SO₄, Cl)
- [ ] Modelo `RecipeIngredient`
  - Cantidad por batch
  - Usage point (MASH, BOIL, FERMENTATION)
- [ ] Integración con Inventory FIFO

**Production Batches:**
- [ ] Modelo `ProductionBatch`
  - Target vs. Real (volúmenes, OG/FG)
  - Tracking de mermas (boil off, trub)
  - Cálculo automático de ABV real
- [ ] Modelo `FermentationReading`
  - Tracking diario: °Brix, pH, temperatura
  - Logs de actividad
  - Detección de terminal gravity

**Core Features:**
- [ ] Funciones de conversión:
  - `brix_to_sg()`
  - `sg_to_brix()`
  - `calculate_abv(og, fg)`
- [ ] Validación vs. BA style ranges
- [ ] Alertas:
  - Mermas >15%
  - Fuera de rango (OG/FG)
  - Temperatura fuera de spec
- [ ] Trazabilidad completa: batch → ingredientes → proveedores

**Brewhouse Config:**
- [ ] Configuración para 90L → 40L output
- [ ] Pérdidas estándar:
  - Granos absorben ~10L
  - Evaporación ~10L
  - Trub ~10L
- [ ] Eficiencia del sistema (~44%)

**Event-Driven:**
- [ ] Event: `batch.created` → Inventory allocate_stock_fifo
- [ ] Event: `batch.packaged` → Cold Room inventory creation
- [ ] RabbitMQ integration

**Entregables:**
- 12 endpoints
- 25+ tests
- Sistema completo de recetas y producción

---

### Sprint 6: Telemetry & IoT
**Duración:** 2 semanas
**Service:** Telemetry Service (nuevo)

- [ ] TimescaleDB setup (hypertables)
- [ ] Pipeline MQTT → TimescaleDB
- [ ] Real-time fermentation monitoring
- [ ] Temperature/gravity graphs
- [ ] Alertas automáticas

---

### Sprint 7-8: B2B Sales & Orders
**Duración:** 3 semanas
**Service:** Sales Service (expansion)

- [ ] MongoDB models (clientes, órdenes)
- [ ] Cliente B2B model
- [ ] Order model con estados
- [ ] Double-gate credit control
- [ ] Keg lending tracking
- [ ] Payment terms (NET_30, NET_60)

---

### 🚀 Sprint 9-10: Antigravity (Costing Core v1.0)
**Duración:** 2 semanas (Hard Deadline)
**Service:** Finance Service (nuevo)
**Codename:** "Antigravity" - Motor de Costeo por Absorción en Tiempo Real

**Objetivos del Sprint:**
Implementar un motor de Costeo por Absorción en Tiempo Real que calcule el COGS (Cost of Goods Sold) dinámico de cada Batch basándose en el consumo FIFO de inventario, asignación de energéticos y mano de obra directa.

**Arquitectura:**
- **Patrón:** Event-Driven Observer (RabbitMQ)
- **Desacoplamiento:** Finance NO modifica Inventory ni Production
- **Flow:** Production consume → Inventory emite evento → Finance "monetiza"
- **Database:** PostgreSQL con `DECIMAL(14,4)` (no floats)

#### 📊 Database Models

**BatchLedger (Libro Mayor Inmutable):**
- [ ] Tabla `batch_ledger`:
  ```python
  id: Integer (PK)
  batch_id: UUID (indexed) 
  source_event_id: String  # FIFO layer traceability
  description: String      # "50kg Pale Ale Lote #455"
  cost_type: Enum          # MATERIAL, LABOR, ENERGY, OVERHEAD
  amount: DECIMAL(14,4)    # Costo monetario neto
  currency: String(3)      # "MXN"
  recorded_at: DateTime
  ```
- [ ] **Business Rule:** Cada gramo de malta o minuto de trabajo agrega una fila
- [ ] **Costo Total:** SUM(amount) WHERE batch_id = X

**BatchFinancialSummary (Materialized View):**
- [ ] Tabla `batch_financial_summary`:
  ```python
  batch_id: UUID (PK)
  total_material_cost: DECIMAL(14,2)
  total_labor_cost: DECIMAL(14,2)
  total_energy_cost: DECIMAL(14,2)
  total_overhead_cost: DECIMAL(14,2)
  final_yield_liters: DECIMAL(10,2)
  cost_per_liter: Decimal (computed)
  ```
- [ ] Actualización vía Trigger o Background Task
- [ ] Optimización para dashboards

**CostType Enum:**
- [ ] `MATERIAL` - Malta, Lúpulo (Directo)
- [ ] `LABOR` - Horas hombre (Directo/Indirecto)
- [ ] `ENERGY` - Gas, Luz (Variable)
- [ ] `OVERHEAD` - Alquiler, Depreciación (Fijo)

#### 🔌 Backend Tasks

**A. FIFO Cost Listener (RabbitMQ Consumer):**
- [ ] Crear consumidor: `queue: inventory.consumed`
- [ ] **Event Schema:**
  ```json
  {
    "sku": "MALTA-PALE",
    "qty": 50,
    "layers": [
      {"lot_id": "A1", "cost": 15.50, "qty": 20},
      {"lot_id": "A2", "cost": 16.00, "qty": 30}
    ]
  }
  ```
- [ ] Lógica: Calcular costo ponderado
- [ ] Escribir en `BatchLedger` con `cost_type=MATERIAL`

**B. Módulo de Costos Indirectos (Overhead):**
- [ ] Endpoint: `POST /api/v1/finance/overhead-rules`
- [ ] Configurar costos fijos por hora de equipo
- [ ] **Ejemplo:** Fermentador #3 = $5 MXN/hora (depreciación + glicol)
- [ ] **Business Rule:** Si batch estuvo 8h → Agregar $40 al ledger
- [ ] Almacenar reglas en tabla `overhead_rules`

**C. Unit Economics API:**
- [ ] Endpoint: `GET /api/v1/finance/batch/{batch_id}/pnl`
- [ ] **Output:** Desglose completo de P&L
  ```json
  {
    "batch_id": "uuid",
    "total_volume_L": 750,
    "costs": {
      "materials": 12500.00,
      "energy": 800.00,
      "labor": 700.00,
      "overhead": 500.00
    },
    "total_cost": 14500.00,
    "unit_cost_L": 19.33,
    "suggested_wholesale_price": 35.00,
    "margin_percent": 44.8
  }
  ```

**D. Gestión de Levadura (Generaciones):**
- [ ] Modelo `YeastGeneration`:
  - Gen 0 (Paquete nuevo): Costo 100% al batch
  - Gen 1-N (Reutilizada): Costo $0 o costo marginal de lavado
- [ ] **Impacto:** Reduce drásticamente costo/L en batches subsecuentes

**E. Trub Loss Handling:**
- [ ] **Business Rule:** Si entran 800L pero salen 750L vendibles:
  - Costo total / 750L (no 800L)
  - Penaliza automáticamente la eficiencia
- [ ] Validación: `yield_efficiency = final_volume / initial_volume`

#### 🎨 Frontend Tasks (Flutter)

**A. Waterfall Chart (Cascada de Costos):**
- [ ] Widget de visualización gráfica
- [ ] Barras apiladas: Agua → Malta → Lúpulo → Levadura → Energía → Costo Final
- [ ] Interactivo (tap para detalles)

**B. Input de Costos Ad-hoc:**
- [ ] Pantalla para costos no estandarizados
- [ ] Ejemplos: "Levadura líquida especial", "Compra de hielo de emergencia"
- [ ] Categorización manual (MATERIAL, OVERHEAD, etc.)

#### 🔌 IoT Integration (Edge/Simulado)

**Telemetría Energética:**
- [ ] Tabla de equivalencias teóricas
- [ ] **Lógica:** Sensor reporta Chiller 4h @ 100% → Calcular kWh estimados
- [ ] Fórmula: `kWh_per_fermentation_hour × 4 × Costo_CFE`
- [ ] **Futuro:** Lectura real de pinzas amperimétricas

#### 🧪 Testing & Validation

**Test Case 1 (FIFO Pricing):**
- [ ] Simular receta "IIPA" del business model
- [ ] Ingresar insumos con Lote 1 (precio base)
- [ ] Aumentar precio en Lote 2
- [ ] **Validar:** Sistema usa FIFO correctamente
- [ ] **Validar:** Costo del batch aumenta SIN afectar batches cerrados

**Test Case 2 (Efficiency Impact):**
- [ ] Batch A: 800L → 750L (93.75% efficiency)
- [ ] Batch B: 800L → 700L (87.5% efficiency)
- [ ] **Validar:** Batch B tiene mayor costo/L automáticamente

**Seed Data:**
- [ ] Ejecutar `/seed finance`
- [ ] Poblar costos históricos:
  - CFE (Saltillo): $2.50 MXN/kWh
  - Agua: $0.15 MXN/L
  - Gas: $18.50 MXN/kg
- [ ] Benchmarks realistas para desarrollo

#### 📋 Entregables

- [ ] **Backend:** 8 endpoints API
- [ ] **Models:** 4 tablas nuevas
- [ ] **Event Consumers:** 1 RabbitMQ consumer
- [ ] **Tests:** 20+ tests
- [ ] **Frontend:** 2 widgets (Waterfall + Ad-hoc input)
- [ ] **Documentation:** P&L calculation methodology

**Dependencias:**
- ✅ Inventory Service (completado)
- 🚧 Production Service (en progreso Sprint 4-5)

**Nota Crítica:** Este sprint requiere Production Service operacional para funcionar completamente. Puede iniciarse en paralelo con mocks de eventos.

---

### 🚀 Sprint 11-12: Antigravity V2 (TapRoom POS - Dead Reckoning)
**Duración:** 2 semanas (Hard Deadline)
**Service:** POS Flutter App + Inventory Service Extension
**Codename:** "Antigravity V2" - Control de Inventario por Estima

**Objetivos del Sprint:**
Implementar un sistema de control de inventario por estima POS (Dead Reckoning) capaz de gestionar múltiples formatos de salida (Pintas, Jarras, Growlers) con deducción de mermas integrada y bloqueo preventivo de ventas.

**Stack:**
- FastAPI (Backend)
- Flutter + Riverpod (Frontend)
- PostgreSQL (Inventory extension)
- SQLAlchemy

#### 📐 Constantes de Ingeniería (The Physics)

**Reglas Inmutables (Based on 85% efficiency):**

| Formato | Volumen Nominal (Cliente) | Volumen Deducido (Tanque) | Factor Merma | Lógica |
|---------|---------------------------|---------------------------|--------------|--------|
| Pinta 355ml | 355 ml | 417 ml | 1.17x | Venta estándar |
| Jarra 1.2L | 1,200 ml | 1,408 ml | 1.17x | 3.4x Pintas. Alto riesgo espuma |
| Growler 32oz | 946 ml | 1,111 ml | 1.17x | Llenado lento |
| Growler 64oz | 1,893 ml | 2,221 ml | 1.17x | "Tank Killer" - Baja 12% del barril |

**Nota:** Factor de merma 1.17x = 85% efficiency (15% espuma + pérdida)

#### 🗄️ Backend Tasks

**A. [BE-01] Serving Size Engine (CRÍTICO):**
- [ ] **Tabla Paramétrica:** `serving_sizes`
  ```sql
  CREATE TABLE serving_sizes (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    nominal_volume_liters DECIMAL(6,3),
    deduction_volume_liters DECIMAL(6,3),
    is_active BOOLEAN DEFAULT true
  );
  ```
- [ ] **Seed Data:**
  ```sql
  INSERT INTO serving_sizes VALUES
  ('PINT_355',   'Vaso Estándar (355ml)', 0.355, 0.417, true),
  ('PITCHER_12', 'Jarra (1.2L)',          1.200, 1.408, true),
  ('GROWLER_32', 'Growler (32oz)',        0.946, 1.111, true),
  ('GROWLER_64', 'Growler (64oz)',        1.893, 2.221, true);
  ```
- [ ] **NO hardcodear valores** en código
- [ ] Migration + Seeder SQL

**B. [BE-02] Smart Pour Endpoint con Stock Validation (CRÍTICO):**
- [ ] Endpoint: `POST /api/v1/taproom/pour`
- [ ] **Input Schema:**
  ```json
  {
    "line_id": 1,
    "serving_id": "GROWLER_64",
    "user_id": 5
  }
  ```
- [ ] **Logic Flow:**
  1. Lock row del keg en Línea 1
  2. Get `current_volume` (ej: 1.5L)
  3. Get `deduction` de serving_size (Growler 64 = 2.22L)
  4. **Validation:**
     ```python
     if current_volume < deduction_volume:
         raise HTTPException(
             status_code=409,
             detail=f"Volumen insuficiente. Quedan {current_volume}L, se requieren {deduction_volume}L"
         )
     ```
  5. Si pasa: `new_volume = current_volume - deduction_volume`
  6. Update keg volume
  7. Log en `pour_transactions`
- [ ] **Return:** Nuevo estado del keg

**C. [BE-03] Keg Line Assignment:**
- [ ] Tabla `tap_lines`:
  ```python
  id: Integer (1-8)  # Physical tap number
  keg_id: UUID       # Current keg assigned
  beer_style_id: Int # What's on tap
  active: Boolean
  assigned_at: DateTime
  ```
- [ ] Endpoint: `PATCH /api/v1/taproom/lines/{line_id}/assign`
- [ ] **Business Rule:** Solo 1 keg por línea activa

**D. [BE-04] Pour Transaction Log:**
- [ ] Tabla `pour_transactions`:
  ```python
  id: Integer
  line_id: Integer
  serving_size_id: String
  volume_deducted: Decimal
  keg_id: UUID
  user_id: Integer
  timestamp: DateTime
  ```
- [ ] **Propósito:** Audit trail completo de ventas
- [ ] Reconciliación física vs. estimado

#### 🎨 Frontend Tasks (Flutter)

**A. [FE-01] Tap Selection UI (ALTA PRIORIDAD):**
- [ ] **Screen:** Taproom Dashboard
- [ ] **Grid de 8 tarjetas** (8 líneas de tap)
- [ ] **Por tarjeta:**
  - Nombre de cerveza
  - ABV / IBU
  - Nivel del keg (progress bar)
  - Color indicator:
    - Verde: >50% lleno
    - Amarillo: 20-50%
    - Rojo: <20% ("casi vacío")

**B. [FE-02] Size Selection Modal (ALTA):**
- [ ] **Trigger:** Tap en tarjeta de cerveza
- [ ] **Bottom Sheet** con 4 botones:
  - Pinta 355ml - $XX MXN
  - Jarra 1.2L - $XX MXN
  - Growler 32oz - $XX MXN
  - Growler 64oz - $XX MXN
- [ ] Precios traídos del backend (Sales Service)

**C. [FE-03] Smart Blocking Logic (CRÍTICO):**
- [ ] **Regla Visual Client-Side:**
  ```dart
  if (keg.remaining_liters < 2.5) {
    // Disable Growler 64 button (make it GRAY)
    // Show tooltip: "Inventario insuficiente"
  }
  
  if (keg.remaining_liters < 1.5) {
    // Disable Jarra button
  }
  
  if (keg.remaining_liters < 0.5) {
    // Disable ALL except Pinta
  }
  ```
- [ ] **Toast Message:** Si intenta tap disabled button:
  - "Inventario insuficiente para formato grande. Sugerir Pinta."

**D. [FE-04] Real-time Sync (Riverpod State):**
- [ ] Provider: `tapLinesProvider`
- [ ] **Polling:** Cada 10 segundos
- [ ] **Optimistic Updates:** Inmediato tras pour + server confirmation
- [ ] **Error Handling:** Revert si server rechaza (409)

#### 🔄 Sequence Diagram (Smart Check Flow)

```
Mesero → iPad: Toca "IPA" (Línea 1)
iPad → iPad: Checa Cache (Vol: 1.8L)
iPad → iPad: Client Logic:
  - Disable "Growler 64" (Req: 2.2L)
  - Enable "Jarra" (Req: 1.4L)
  - Enable "Pinta" (Req: 0.4L)

Mesero → iPad: Selecciona "Jarra 1.2L"
iPad → Backend: POST /pour {line: 1, size: "PITCHER_12"}

Backend → DB: Lock Row
Backend → DB: Check Volume (1.8L)
Backend → DB: Validate: 1.8 >= 1.408 ✓
Backend → DB: UPDATE volume = 1.8 - 1.408 = 0.392L
Backend → iPad: OK. Restante: 0.39L

iPad → iPad: Actualizar UI:
  - Tanque ROJO (casi vacío)
  - Bloquear Jarras/Growlers
  - Solo Pintas disponibles
```

#### 🧪 Testing & Edge Cases

**Test Case 1: Happy Path (Pinta):**
- [ ] Keg: 10L disponibles
- [ ] Pour: Pinta (0.417L)
- [ ] **Expected:** Success, keg = 9.583L

**Test Case 2: Blocking Prevention:**
- [ ] Keg: 2.0L disponibles
- [ ] Intento: Growler 64 (2.221L)
- [ ] **Expected:** Error 409 "Volumen insuficiente"
- [ ] UI: Botón deshabilitado desde inicio

**Test Case 3: Race Condition:**
- [ ] 2 meseros intentan pour simultáneo
- [ ] **Expected:** Row locking previene double-deduction
- [ ] Segundo request espera o falla con mensaje claro

**Test Case 4: Near-Empty Workflow:**
- [ ] Keg: 0.5L restantes
- [ ] **Expected UI:**
  - Solo Pinta habilitada
  - Warning visual: "Último vaso disponible"
  - Sugerir cambio de keg

#### 🔧 Additional Features

**A. Low Level Alert:**
- [ ] Backend: Webhook cuando keg <10%
- [ ] Notificación push a manager
- [ ] "Preparar siguiente keg para Línea X"

**B. Statistical Reconciliation:**
- [ ] Endpoint: `GET /api/v1/taproom/reconciliation`
- [ ] **Output:**
  ```json
  {
    "keg_id": "uuid",
    "estimated_remaining": 2.5,
    "pours_count": 45,
    "total_volume_deducted": 17.5,
    "discrepancy_liters": 0.2,
    "discrepancy_percent": 1.1
  }
  ```
- [ ] **Purpose:** Detectar fugas o serving errors

**C. Waste Tracking:**
- [ ] Tabla `waste_log`:
  - Keg change waste (fond
o del barril)
  - Line cleaning
  - Spills
- [ ] Endpoint: `POST /api/v1/taproom/waste`

#### 📋 Entregables

- [ ] **Backend:** 6 endpoints API
- [ ] **Models:** 3 tablas nuevas
- [ ] **Frontend:** 4 screens/widgets principales
- [ ] **Tests:** 15+ tests (unit + integration)
- [ ] **Seed Data:** Serving sizes + 8 tap lines
- [ ] **Documentation:** Dead reckoning methodology

**Dependencias:**
- ✅ Inventory Service Keg Management (Sprint 2)
- ✅ Sales Service Product Catalog (Sprint 3)

**Nota Técnica:** Sistema diseñado para operar SIN balanzas ni sensores de nivel. Pure software estimation basado en física real de serving.

---

## 🎯 Arquitectura de Microservicios

### Servicios Implementados
1. **Inventory Service** ✅ (v0.4.0) - **PRODUCTION READY**
   - Materia prima (FIFO automático)
   - Proveedores & Gases
   - Keg Asset Management
   - Cold Room Inventory
   - **39 endpoints**
   - **95 tests**
   - **6 migrations**

### Planeados
3. **Sales Service** 📋
   - Product Catalog (Sprint 3)
   - Multi-channel Pricing
   - Aguas Minerales (Sprint 3.5)
   - B2B Orders (Sprint 7-8)
   - **~20 endpoints**

4. **Production Service** 📋
   - Recetas técnicas (Sprint 4-5)
   - Production batches
   - Fermentation tracking
   - **~12 endpoints**

5. **Telemetry Service** 📋
   - TimescaleDB
   - IoT sensors
   - Real-time monitoring
   - **~8 endpoints**

6. **Finance Service** 📋
   - Costing
   - IEPS/IVA
   - Cuentas por pagar
   - **~10 endpoints**

7. **POS Service** 📋
   - Taproom orders
   - Flutter app
   - Offline-first
   - **~15 endpoints**

**Total proyectado:** ~100+ endpoints

---

## � Timeline Actualizado

| Sprint | Servicio | Duración | Endpoints | Tests | Status |
|--------|----------|----------|-----------|-------|--------|
| S1 | Inventory (materia prima) | 2 sem | 21 | 28 | ✅ Done |
| S1.5 | Inventory (proveedores + gases) | 3 días | +8 | +14 | ✅ Done |
| S2 | Inventory (kegs) | 2 sem | +8 | +32 | ✅ Done |
| S2.5 | Inventory (cold room) | 1 sem | +10 | +21 | ✅ Done |
| **Subtotal Inventory** | **v0.4.0** | - | **39** | **95** | ✅ **Complete** |
| S3 | Sales Service (catalog) | 2 sem | 12 | 20 | 📋 Planned |
| S3.5 | Aguas Minerales | 1 sem | 6 | 10 | 📋 Planned |
| S4-5 | Production Service | 3-4 sem | 12 | 25 | 📋 Planned |
| S6 | Telemetry | 2 sem | 8 | 15 | 📋 Planned |
| S7-8 | Sales Orders (B2B) | 3 sem | 8 | 15 | 📋 Planned |
| S9-10 | Finance | 2-3 sem | 10 | 20 | 📋 Planned |
| S11-12 | POS Taproom | 3-4 sem | 15 | 25 | 📋 Planned |

**Duración total:** 6-7 meses desde inicio

---

## 🎯 Hitos Clave

| Hito | Sprint | Entregable | Impacto |
|------|--------|------------|---------|
| **H1** | S2.5 | Inventario producto terminado | Control de stock completo (materia prima + terminado) |
| **H2** | S3 | Catálogo multi-canal | Pricing diferenciado por canal de venta |
| **H3** | S5 | Trazabilidad completa | Batch → Ingredientes → Proveedores |
| **H4** | S8 | B2B Credit Control | Protección de capital de trabajo |
| **H5** | S12 | POS Taproom | Go live operacional |

---

## 📈 Progreso Actual

**Completado:**
- ✅ **Inventory Service v0.4.0** - Production Ready
- ✅ 4 sprints completados (S1, S1.5, S2, S2.5)
- ✅ 95 tests, >85% coverage
- ✅ 39 API endpoints
- ✅ 13 modelos de datos
- ✅ 6 Alembic migrations
- ✅ FIFO automático + Asset Management + Cold Room

**Features Disponibles:**
- ✅ Materia prima (FIFO con locking)
- ✅ Proveedores & Gases
- ✅ Keg tracking (FSM, QR, RFID, bulk ops)
- ✅ Producto terminado (3 tipos)
- ✅ Temperature monitoring
- ✅ Stock analytics & reports

**Diseñado (documentado, listo para implementar):**
- 📋 Sales Service multi-canal (Sprint 3)
- 📋 Aguas Minerales (Sprint 3.5)
- 📋 Production Service (Sprint 4-5)
- 📋 Finance Service - Antigravity (Sprint 9-10)
- 📋 TapRoom POS - Antigravity V2 (Sprint 11-12)

**Próximo sprint:** Sprint 3 - Sales Service (Product Catalog)

---

**Última actualización:** 2026-02-02  
**Versión Actual:** v0.4.0 (Inventory Service)  
**Sprints Completados:** 4/12  
**Progreso General:** ~33% (Base sólida establecida)  
**Responsable:** Equipo de Desarrollo
