"""
Main FastAPI application for Payroll Service.

Manages employee records, payroll entries, and tip pool distributions
for both Cervecería (Brewery) and Taproom departments.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from api.employee_routes import router as employee_router
from api.payroll_routes import router as payroll_router
from api.tip_pool_routes import router as tip_pool_router
from database import Base, engine
from models.employee import Employee, PayrollEntry, TipPool  # noqa: F401

app = FastAPI(
    title="Desert Brew Payroll Service",
    description="Employee & Payroll Management — Brewery (fixed) + Taproom (fixed/temps, tips, taxi)",
    version="0.1.0",
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
app.include_router(employee_router)
app.include_router(payroll_router)
app.include_router(tip_pool_router)


@app.on_event("startup")
def startup_event():
    """Ensure schema exists before serving requests."""
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "service": "Desert Brew Payroll Service",
        "version": "0.1.0",
        "status": "operational",
        "modules": ["employees", "payroll", "tip_pools"],
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
