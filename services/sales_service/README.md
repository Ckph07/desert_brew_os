# Desert Brew Sales Service

Multi-channel sales management with commission tracking.

## Features (Sprint 3)

- **Commission Tiers**: Platinum/Gold/Silver/Bronze based on monthly volume
- **Tier Calculation**: Automatic tier assignment based on delivered liters
- **Retroactive Commission**: Rate applied retroactively when seller moves up

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/sales/commission-tiers` | Get all commission tiers |
| GET | `/api/v1/sales/sellers/{id}/tier` | Get seller's current tier |

## Commission Structure

| Tier | Min Monthly Liters | Rate (MXN/L) | Description |
|------|-------------------|--------------|-------------|
| **Platinum** | 500 L | $2.50 | Elite sellers |
| **Gold** | 200 L | $2.00 | High performers |
| **Silver** | 50 L | $1.50 | Standard |
| **Bronze** | 0 L | $1.00 | Entry level |

## Business Rules

1. **Commission calculated on DELIVERED liters** (PoD verified) - Sprint 6
2. **Tier based on current month cumulative volume**
3. **Retroactive application:** If seller reaches Platinum mid-month, entire month recalculated

## Installation

```bash
cd services/sales_service
pip install -r requirements.txt
python seed_commission_tiers.py  # Seed tiers
```

## Run

```bash
uvicorn main:app --reload --port 8002
```

## Database

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/desertbrew_sales"
```

## Sprint 3 Status

- [x] CommissionTier model
- [x] 2 API endpoints
- [x] Seed data script
- [ ] Actual commission calculation (Sprint 6 - after PoD)
- [ ] Tests (in progress)

**Version:** 0.1.0  
**Part of:** Sprint 3 - Security & B2B Foundations
