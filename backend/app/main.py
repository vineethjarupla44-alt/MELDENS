from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import engine, Base
import app.db.models # Ensure all models are registered
from app.api.health import router as health_router
from app.api.v1.router import api_v1_router
import os

# Create database tables automatically for local development
Base.metadata.create_all(bind=engine)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "MedLens API — Transforms fragmented medical reports into a structured, "
        "understandable, traceable, and reviewable patient record. "
        "Strictly non-diagnostic and non-prescriptive."
    ),
    version="1.0.0-phase1",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health router at /api/health as well as /health
app.include_router(health_router, prefix="/api")
app.include_router(health_router)

# Versioned API routes
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "health_check": "/api/health",
        "documentation": "/api/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
