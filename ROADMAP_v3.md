# Desert Brew OS - Roadmap v3.0 (Layered Architecture)

> **Reestructurado por Capas de Integridad Financiera**

**Version:** 3.0  
**Fecha:** 2026-02-03  
**Filosofía:** "Financial Integrity First" - No se puede vender lo que no se puede costear con precisión

---

## 🎯 Por Qué Este Orden Importa

El roadmap v2 asumía un flujo lineal: Inventario → Sales → Production → Finance.

**Problema Crítico Identificado:**
- ❌ No puedes calcular **comisiones reales** sin costos FIFO de producción
- ❌ No puedes implementar **Transfer Pricing** sin Production Service
- ❌ No puedes confiar en **entregas offline** sin criptografía Ed25519
- ❌ No puedes separar **P&L Fábrica vs Taproom** sin el "Financial Bridge"

**Nueva Filosofía:**
```
Seguridad → Bridge Financiero → Producción Real → Logística → Hospitalidad
   ↓              ↓                    ↓              ↓            ↓
 Ed25519    Transfer Pricing      FIFO Costing    PoD Crypto   Point of Sale
```

---

## ✅ COMPLETADO (Base Sólida)

### Sprints 1-2.5: Inventory Service v0.4.0
**Status:** 🟢 Production Ready

- ✅ FIFO automático con SQL locking
- ✅ Proveedores & Gases
- ✅ Keg Asset Management (10-state FSM)
- ✅ Cold Room Inventory (3 tipos)
- ✅ Temperature monitoring
- ✅ 39 endpoints, 95 tests, 13 modelos

**Gap Identificado:** No distingue HOUSE_BEER vs GUEST_BEER para Transfer Pricing

---

## ✅ FASE 1: El Puente Financiero (Sprints 3-3.5) - COMPLETA

> **Objetivo:** Antes de vender, saber quién gana el dinero

### Sprint 3: Security & B2B Foundations ✅
**Service:** Security Service (nuevo) + Sales Service (base)  
**Status:** 🟢 COMPLETADO

#### A. Device Enrollment Service (CRÍTICO) ✅
- [x] Modelo `DeviceEnrollment` con public_key Ed25519
- [x] Endpoint: `POST /api/v1/security/enroll`
- [x] Endpoint: `PATCH /api/v1/security/enrollments/{id}/approve`
- [x] Signature verification logic (PyNaCl)
- [x] 8 endpoints totales (enrollment, heartbeat, revoke, list)
- [x] 20+ tests

**Propósito:** ✅ Logrado - Identity trust for offline deliveries

#### B. Commission Structure (No Calculation Yet) ✅
- [x] Modelo `CommissionTier` (Platinum, Gold, Silver, Bronze)
- [x] Endpoint: `GET /api/v1/sales/commission-tiers`
- [x] Seed data con 4 tiers
- [x] 8+ tests

**Propósito:** ✅ Estructura definida, cálculo real en Sprint 6

#### C. Inventory Refactor: HOUSE vs GUEST ✅
- [x] Enum `OriginType` (HOUSE, GUEST, COMMERCIAL, MERCH)
- [x] Migration 007: Add `origin_type` column
- [x] Intelligent backfill logic
- [x] Indexes para Transfer Pricing queries
- [x] 10+ tests

**Propósito:** ✅ Habilita Transfer Pricing en Sprint 3.5

**Entregables:**
- ✅ 10 endpoints (Security + Sales)
- ✅ 38+ tests
- ✅ 1 migration crítica
- ✅ READMEs completos

---

### Sprint 3.5: "The Financial Bridge" ✅
**Service:** Finance Service (nuevo)  
**Status:** 🟢 COMPLETADO

#### A. Transfer Pricing Engine ✅
- [x] Modelo `TransferPricingRule`
  - [x] HOUSE → COST_PLUS (markup 15%)
  - [x] GUEST → PASSTHROUGH (markup 0%)
  - [x] COMMERCIAL → PASSTHROUGH (markup 0%)
  - [x] MERCHANDISE → FIXED_MARKUP (markup 25%)
- [x] TransferPricingEngine logic
- [x] Seed script con 4 reglas

#### B. Shadow Ledger (Internal Transfers) ✅
- [x] Modelo `InternalTransfer`
- [x] Endpoint: `POST /api/v1/finance/internal-transfers`
- [x] Endpoint: `GET /api/v1/finance/profit-center/{id}/summary`
- [x] Factory vs Taproom P&L segregation
- [x] 5 endpoints totales

**Propósito:** ✅ Logrado - Shadow ledger sin CFDI operacional

**Entregables:**
- ✅ 5 endpoints
- ✅ 20+ tests
- ✅ Profit Center P&L segregation operacional
- ✅ README con business logic

---

## 🏭 FASE 2: La Cocina Digital (Sprints 4-5)

> **Objetivo:** Costos reales, no estimados

### Sprint 4: Production Service (MES) Core ✅
**Status:** 🟢 COMPLETADO (Core + Sprint 4.5 Integrations)

#### A. BeerSmith + Manual Recipe Management ✅
- [x] XML Parser (.bsmx → Recipe model)
- [x] Endpoint: `POST /api/v1/production/recipes/import`
- [x] Endpoint: `POST /api/v1/production/recipes` (manual JSON creation)
- [x] Endpoint: `PATCH /api/v1/production/recipes/{id}` (update)
- [x] Parse: fermentables, hops, yeast, water, mash steps
- [x] Validated sub-schemas: `FermentableInput`, `HopInput`, `YeastInput`, `MashStepInput`
- [x] 6 recipe endpoints totales
- [x] Sample .bsmx fixture (American IPA)
- [x] 6 parser tests + 4 manual recipe tests

#### B. FIFO Cost Allocation ✅
- [x] BatchIngredientAllocation model
- [x] CostAllocator logic (mock data Sprint 4)
- [x] Cost breakdown: malt, hops, yeast, water, labor, overhead
- [x] Real StockBatch FIFO integration (Inventory Service HTTP)
- [x] Event bus `production.batch_started` (RabbitMQ)
- [x] Cost Management CRUD (IngredientPrice + FixedMonthlyCost + ProductionTarget)
- [x] Real overhead: $57,900/1,800L = $32.17/L (replaced hardcoded $80)

#### C. Batch State Machine ✅
- [x] 6 estados: PLANNED → BREWING → FERMENTING → CONDITIONING → PACKAGING → COMPLETED
- [x] Modelo `ProductionBatch` con cost tracking
- [x] BatchStateMachine con transition validation
- [x] 6 batch endpoints + 2 cost endpoints
- [x] 7 state machine tests

#### D. Sprint 4.5 Inter-Service Integration ✅
- [x] `InventoryServiceClient` — Real FIFO from StockBatch (HTTP)
- [x] `FinanceServiceClient` — InternalTransfer on batch completion (HTTP)
- [x] `EventPublisher` — RabbitMQ (production.batch_started, production.batch_completed)
- [x] FinishedProductInventory auto-created on batch completion
- [x] Mock dependency overrides for local testing

**Entregables Sprint 4 + 4.5:**
- ✅ 26 endpoints (6 recipe + 6 batch + 2 cost + 6 ingredients + 6 fixed costs)
- ✅ 53 tests
- ✅ Manual + BeerSmith recipe creation
- ✅ Inter-service integration operational
- ✅ Real FIFO cost allocation + real overhead ($32.17/L)

---

### Sprint 5: CMMS & Water Treatment (2 semanas)

#### A. Digital Twins de Equipos
- [ ] Modelo `Equipment` (runtime_hours tracking)
- [ ] Auto-trigger mantenimiento preventivo
- [ ] Maintenance Order management

#### B. Water Treatment Sub-Factory
- [ ] Modelo `WaterProductionRun`
- [ ] Costo del agua RO (cruda + energía + químicos + membranas)
- [ ] Validación: TDS <50ppm para batches

**Entregables:**
- 10 endpoints
- 20+ tests
- CMMS operacional

---

### Sprint 5.5: Sales Service Expansion ✅
**Service:** Sales Service v0.2.0  
**Status:** 🟢 COMPLETADO  
**Duración:** 1 semana

#### A. CRUD de Clientes ✅
- [x] Modelo `Client` (B2B/B2C/Distributor)
- [x] Double-Gate Credit Control (financial + asset limits)
- [x] 6 endpoints (CRUD + balance check)
- [x] 9 tests

#### B. Catálogo de Productos con Precios Duales ✅
- [x] Modelo `ProductCatalog` (fixed_price vs theoretical_price)
- [x] Modelo `PriceHistory` (audit trail)
- [x] `PricingEngine` logic (margin comparison)
- [x] Margin report endpoint (fixed vs theoretical side-by-side)
- [x] Per-channel pricing (Taproom, Distributor, On/Off Premise, E-commerce)
- [x] 8 endpoints + 9 tests

#### C. Notas de Venta (Sales Notes) ✅
- [x] Modelo `SalesNote` + `SalesNoteItem`
- [x] **`include_taxes` toggle** (IEPS/IVA empty when not invoiced)
- [x] PDF export (ReportLab) matching real Desert Brew Co. format
- [x] PNG export (Pillow)
- [x] Auto-numbering 8-digit (00000001...)
- [x] Lifecycle: DRAFT → CONFIRMED → CANCELLED
- [x] **Inventory deduction** on confirm (HTTP → Inventory Service)
- [x] 8 endpoints + 11 tests

#### D. Nómina Mejorada (Payroll + TipPool) ✅
- [x] Modelo `Employee` (FIXED/TEMPORARY)
- [x] **Cervecería:** 3 fijos, pago semanal estándar
- [x] **Taproom:** 3 fijos + temporales (pago diario), propinas, taxi
- [x] Modelo `TipPool` (distribución semanal Sun-Sat, división igualitaria)
- [x] Taxi allowance per shift
- [x] 9 endpoints + 15 tests

#### E. Inter-Service Integration ✅
- [x] `InventoryServiceClient` (HTTP client, async httpx)
- [x] Deducción de inventario producto terminado al confirmar nota
- [x] Feature flag: `ENABLE_INVENTORY_DEDUCTION`
- [x] Graceful degradation (nota se confirma aun si Inventory no responde)

**Entregables:**
- ✅ 33 endpoints (2 commission + 6 clients + 8 products + 8 notes + 9 payroll)
- ✅ 8 new models (Client, ProductCatalog, PriceHistory, SalesNote, SalesNoteItem, Employee, PayrollEntry, TipPool)
- ✅ 56 tests (all passing)
- ✅ PDF/PNG export operacional
- ✅ Inter-service integration con Inventory Service

---

## 📦 FASE 3: Logística y Experiencia (Sprints 6-7)

> **Objetivo:** Ahora que tenemos costos reales y seguridad, podemos vender

### Sprint 6: B2B Offline Logistics (2 semanas)

#### A. Proof of Delivery (PoD) Crypto
- [ ] Modelo `Delivery` con signature Ed25519
- [ ] Endpoint: `POST /api/v1/logistics/deliveries/submit`
- [ ] Signature verification + timestamp check

#### B. Async Commission Calculation
- [ ] RabbitMQ worker escucha `order.delivered`
- [ ] Calcula tier del vendedor (monthly volume)
- [ ] Crea `Commission` record

#### C. Logística Inversa (Kegs)
- [ ] Registrar kegs retornados en PoD
- [ ] Update customer keg balance
- [ ] Double-gate credit check

**Entregables:**
- 8 endpoints
- 15+ tests
- Commission calculation automático

---

### Sprint 7: Taproom POS (3 semanas)

#### A. Multi-Location Inventory
- [ ] Transfer COLD_ROOM → TAPROOM_BAR
- [ ] Endpoint: `POST /api/v1/taproom/stock-transfer`

#### B. Fractional Keg Consumption
- [ ] Modelo `TapLine` (current_volume tracking)
- [ ] Dead reckoning con factor 1.17x merma
- [ ] Smart blocking (keg <20%)

#### C. Mixed Basket Pricing
- [ ] HOUSE: transfer_price × 1.30 (taproom markup)
- [ ] GUEST: unit_cost × 1.50
- [ ] IEPS/IVA calculator

**Entregables:**
- 15 endpoints
- 12 Flutter screens
- 25+ tests

---

## 🧠 FASE 4: Antigravity Intelligence (Sprints 8+)

### Sprint 8: Auditoría Financiera Automática
- [ ] Dashboard: Factory Yield vs Taproom Margins
- [ ] Alertas: Inventory discrepancies
- [ ] Report: Days of Inventory (DOI)

### Sprint 9: IoT Telemetry (TimescaleDB)
- [ ] Sensor ingestion (temp, pH, °Brix)
- [ ] Fermentation alerts
- [ ] Grafana dashboards

---

## 📊 Timeline Actualizado

| Sprint | Módulo | Dependencias | Duración | Status |
|--------|--------|--------------|----------|--------|
| **S1-2.5** | Inventory v0.4.0 | - | - | ✅ Done |
| **S3** | Security & B2B Foundations | Inventory | 1 sprint | ✅ Done |
| **S3.5** | Financial Bridge | S3 | 1 sprint | ✅ Done |
| **S4** | Production MES Core | S3.5, Inventory | 1 sprint | ✅ Done |
| **S4.5** | Production Integrations | S4, S1, S3.5 | 1 sprint | 📋 Next |
| **S5** | CMMS & Water | S4 | 2 sem | 📋 Planned |
| **S6** | B2B Logistics | S3, S4 | 2 sem | 📋 Planned |
| **S7** | Taproom POS | S3.5, S6 | 3 sem | 📋 Planned |
| **S8** | Financial Audit | S3.5, S4 | 2 sem | 📋 Future |
| **S9** | IoT Telemetry | S4 | 2 sem | 📋 Future |

**Total Estimated:** ~6-7 meses

---

## 🎯 Justificación del Reorden

| Decisión | Razón (Del brief_readme.md) |
|----------|---------------------------|
| Sprint 3 primero (Security) | Sin Ed25519, no hay "no repudio" en entregas offline |
| Sprint 3.5 (Financial Bridge) | Sin Transfer Pricing, no puedes separar P&L Fábrica/Taproom |
| Sprint 4 antes que Sales | Sin costos reales de FIFO, las comisiones son inventadas |
| Sprint 5 (CMMS) antes que POS | Una falla de equipo puede botar un batch de $50k MXN |
| Sprint 6 (B2B) antes que Taproom | La distribución genera más volumen que retail |

---

**Última actualización:** 2026-02-03 18:40  
**Completado:** Fase 1 (Security + Finance) ✅ + Sprint 4 Core ✅  
**Próximo Sprint:** Sprint 4.5 (Production Integrations) o Sprint 5 (CMMS)

---

**Ver archivos complementarios:**
- [`sprint_3_security_plan.md`](file:///Users/ckph/.gemini/antigravity/brain/851ed79b-e31f-4077-962a-b3b8212d79b8/sprint_3_security_plan.md) - Implementation plan detallado
- [`project_status.md`](file:///Users/ckph/.gemini/antigravity/brain/851ed79b-e31f-4077-962a-b3b8212d79b8/project_status.md) - Estado actual del sistema
- [`brief_readme.md`](file:///Users/ckph/desert_brew_os/brief_readme.md) - Business model context
