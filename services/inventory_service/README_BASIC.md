# Desert Brew OS - Inventory Service

Servicio de gestión de inventario con FIFO automático.

## Funcionalidades

- ✅ CRUD de lotes de materia prima
- ✅ Asignación automática FIFO (First-In, First-Out)
- ✅ Trazabilidad completa
- ✅ Locking pesimista para evitar race conditions

## Instalación

```bash
cd services/inventory_service
pip install -r requirements.txt
```

## Configuración

Asegúrate de tener PostgreSQL ejecutándose. Luego copia `.env.template`:

```bash
cp ../../.env.template .env
```

## Ejecutar

```bash
uvicorn main:app --reload --port 8001
```

## Endpoints

### POST /api/v1/inventory/stock
Recibir nueva materia prima

### GET /api/v1/inventory/stock/{sku}
Consultar stock de un SKU

### POST /api/v1/inventory/allocate
Asignar stock usando FIFO

## Testing

Ver `/Users/ckph/desert_brew_os/services/inventory_service/README.md` para ejemplos de testing.
