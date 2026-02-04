"""
Main FastAPI application for Finance Service.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.finance_routes import router as finance_router

app = FastAPI(
    title="Desert Brew Finance Service",
    description="Transfer Pricing and Shadow Ledger",
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
app.include_router(finance_router)


@app.get("/")
def root():
    return {
        "service": "Desert Brew Finance Service",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
