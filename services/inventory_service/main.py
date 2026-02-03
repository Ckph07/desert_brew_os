"""
Main FastAPI application for Inventory Service.

Port: 8001
Database: PostgreSQL
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Desert Brew OS - Inventory Service",
    description="Gestión de inventario con FIFO automático y trazabilidad",
    version="0.4.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configurar origins en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database tables created")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "inventory_service",
        "version": "0.4.0"
   }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Desert Brew OS - Inventory Service",
        "version": "0.4.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "stock": "/api/v1/inventory/stock",
            "transfers": "/api/v1/inventory/transfer",
            "movements": "/api/v1/inventory/movements",
            "suppliers": "/api/v1/suppliers",
            "gas_tanks": "/api/v1/inventory/gas-tanks",
            "kegs": "/api/v1/inventory/kegs",
            "finished_products": "/api/v1/inventory/finished-products",
            "cold_room": "/api/v1/inventory/cold-room"
        }
    }


# Include API routers
from api import stock_routes, movement_routes, supplier_routes, gas_routes, keg_routes, finished_product_routes

app.include_router(
    stock_routes.router,
    prefix="/api/v1/inventory",
    tags=["stock"]
)

app.include_router(
    movement_routes.router,
    prefix="/api/v1/inventory",
    tags=["movements", "transfers"]
)

app.include_router(
    supplier_routes.router,
    prefix="/api/v1",
    tags=["suppliers"]
)

app.include_router(
    gas_routes.router,
    prefix="/api/v1/inventory",
    tags=["gases"]
)

app.include_router(
    keg_routes.router,
    prefix="/api/v1/inventory",
    tags=["kegs"]
)

app.include_router(
    finished_product_routes.router,
    prefix="/api/v1/inventory",
    tags=["finished-products", "cold-room"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
