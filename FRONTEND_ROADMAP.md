# Frontend Roadmap - Desert Brew OS

## Estado actual (2026-03-04)

Objetivo de este corte: estabilizar contratos reales de backend y cerrar P0+P1 de frontend en flujos criticos.

Referencia de cambios implementados:
- `docs/implementaciones_2026-03-04.md`

## Estado real por modulo

| Modulo | Estado | Entregado en este corte | Gaps actuales |
|---|---|---|---|
| Inventory | P0+P1 operativo | Stock dashboard y Receive Stock usando `/api/v1/inventory/stock`; mapping real de `StockBatch`; summary primario en `/api/v1/inventory/summary` con fallback a `/api/v1/inventory/stock/summary`; vista `Lotes/Insumos`; catalogo de insumos CRUD (`/inventory/ingredients`) conectado a selector en Receive Stock; payload de suppliers alineado (`contact_person`, `payment_terms`). | Falta migracion Alembic para `ingredient_catalog`; UX avanzada de Kegs/Cold Room pendiente. |
| Sales | P0+P1 operativo | Rutas `sales/*` alineadas; notas con `offset`; confirm/cancel por `PATCH`; nuevo pago `PATCH /api/v1/sales/notes/{id}/payment`; create note con `product_id + sku`; detalle de nota con export PDF/PNG; analytics liters-by-style activo. | Client detail sigue en placeholder; sharing/download de export en dispositivo (flujo nativo) queda para siguiente corte. |
| Production | P0+P1 operativo | Costos corregidos a `/ingredients`, `/costs/fixed`, `/costs/summary`; parser UI usa `monthly_amount`; `completeBatch(...)` implementado en repo/bloc/ui; recetas con CRUD + import BeerSmith (`.bsmx`) en frontend; editor manual/edicion de receta ahora soporta multiples fermentables, lupulos y levaduras con `sku`; reglas por estilo activas en formularios de receta y batch (validacion OG/FG/ABV/IBU + escala de volumen por estilo); reglas avanzadas por estilo activas (SRM + perfil de agua por ion), con sugerencia automatica de targets desde el formulario de receta; matching de estilo alineado a nombres BA para alias comunes; catálogo BA 2025 completo extraído a `data/ba_beer_styles_2025.json` desde el PDF oficial; transiciones de batch habilitadas para `conditioning`, `packaging` y `cancel`; validacion de insumos (`validate-stock`) desde frontend; `start-brewing` bloquea si la validacion de stock falla; snapshot inmutable de receta para costos de batch. | Fuente de reglas por estilo aun local en frontend; faltan perfiles dedicados para cubrir el 100% del catalogo BA en validación avanzada (hoy se mapea por alias a un subconjunto canónico) y exponer catalogo/versionado desde backend para evitar drift. |
| Finance | P1 operativo | CRUD completo de incomes y expenses (create/update/delete); dashboard enlaza a pricing rules, internal transfers y profit-center summary (lectura). | Edicion/alta de pricing rules e internal transfers aun no expuesta en UI. |
| Payroll | Fuera de corte | Estructura base y pantallas existentes. | Data layer completo + flujos operativos quedan para siguiente fase. |
| Security | Fuera de corte | Estructura base y device list existente. | Enrollment operativo, heartbeat y acciones administrativas quedan para siguiente fase. |

## Entregables cerrados (P0 + P1)

1. Sales contracts + endpoint de pago de nota.
2. Inventory contracts + stock mapping + summary derivado en frontend.
3. Production costos con rutas reales.
4. Complete batch end-to-end con integracion Production -> Inventory/Finance.
5. Finance CRUD de ingresos/egresos + navegacion de cards pendientes.
6. Sales note con lineas ligadas a catalogo (`product_id`) + detalle/export.
7. Documentacion de integracion y roadmap actualizados.
8. Catalogo de insumos (Inventory) con CRUD y seleccion desde Receive Stock.
9. Production recetas CRUD + import BeerSmith en frontend y flujo completo de estados `planned -> ... -> completed`.
10. Production recetas manuales/editables con multiples lineas de ingredientes y `sku`, mas bloqueo de inicio de lote cuando no hay stock suficiente.
11. Validaciones por estilo en formularios de Produccion: receta (OG/FG/ABV/IBU/SRM/perfil de agua) con sugerencia automatica de targets, y batch (escala de volumen + cumplimiento de objetivos de estilo).

## Calidad y validacion ejecutada

- Frontend:
  - `flutter analyze` sin errores de compilacion (solo lints informativos existentes).
  - Tests agregados y pasando:
    - `test/features/inventory/data/repositories/inventory_repository_impl_test.dart`
    - `test/features/production/presentation/bloc/batch/batch_bloc_test.dart`
    - `test/features/production/domain/entities/style_guidelines_test.dart`
- Backend:
  - `services/sales_service`: `41 passed`
  - `services/production_service`: `53 passed`
  - `services/inventory_service`: modulos nuevos compilando via `py_compile`.
  - Nota: tests de integracion con SQLite estan impactados por incompatibilidad preexistente de tipos `JSONB`.

## Backlog siguiente corte (P2)

1. Payroll y Security con data layer + casos operativos completos.
2. Client Detail de Sales (sin placeholder) con historial y estado de credito.
3. Eliminacion del fallback legacy de inventory summary cuando backend lo depreque oficialmente.
4. Migracion Alembic para `ingredient_catalog` y estrategia de tests sin bloqueo por `JSONB`.
5. Auth/RBAC y controles de permisos por modulo.
6. Offline/outbox y sync status transversal.
7. Externalizar reglas de estilo (rangos y targets de agua) a backend/configuracion central versionada.
