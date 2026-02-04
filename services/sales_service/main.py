"""
Main FastAPI application for Sales Service.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.commission_routes import router as commission_router

app = FastAPI(
    title="Desert Brew Sales Service",
    description="Multi-channel Sales Management",
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
app.include_router(commission_router)


@app.get("/")
def root():
    return {
        "service": "Desert Brew Sales Service",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
