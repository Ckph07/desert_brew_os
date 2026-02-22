"""
Main FastAPI application for Sales Service.

Sprint 5.5: Clients, Products, Sales Notes, Commissions.
Payroll → extracted to Payroll Service (port 8006).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.commission_routes import router as commission_router
from api.client_routes import router as client_router
from api.product_routes import router as product_router
from api.sales_note_routes import router as sales_note_router

app = FastAPI(
    title="Desert Brew Sales Service",
    description="Multi-channel Sales Management — Clients, Products, Notes, Commissions",
    version="0.3.0",
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
app.include_router(commission_router)
app.include_router(client_router)
app.include_router(product_router)
app.include_router(sales_note_router)


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
