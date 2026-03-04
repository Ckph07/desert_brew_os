# Frontend Roadmap - Desert Brew OS

## Estado actual (2026-03-04)

Objetivo de este corte: cerrar F6 (Payroll + Security) y arrancar F7 (dashboard global + base offline) sobre contratos backend reales.

## Contratos backend verificados

| Servicio | Puerto | Endpoints útiles para frontend | Estado de integración frontend |
|---|---:|---:|---|
| Inventory | 8001 | 39 | Operativo (F1/F2) + usado por Dashboard global |
| Sales | 8002 | 24+ | Operativo (F3/F3+) + usado por Dashboard global |
| Production | 8004 | 26 | Operativo (F4) + usado por Dashboard global |
| Finance | 8005 | 19 | Operativo (F5) |
| Payroll | 8006 | 11 | Operativo (F6): empleados, entries, tip-pools |
| Security | 8003 | 7 (+root/health) | Operativo (F6): enrollment, approve/revoke, heartbeat, stats |

Nota backend aplicada en este corte:
- `services/security_service/api/enrollment_routes.py`: import de `timedelta` corregido para `/api/v1/security/enrollments/stats`.

## Estado real por módulo

| Modulo | Estado | Entregado en este corte | Gaps actuales |
|---|---|---|---|
| Inventory | P0+P1 operativo | Stock dashboard, Receive Stock, ingredientes, suppliers, kegs, finished products. | UX avanzada de kegs/cold room y mejoras de performance de listados grandes. |
| Sales | P0+P1 operativo | Notas de venta con confirm/cancel/payment, analytics litros por estilo, detalle/export. | Client detail sigue en placeholder. |
| Production | P0+P1 operativo | Recetas CRUD/import, batches FSM, costos FIFO, validación de stock por receta. | Externalizar reglas de estilo al backend para evitar drift local. |
| Finance | P1 operativo | CRUD incomes/expenses, balance/cashflow, vistas de pricing rules/internal transfers/profit summary. | Alta/edición de pricing rules e internal transfers aún no expuesta. |
| Payroll | P0+P1 operativo | `/payroll`: lista real de empleados + entradas de nómina + alta de empleado + alta de entry + marcar pagado. `/payroll/tip-pool`: lista y creación de tip pools con participantes. | Edición de empleado y reportes de nómina consolidados pendientes. |
| Security | P0+P1 operativo | `/security`: listado real de dispositivos, filtros por estado, stats, enrollment, approve/revoke, heartbeat. | RBAC real de acciones admin y flujo de asignación de admin_user_id desde auth. |
| Dashboard global + Offline | F7 base operativa | Home dashboard con KPIs reales multi-servicio + fallback a snapshot en memoria + estado online/offline + contador outbox + flush manual. | Persistencia offline (Isar) para snapshot/outbox aún pendiente; cola sigue in-memory. |

## Entregables cerrados en este corte

1. Data layer completo de Payroll (datasource + repo + modelos + entidades).
2. UI operativa de Payroll (empleados, payroll entries, tip pools).
3. Data layer completo de Security (datasource + repo + modelos + entidades).
4. UI operativa de Security (enrollment + lifecycle admin + stats).
5. Dashboard global con KPIs reales (Inventory, Production, Sales, Payroll, Security).
6. Integración offline base en frontend con `SyncManager` + outbox reactivo.
7. Ruta de payroll alineada: `/payroll/tip-pool` (con compatibilidad legacy `/payroll/tips` → redirect).
8. Corrección backend en endpoint de stats de Security.

## Calidad y validación esperada

- Frontend:
  - `flutter analyze` sin errores de compilación.
  - Validar manualmente rutas nuevas:
    - `/payroll`
    - `/payroll/tip-pool`
    - `/security`
    - `/` (dashboard global + offline indicators)
- Backend:
  - Confirmar `/api/v1/security/enrollments/stats` respondiendo sin `NameError`.

## Backlog siguiente corte (P2)

1. Persistencia offline real (Isar) para outbox y snapshots de dashboard.
2. RBAC/Auth para acciones sensibles de Security y Payroll.
3. Reportes consolidados de nómina (semanal/quincenal/mensual + export).
4. Client Detail completo en Sales (sin placeholder).
5. Alta/edición de pricing rules e internal transfers en Finance.
6. Telemetría de sync: latencia de cola, reintentos y fallas por endpoint.
