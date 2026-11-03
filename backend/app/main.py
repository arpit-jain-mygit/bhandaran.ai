# ---------------------------------------------------------------
# FastAPI application entry point.
# Run locally:  uvicorn app.main:app --reload
# Interactive API docs: http://localhost:8000/docs
# ---------------------------------------------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import admin_warehouse, auth, health, master, profile, settings, warehouse
from app.config import get_settings

app = FastAPI(title="bhandaran.ai API", version=__version__)

# CORS: allow the Angular app (different port/domain) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules. Each new feature adds one line here.
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(master.router)
app.include_router(settings.router)
app.include_router(profile.router)
app.include_router(warehouse.router)
app.include_router(admin_warehouse.router)
