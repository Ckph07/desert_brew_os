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

## 🏗️ FASE 1: El Puente Financiero (Sprints 3-3.5)

> **Objetivo:** Antes de vender, saber quién gana el dinero

### Sprint 3: Security & B2B Foundations (2 semanas)
**Service:** Security Service (nuevo) + Sales Service (base)

#### A. Device Enrollment Service (CRÍTICO)
- [ ] Modelo `DeviceEnrollment` con public_key Ed25519
- [ ] Endpoint: `POST /api/v1/security/enroll`
- [ ] Endpoint: `PATCH /api/v1/security/enrollments/{id}/approve`
- [ ] Signature verification logic (nacl)

**Propósito:** Sin identity trust, las entregas offline no tienen "no repudio"

#### B. Commission Structure (No Calculation Yet)
- [ ] Modelo `CommissionTier` (Platinum, Gold, Silver, Bronze)
- [ ] Endpoint: `GET /api/v1/sales/commission-tiers`
- [ ] Endpoint: `GET /api/v1/sales/sellers/{id}/tier`

**Propósito:** Definir estructura antes de calcular comisiones reales

#### C. Inventory Refactor: HOUSE vs GUEST
- [ ] Enum `OriginType` (HOUSE, GUEST, COMMERCIAL, MERCH)
- [ ] Migration 007: Add `origin_type` column
- [ ] Backfill existing products
- [ ] Validators: HOUSE requires production_batch_id

**Propósito:** Habilitar Transfer Pricing en Sprint 3.5

**Entregables:**
- 8 endpoints (Security + Sales base)
- 15+ tests
- 1 migration crítica

---

### Sprint 3.5: "The Financial Bridge" (1 semana)
**Service:** Finance Service (nuevo)

#### A. Transfer Pricing Engine
- [ ] Modelo `TransferPricingRule`
  - HOUSE → COST_PLUS (markup 15%)
  - GUEST → PASSTHROUGH (markup 0%)
- [ ] Pricing Calculator logic

#### B. Shadow Ledger (Internal Transfers)
- [ ] Modelo `InternalTransfer`
- [ ] Endpoint: `POST /api/v1/finance/internal-transfer`
- [ ] View: `profit_center_summary`

**Propósito:** Registrar "ventas internas" Fábrica → Taproom sin facturas fiscales

**Entregables:**
- 6 endpoints
- 12+ tests
- Profit Center P&L segregation

---

## 🏭 FASE 2: La Cocina Digital (Sprints 4-5)

> **Objetivo:** Costos reales, no estimados

### Sprint 4: Production Service (MES) (3 semanas)

#### A. BeerSmith Integration
- [ ] XML Parser (.bsmx → Recipe model)
- [ ] Endpoint: `POST /api/v1/production/recipes/import-bsmx`

#### B. FIFO Cost Allocation
- [ ] Event: `production.batch_started`
- [ ] Inventory Service escucha y asigna FIFO layers
- [ ] Finance Service registra costo en `BatchLedger`

#### C. Batch State Machine
- [ ] Estados: PLANNED → MASHING → FERMENTING → PACKAGED
- [ ] Modelo `ProductionBatch` con cost tracking

**Entregables:**
- 12 endpoints
- 25+ tests
- Event-driven costing

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

## 📊 Nueva Tabla de Timeline

| Sprint | Módulo | Dependencias | Duración | Status |
|--------|--------|--------------|----------|--------|
| **S1-2.5** | Inventory v0.4.0 | - | - | ✅ Done |
| **S3** | Security & B2B Foundations | Inventory | 2 sem | 📋 Next |
| **S3.5** | Financial Bridge | S3 | 1 sem | 📋 Planned |
| **S4** | Production MES | S3.5, Inventory | 3 sem | 📋 Planned |
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

**Última actualización:** 2026-02-03  
**Aprobado por:** Análisis de Arquitectura Financiera  
**Próximo Sprint:** Sprint 3 - Security & B2B Foundations

---

**Ver archivos complementarios:**
- [`sprint_3_security_plan.md`](file:///Users/ckph/.gemini/antigravity/brain/851ed79b-e31f-4077-962a-b3b8212d79b8/sprint_3_security_plan.md) - Implementation plan detallado
- [`project_status.md`](file:///Users/ckph/.gemini/antigravity/brain/851ed79b-e31f-4077-962a-b3b8212d79b8/project_status.md) - Estado actual del sistema
- [`brief_readme.md`](file:///Users/ckph/desert_brew_os/brief_readme.md) - Business model context
