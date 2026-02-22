# Desert Brew OS - Executive Summary v3.5

**Date:** 2026-02-22  
**Architecture:** 6 Microservices, Layered by Financial Integrity

---

## 🎯 System Architecture

```
Inventory (8001)  ←→  Production (8004)  ←→  Finance (8005)
     ↑                     ↑
     └─── Sales (8002) ────┘      Security (8003)    Payroll (8006)

Flow: Recipe → Batch → FIFO Cost → Finished Product → Sales Note → Inventory Deduct
```

---

## ✅ Current State

| Service | Port | Endpoints | Tests | Status |
|---------|------|-----------|-------|--------|
| Inventory | 8001 | 39 | 95 | 🟢 |
| Sales | 8002 | 24 | 41 | 🟢 |
| Security | 8003 | 8 | 20+ | 🟢 |
| Production | 8004 | 24 | 37+ | 🟢 |
| Finance | 8005 | 5 | 20+ | 🟢 |
| Payroll | 8006 | 11 | 21 | 🟢 |
| **Total** | — | **111** | **234+** | — |

### Key Capabilities
- ✅ FIFO automatic with SQL locking (raw materials)
- ✅ Keg Asset Management (10-state FSM, QR/RFID)
- ✅ BeerSmith recipe import (.bsmx XML)
- ✅ Production batch lifecycle (6 states)
- ✅ Transfer Pricing (HOUSE +15%, GUEST 0%, MERCH +25%)
- ✅ P&L segregation (Factory vs Taproom)
- ✅ Ed25519 device enrollment + signature verification
- ✅ Client CRUD with Double-Gate Credit Control
- ✅ Dual Pricing (fixed vs theoretical) with margin reports
- ✅ Sales Notes with PDF/PNG export + inventory deduction
- ✅ Payroll: brewery fixed + taproom (fixed/temps, tip pool, taxi)
- ✅ **NEW:** Ingredient price CRUD (reference pricing)
- ✅ **NEW:** Fixed monthly cost CRUD ($57,900 → $32.17/L)
- ✅ **NEW:** CostAllocator uses real overhead instead of hardcoded values

---

## 🚀 Next Steps

| Sprint | Focus | Key Deliverables |
|--------|-------|-----------------|
| 5 | CMMS & Water | Equipment maintenance, water RO costing |
| 6 | B2B Logistics | PoD crypto, commission calculation, keg returns |
| 7 | Taproom POS | Point of sale, IEPS/IVA, keg consumption |

---

**Details:** [`ROADMAP_v3.md`](file:///Users/ckph/desert_brew_os/ROADMAP_v3.md)
