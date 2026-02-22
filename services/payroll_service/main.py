"""
Main FastAPI application for Payroll Service.

Manages employee records, payroll entries, and tip pool distributions
for both Cervecería (Brewery) and Taproom departments.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.employee_routes import router as employee_router
from api.payroll_routes import router as payroll_router
from api.tip_pool_routes import router as tip_pool_router

app = FastAPI(
    title="Desert Brew Payroll Service",
    description="Employee & Payroll Management — Brewery (fixed) + Taproom (fixed/temps, tips, taxi)",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(employee_router)
app.include_router(payroll_router)
app.include_router(tip_pool_router)


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
