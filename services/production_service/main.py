"""
Main FastAPI application for Production Service.

v0.2.0: Added Cost Management (Ingredient Prices + Fixed Costs CRUD).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.production_routes import router as production_router
from api.ingredient_price_routes import router as ingredient_price_router
from api.fixed_cost_routes import router as fixed_cost_router

app = FastAPI(
    title="Desert Brew Production Service",
    description="Manufacturing Execution System (MES) with BeerSmith integration + Cost Management",
    version="0.2.0"
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
app.include_router(production_router)
app.include_router(ingredient_price_router)
app.include_router(fixed_cost_router)


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
