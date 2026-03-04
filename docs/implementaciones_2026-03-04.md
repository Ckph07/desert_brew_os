# Implementaciones P0+P1 - Corte 2026-03-04

## Alcance del corte

Este documento resume los cambios implementados en frontend y backend para estabilizar contratos entre microservicios y habilitar flujos criticos de operacion.

## Frontend

### Inventory

- Contratos de stock alineados a backend real:
  - `GET /api/v1/inventory/stock`
  - `POST /api/v1/inventory/stock`
- Ajuste de summary para evitar 404 repetidos:
  - primary: `GET /api/v1/inventory/summary`
  - fallback: `GET /api/v1/inventory/stock/summary`
- Mapping de `StockBatch` alineado a schema real:
  - `ingredientName <- sku`
  - `quantity <- initial_quantity`
  - `unit <- unit_measure`
  - `receivedAt <- arrival_date`
  - `expiryDate <- expiration_date`
  - `supplierName <- provider_name`
- Dashboard de inventario con doble vista:
  - `Lotes`
  - `Insumos` (agregado por SKU/categoria/unidad)
- Filtros de categoria extendidos (`CAP`, `LABEL`).
- Acceso rapido desde home a `Recibir Stock`.

### Inventory - Catalogo de Insumos (nuevo)

- Nueva ruta frontend:
  - `/inventory/ingredients`
- Nueva pantalla:
  - Catalogo de insumos con CRUD (create, list/search, update, soft-delete)
- Integracion de catalogo en `Recibir Stock`:
  - Selector de insumo
  - Autocompletado de `SKU`, `categoria`, `unidad`
  - Soporte de captura manual cuando no hay insumo catalogado

### Sales

- Rutas de frontend alineadas a backend:
  - `/api/v1/sales/clients`
  - `/api/v1/sales/products`
  - `/api/v1/sales/notes`
- Listado de notas usa `offset`/`limit`.
- Confirmar/cancelar nota por `PATCH`.
- Flujo de pago de nota integrado (`PATCH /payment`).
- Nota de venta con lineas asociadas a catalogo (`product_id + sku`).
- Detalle de nota con export PDF/PNG.

### Production

- Costos alineados a rutas reales:
  - `/api/v1/production/ingredients`
  - `/api/v1/production/costs/fixed`
  - `/api/v1/production/costs/summary`
- Parser frontend ajustado a `monthly_amount`.
- Flujo de `Completar Batch` integrado en repo/bloc/ui.
- Ruta de detalle de receta funcional:
  - `/production/recipes/:id`
- CRUD frontend de recetas habilitado:
  - crear manual
  - editar receta completa (metadata + ingredientes)
  - eliminar
  - importar `.bsmx` desde UI
- Editor de recetas manuales ahora permite:
  - multiples fermentables
  - multiples lupulos
  - multiples levaduras
  - captura de `sku` por ingrediente
  - `amount_packets` para levadura
- Reglas por estilo en formulario de receta:
  - matching por estilo (IPA, Blonde, Lager, Stout, etc.)
  - validacion de objetivos `OG/FG/ABV/IBU` contra rangos BJCP-like configurados
  - bloqueo de guardado cuando receta queda fuera de rango del estilo reconocido
- Flujo de estados de batch completado en frontend:
  - `planned -> brewing -> fermenting -> conditioning -> packaging -> completed`
  - soporte para salto `fermenting -> packaging`
- Validacion previa de inventario desde detalle de batch (`validate-stock`) con desglose por insumo.
- `start-brewing` en frontend exige validacion de stock positiva antes de ejecutar transicion.
- Accion de cancelar batch desde frontend (con motivo opcional).
- Reglas por estilo en formulario de batch:
  - valida que la receta seleccionada tenga objetivos de estilo completos
  - valida que la receta no este fuera de rango del estilo
  - valida escala de volumen planeado contra rango permitido por estilo

### Finance

- CRUD operativo para:
  - Ingresos (`incomes`)
  - Egresos (`expenses`)
- Dashboard financiero conecta a:
  - pricing rules (lectura)
  - internal transfers (lectura)
  - profit-center summary (lectura)

## Backend

### Sales Service

- Nuevo endpoint:
  - `PATCH /api/v1/sales/notes/{note_id}/payment`
- Reglas:
  - solo notas `CONFIRMED`
  - rechaza `CANCELLED`
  - al marcar `PAID`, registra timestamp de pago

### Production Service

- Correccion de cliente interno hacia inventory:
  - `consume_stock` envia `quantity`, `unit`, `reason` como query params
- Correccion de payload para crear producto terminado en inventory:
  - `product_type=OWN_PRODUCTION`
  - `category=BEER_KEG`
  - `production_batch_id`
  - `quantity=actual_volume_liters`
  - `unit_measure=LITERS`
  - `cold_room_id=COLD_ROOM_A`
  - `unit_cost`, `sku`, `product_name`, `notes`
- Nuevos endpoints de transicion de batch:
  - `PATCH /api/v1/production/batches/{id}/start-conditioning`
  - `PATCH /api/v1/production/batches/{id}/start-packaging`
  - `PATCH /api/v1/production/batches/{id}/cancel`
- Nuevo endpoint de reconciliacion receta -> inventario:
  - `POST /api/v1/production/recipes/{id}/validate-stock`
- Snapshot inmutable de receta por batch:
  - `production_batches.recipe_snapshot` se captura al crear batch
  - `start-brewing` usa snapshot para asignacion FIFO (evita drift por ediciones posteriores de receta)
- Contrato de ingredientes de receta extendido con `sku` opcional; backend normaliza SKU desde nombre cuando no viene informado.
- Contrato de levadura extendido con `amount_packets` (default `1.0`) para validacion/consumo real.
- `CostAllocator` con estrategia preflight:
  - valida disponibilidad de **todos** los insumos antes de consumir
  - evita consumos parciales cuando un ingrediente posterior falla por stock insuficiente

### Inventory Service - Catalogo de Insumos (nuevo)

- Nuevo recurso de catalogo:
  - `POST /api/v1/inventory/ingredients`
  - `GET /api/v1/inventory/ingredients`
  - `GET /api/v1/inventory/ingredients/{id}`
  - `PATCH /api/v1/inventory/ingredients/{id}`
  - `DELETE /api/v1/inventory/ingredients/{id}` (soft-delete)
- Nuevo modelo ORM: `ingredient_catalog`
- Nuevos schemas Pydantic para create/update/response
- Registro de router en `main.py`

## Validacion ejecutada

- Frontend:
  - `flutter analyze` sin errores de compilacion (lints informativos existentes).
  - `flutter test test/features/inventory/data/repositories/inventory_repository_impl_test.dart test/features/production/presentation/bloc/batch/batch_bloc_test.dart` pasando.
  - `flutter test test/features/production/domain/entities/style_guidelines_test.dart` pasando.
- Backend:
  - Compilacion de modulos Python nuevos de inventory (`py_compile`) sin errores.
  - `services/production_service`: `pytest tests/integration/test_production_api.py` pasando (20 tests, incluye transitions + cancel + validate-stock + preflight anti consumo parcial).
  - Nota de entorno de pruebas: los tests de integracion con SQLite fallan por incompatibilidad preexistente de tipos `JSONB` en metadatos compartidos.

## Pendientes tecnicos conocidos

1. Migracion Alembic formal para `ingredient_catalog` (actualmente se crea via `Base.metadata.create_all`).
2. Ajustar strategy de pruebas de `inventory_service` para evitar dependencia de SQLite en tablas con `JSONB`.
3. Exponer en frontend acciones avanzadas para pricing rules e internal transfers (actualmente lectura).
4. Completar Client Detail en Sales (hoy en placeholder).
5. Mitigar fallas parciales por errores de red durante consumo FIFO con estrategia de compensacion/reserva en Inventory Service (siguiente fase).
