"""
Main FastAPI application for Production Service.

v0.2.0: Added Cost Management (Ingredient Prices + Fixed Costs CRUD).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from api.production_routes import router as production_router
from api.ingredient_price_routes import router as ingredient_price_router
from api.fixed_cost_routes import router as fixed_cost_router
from database import Base, engine, ensure_schema_upgrades
import models  # noqa: F401

app = FastAPI(
    title="Desert Brew Production Service",
    description="Manufacturing Execution System (MES) with BeerSmith integration + Cost Management",
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
app.include_router(production_router)
app.include_router(ingredient_price_router)
app.include_router(fixed_cost_router)


@app.on_event("startup")
def startup_event():
    """Ensure schema exists before serving requests."""
    Base.metadata.create_all(bind=engine)
    ensure_schema_upgrades()


@app.get("/")
def root():
    return {
        "service": "Desert Brew Production Service",
        "version": "0.2.0",
        "status": "operational",
        "modules": ["production", "ingredient_prices", "fixed_costs"],
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
