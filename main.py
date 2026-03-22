"""
Aerospace Compliance Platform
Ana uygulama dosyasi. Buradan baslatilir.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.api.routes.standards_router import router as standards_router
from src.api.routes.reports_router import router as reports_router
from src.infrastructure.database.connection import create_tables

# ── Uygulama ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Aerospace Compliance Platform",
    description="MIL-STD-810H, DO-178C gibi standartlarla uyumluluk analizi",
    version="1.0.0",
)

# CORS — frontend'den erisim icin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route'lari ekle
app.include_router(standards_router)
app.include_router(reports_router)


# ── Baslangic ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    logger.info("Uygulama baslatiliyor...")
    create_tables()
    logger.info("Aerospace Compliance Platform hazir!")


@app.get("/")
def root():
    return {
        "app": "Aerospace Compliance Platform",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}