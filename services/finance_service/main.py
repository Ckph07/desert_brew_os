"""
Main FastAPI application for Finance Service.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from api.finance_routes import router as finance_router
from api.income_routes import router as income_router
from api.expense_routes import router as expense_router
from database import Base, engine
import models  # noqa: F401

app = FastAPI(
    title="Desert Brew Finance Service",
    description="Transfer Pricing, Income/Expense Tracking & Balance Sheet",
    version="0.2.0"
)

def _get_allowed_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS")
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(finance_router)
app.include_router(income_router)
app.include_router(expense_router)


@app.on_event("startup")
def startup_event():
    """Ensure schema exists before serving requests."""
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "service": "Desert Brew Finance Service",
        "version": "0.2.0",
        "status": "operational",
        "modules": {
            "transfer_pricing": "/api/v1/finance/pricing-rules",
            "internal_transfers": "/api/v1/finance/internal-transfers",
            "incomes": "/api/v1/finance/incomes",
            "expenses": "/api/v1/finance/expenses",
            "balance": "/api/v1/finance/balance",
            "cashflow": "/api/v1/finance/cashflow",
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
