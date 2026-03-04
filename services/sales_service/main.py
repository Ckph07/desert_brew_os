"""
Main FastAPI application for Sales Service.

Sprint 5.5: Clients, Products, Sales Notes, Commissions.
Payroll → extracted to Payroll Service (port 8006).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from sqlalchemy import inspect, text

from api.commission_routes import router as commission_router
from api.client_routes import router as client_router
from api.product_routes import router as product_router
from api.sales_note_routes import router as sales_note_router
from database import Base, engine
import models  # noqa: F401

app = FastAPI(
    title="Desert Brew Sales Service",
    description="Multi-channel Sales Management — Clients, Products, Notes, Commissions",
    version="0.3.0",
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
app.include_router(commission_router)
app.include_router(client_router)
app.include_router(product_router)
app.include_router(sales_note_router)

def _run_schema_compat_migrations() -> None:
    """
    Apply lightweight compatibility migrations for existing local databases.

    Current fixes:
    - add sales_notes.paid_at when missing.
    - add sales_notes.include_ieps / include_iva when missing.
    """
    inspector = inspect(engine)
    if "sales_notes" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("sales_notes")}
    with engine.begin() as conn:
        if "paid_at" not in columns:
            conn.execute(text("ALTER TABLE sales_notes ADD COLUMN paid_at TIMESTAMP NULL"))

        if "include_ieps" not in columns:
            conn.execute(text("ALTER TABLE sales_notes ADD COLUMN include_ieps BOOLEAN NOT NULL DEFAULT FALSE"))
            conn.execute(text("UPDATE sales_notes SET include_ieps = include_taxes WHERE include_taxes = TRUE"))

        if "include_iva" not in columns:
            conn.execute(text("ALTER TABLE sales_notes ADD COLUMN include_iva BOOLEAN NOT NULL DEFAULT FALSE"))
            conn.execute(text("UPDATE sales_notes SET include_iva = include_taxes WHERE include_taxes = TRUE"))


@app.on_event("startup")
def startup_event():
    """Ensure schema exists before serving requests."""
    Base.metadata.create_all(bind=engine)
    _run_schema_compat_migrations()


@app.get("/")
def root():
    return {
        "service": "Desert Brew Sales Service",
        "version": "0.3.0",
        "status": "operational",
        "modules": ["commissions", "clients", "products", "sales_notes"],
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
