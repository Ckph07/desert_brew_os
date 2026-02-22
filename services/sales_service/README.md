# Desert Brew Sales Service v0.3.0

Multi-channel Sales Management for Desert Brew Co.

**Port:** 8002  
**Payroll:** Extracted to [Payroll Service](../payroll_service/) (port 8006)

## Architecture

```
Sales Service (8002) ←→ Inventory Service (8001)
                          ↓ (deduct finished product on note confirm)
```

## API Endpoints (24 total)

### Commissions (2)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/sales/commission-tiers` | List tiers |
| GET | `/api/v1/sales/sellers/{id}/tier` | Seller's current tier |

### Clients (6)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/sales/clients` | Create client |
| GET | `/api/v1/sales/clients` | List (filters: type, tier, search) |
| GET | `/api/v1/sales/clients/{id}` | Get client |
| PATCH | `/api/v1/sales/clients/{id}` | Update |
| DELETE | `/api/v1/sales/clients/{id}` | Soft-delete |
| GET | `/api/v1/sales/clients/{id}/balance` | Credit + keg status |

### Products (8)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/sales/products` | Create product |
| GET | `/api/v1/sales/products` | List products |
| GET | `/api/v1/sales/products/margin-report` | Fixed vs Theoretical margins |
| GET | `/api/v1/sales/products/{id}` | Get with margins |
| PATCH | `/api/v1/sales/products/{id}` | Update |
| DELETE | `/api/v1/sales/products/{id}` | Soft-delete |
| PATCH | `/api/v1/sales/products/{id}/prices` | Update channel prices |
| GET | `/api/v1/sales/products/{id}/price-history` | Audit trail |

### Sales Notes (8)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/sales/notes` | Create note with items |
| GET | `/api/v1/sales/notes` | List (filters: client, status, channel) |
| GET | `/api/v1/sales/notes/{id}` | Get with items |
| PATCH | `/api/v1/sales/notes/{id}` | Update DRAFT |
| PATCH | `/api/v1/sales/notes/{id}/confirm` | **Confirm + deduct inventory** |
| PATCH | `/api/v1/sales/notes/{id}/cancel` | Cancel |
| GET | `/api/v1/sales/notes/{id}/export/pdf` | PDF export |
| GET | `/api/v1/sales/notes/{id}/export/png` | PNG export |

## Running

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8002

# With inventory deduction
ENABLE_INVENTORY_DEDUCTION=true uvicorn main:app --reload --port 8002
```

## Testing

```bash
python -m pytest tests/ -v
# 41 tests, ~1s
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql://...localhost:5432/desertbrew_sales | PostgreSQL |
| INVENTORY_SERVICE_URL | http://localhost:8001 | Inventory Service |
| ENABLE_INVENTORY_DEDUCTION | false | Stock deduction on confirm |
