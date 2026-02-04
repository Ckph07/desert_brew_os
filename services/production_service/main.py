"""
Main FastAPI application for Production Service.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.production_routes import router as production_router

app = FastAPI(
    title="Desert Brew Production Service",
    description="Manufacturing Execution System (MES) with BeerSmith integration",
    version="0.1.0"
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


@app.get("/")
def root():
    return {
        "service": "Desert Brew Production Service",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
