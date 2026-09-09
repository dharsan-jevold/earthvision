from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth_routes import router as auth_router
from app.api.extras_routes import router as extras_router
from app.api.project_routes import router as project_router
from app.api.routes import router
from app.database.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="EarthVision AI API",
    description="AI-powered satellite Earth intelligence & change detection platform",
    version="0.2.0-phase14",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production via env-configured allowlist
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(project_router, prefix="/api")
app.include_router(extras_router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "EarthVision AI",
        "status": "running",
        "phase": "1-14 (map, demo provider, NDVI/NDWI/NDBI, baseline + ML change detection, "
        "GIS layers, time-series, report generation, auth/database, export)",
        "docs": "/docs",
    }
