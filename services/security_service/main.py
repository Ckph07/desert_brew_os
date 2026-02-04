"""
Main FastAPI application for Security Service.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.enrollment_routes import router as enrollment_router

app = FastAPI(
    title="Desert Brew Security Service",
    description="Device Enrollment and Cryptographic Verification",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(enrollment_router)


@app.get("/")
def root():
    return {
        "service": "Desert Brew Security Service",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
