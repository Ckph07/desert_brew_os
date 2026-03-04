# Runbook de Integracion - Desert Brew OS

## Objetivo

Este runbook documenta el estado real de integracion entre frontend Flutter y microservicios (backend como fuente de verdad), incluyendo contratos vigentes de P0+P1.

Complemento de detalle del corte:
- `docs/implementaciones_2026-03-04.md`

## Topologia (docker compose)

- Infra: `postgres` (inventario/finanzas/ventas/seguridad/nomina), `timescaledb` (produccion), `redis`, `rabbitmq`.
- APIs: `inventory` (8001), `sales` (8002), `security` (8003), `production` (8004), `finance` (8005), `payroll` (8006).
- Worker async: `finance_event_consumer` (consume `production_events`).
- Frontend: Flutter Web en `3000`.
- Red: `desertbrew_network`.

## Arranque local

1. Limpiar stack previo (si hubo cambios de init):
   - `docker compose down`
2. Levantar todo el stack:
   - `docker compose up -d --build --remove-orphans`
3. Levantar flujo de desarrollo completo:
   - `./dev_launcher.sh --all`
4. Solo frontend (si necesitas rebuild web):
   - `FLUTTER_CLEAN=1 ./dev_launcher.sh --frontend-only`

## Contratos frontend vigentes

### Sales Service (8002)

- Clientes:
  - `GET /api/v1/sales/clients`
  - `GET /api/v1/sales/clients/{id}`
  - `POST /api/v1/sales/clients`
  - `PATCH /api/v1/sales/clients/{id}`
- Productos:
  - `GET /api/v1/sales/products`
  - `GET /api/v1/sales/products/{id}`
  - `GET /api/v1/sales/products/margin-report`
- Notas:
  - `GET /api/v1/sales/notes?offset=&limit=`
  - `GET /api/v1/sales/notes/{id}`
  - `POST /api/v1/sales/notes`
  - `PATCH /api/v1/sales/notes/{id}/confirm`
  - `PATCH /api/v1/sales/notes/{id}/cancel`
  - `PATCH /api/v1/sales/notes/{id}/payment` (nuevo)
    - body: `{ "payment_status": "PAID|PENDING|PARTIAL|OVERDUE" }`
  - `GET /api/v1/sales/notes/{id}/export/pdf`
  - `GET /api/v1/sales/notes/{id}/export/png`
- Analytics:
  - `GET /api/v1/sales/notes/analytics/liters-by-style`

### Inventory Service (8001)

- Stock:
  - `GET /api/v1/inventory/stock`
  - `POST /api/v1/inventory/stock`
  - `GET /api/v1/inventory/summary` (primario en frontend)
  - `GET /api/v1/inventory/stock/summary` (fallback temporal)
- Catalogo de insumos (nuevo):
  - `GET /api/v1/inventory/ingredients`
  - `GET /api/v1/inventory/ingredients/{id}`
  - `POST /api/v1/inventory/ingredients`
  - `PATCH /api/v1/inventory/ingredients/{id}`
  - `DELETE /api/v1/inventory/ingredients/{id}` (soft-delete)
- Suppliers:
  - `GET /api/v1/suppliers`
  - `GET /api/v1/suppliers/{id}`
  - `POST /api/v1/suppliers`
  - `PATCH /api/v1/suppliers/{id}`
- Kegs / Finished:
  - `GET /api/v1/inventory/kegs`
  - `PATCH /api/v1/inventory/kegs/{keg_id}/transition`
  - `GET /api/v1/inventory/finished-products`
  - `GET /api/v1/inventory/finished-products/summary`

Notas de mapping en frontend:
- `ingredientName <- sku`
- `quantity <- initial_quantity`
- `unit <- unit_measure`
- `receivedAt <- arrival_date`
- `expiryDate <- expiration_date`
- `supplierName <- provider_name`

Notas de UX/frontend:
- Ruta catalogo de insumos: `/inventory/ingredients`
- `Recibir Stock` permite:
  - seleccionar insumo catalogado (autocompleta `sku/categoria/unidad`)
  - captura manual si no existe insumo en catalogo

### Production Service (8004)

- Recetas:
  - `POST /api/v1/production/recipes`
  - `POST /api/v1/production/recipes/import`
  - `GET /api/v1/production/recipes`
  - `GET /api/v1/production/recipes/{id}`
  - `PATCH /api/v1/production/recipes/{id}`
  - `DELETE /api/v1/production/recipes/{id}`
  - `POST /api/v1/production/recipes/{id}/validate-stock`
- Batches:
  - `GET /api/v1/production/batches`
  - `GET /api/v1/production/batches/{id}`
  - `POST /api/v1/production/batches`
  - `PATCH /api/v1/production/batches/{id}/start-brewing`
  - `PATCH /api/v1/production/batches/{id}/start-fermenting`
  - `PATCH /api/v1/production/batches/{id}/start-conditioning`
  - `PATCH /api/v1/production/batches/{id}/start-packaging`
  - `PATCH /api/v1/production/batches/{id}/cancel`
  - `PATCH /api/v1/production/batches/{id}/complete`
- Costos:
  - `GET /api/v1/production/ingredients`
  - `GET /api/v1/production/costs/fixed`
  - `GET /api/v1/production/costs/summary`

Notas de dominio (production):
- Fuente de estilos de referencia operativa: `data/ba_beer_styles_2025.json` (extraído de `data/2025_BA_Beer_Style_Guidelines.pdf`).
- Script de extracción reproducible: `scripts/extract_ba_styles_2025.py`.
- Cada `ProductionBatch` captura `recipe_snapshot` al crearse.
- La asignacion FIFO en `start-brewing` usa snapshot inmutable (si existe) para evitar drift cuando se edita la receta fuente.
- Ingredientes de receta soportan `sku` (fermentables/hops/yeast). Si no se envia, backend normaliza desde `name`.
- Payload de receta ya contempla `color_srm` y `water_profile` (mapa de iones) para reglas avanzadas por estilo.
- Levadura soporta `amount_packets` (default `1.0`) para validacion y consumo.
- `start-brewing` ejecuta preflight de stock completo antes de consumir (evita consumo parcial por faltante de un ingrediente posterior).
- Frontend aplica reglas por estilo en formularios:
  - el catálogo de estilos se carga en runtime desde `assets/data/ba_beer_styles_2025.json` al iniciar la app (`main.dart`), con fallback local canónico si el asset falla.
  - receta: valida `OG/FG/ABV/IBU/SRM` y `water_profile` (ca/mg/na/cl/so4/hco3) contra rangos del estilo reconocido.
  - receta: permite `Aplicar Targets Sugeridos` para autocompletar OG/FG/ABV/IBU/SRM/perfil de agua desde el target recomendado del estilo.
  - batch: valida escala de volumen por estilo y tambien bloquea cuando la receta vinculada incumple objetivos de estilo (incluyendo SRM/agua) o tiene metricas avanzadas faltantes.
  - matching de estilos prioriza alias especificos (ej. `Hazy IPA` sobre alias generico `IPA`) para evitar recomendaciones incorrectas.
  - el matching incluye nombres BA (ej. `American-Style India Pale Ale`, `Juicy or Hazy India Pale Ale`) y mantiene alias operativos (`Hazy IPA`, `West Coast IPA`, `APA`, etc.) sobre el catálogo cargado.

### Finance Service (8005)

- Incomes:
  - `GET /api/v1/finance/incomes`
  - `POST /api/v1/finance/incomes`
  - `PATCH /api/v1/finance/incomes/{id}`
  - `DELETE /api/v1/finance/incomes/{id}`
  - `GET /api/v1/finance/incomes/summary`
- Expenses:
  - `GET /api/v1/finance/expenses`
  - `POST /api/v1/finance/expenses`
  - `PATCH /api/v1/finance/expenses/{id}`
  - `DELETE /api/v1/finance/expenses/{id}`
  - `GET /api/v1/finance/expenses/summary`
- Dashboard auxiliar:
  - `GET /api/v1/finance/balance`
  - `GET /api/v1/finance/cashflow`
  - `GET /api/v1/finance/pricing-rules`
  - `GET /api/v1/finance/internal-transfers`
  - `GET /api/v1/finance/profit-center/{profit_center}/summary`

## Contratos internos entre microservicios

- Production -> Inventory:
  - `PATCH /api/v1/inventory/stock-batches/{id}/consume`
  - `quantity`, `unit`, `reason` se envian como query params.
- Production -> Inventory (producto terminado):
  - `POST /api/v1/inventory/finished-products`
  - payload vigente incluye: `product_type=OWN_PRODUCTION`, `category=BEER_KEG`, `production_batch_id`, `quantity`, `unit_measure=LITERS`, `cold_room_id=COLD_ROOM_A`, `unit_cost`, `sku`, `product_name`, `notes`.
- Production -> Finance:
  - `POST /api/v1/finance/internal-transfers`

## Smoke checks recomendados

1. Salud de APIs:
   - `curl http://localhost:8001/health`
   - `curl http://localhost:8002/health`
   - `curl http://localhost:8004/health`
   - `curl http://localhost:8005/health`
2. Navegacion critica frontend:
   - `/inventory`
   - `/inventory/ingredients`
   - `/inventory/receive`
   - `/sales/notes`
   - `/production/batches/:id`
   - `/finance/income`
   - `/finance/expenses`
3. Flujos funcionales:
   - Crear, confirmar y marcar pagada una nota.
   - Recibir stock desde formulario.
   - Crear insumo en catalogo y recibir stock seleccionandolo.
   - Crear/editar/eliminar receta e importar `.bsmx` desde frontend.
   - En receta manual por estilo, usar `Aplicar Targets Sugeridos` y validar guardado con SRM/perfil de agua.
   - Mover batch por `fermenting -> conditioning -> packaging -> complete`.
   - Cargar costos de produccion.
   - Completar batch.
   - Crear/editar/eliminar ingreso y egreso.

## Notas de pruebas conocidas

- En `inventory_service`, los tests de integracion que usan SQLite pueden fallar por incompatibilidad preexistente con columnas `JSONB` de tablas compartidas de metadata.
- Para validar cambios de este corte:
  - usar smoke tests funcionales via frontend
  - usar compilacion de modulos Python (`py_compile`) para chequeo rapido de sintaxis

## Nota de legado

- `infra/mongodb/init.js` se considera legado y no se usa en el `docker-compose` actual.
