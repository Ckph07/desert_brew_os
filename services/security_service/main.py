"""
Main FastAPI application for Security Service.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from api.enrollment_routes import router as enrollment_router
from database import Base, engine
import models  # noqa: F401

app = FastAPI(
    title="Desert Brew Security Service",
    description="Device Enrollment and Cryptographic Verification",
    version="0.1.0"
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
app.include_router(enrollment_router)


@app.on_event("startup")
def startup_event():
    """Ensure schema exists before serving requests."""
    Base.metadata.create_all(bind=engine)


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
