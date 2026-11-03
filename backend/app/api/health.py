# ---------------------------------------------------------------
# GET /api/health
# Tells the Angular app (and monitoring) that the API is up and
# whether it can reach the database.
# ---------------------------------------------------------------
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import __version__
from app.config import get_settings
from app.db import get_session

router = APIRouter(prefix="/api", tags=["health"])


# Shape of the JSON response (also documented in /docs automatically).
class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    db_mode: str
    database: Literal["ok", "unreachable"]


@router.get("/health", response_model=HealthResponse)
def health(session: Annotated[Session, Depends(get_session)]) -> HealthResponse:
    # Run the cheapest possible query to prove the DB connection works.
    try:
        session.execute(text("SELECT 1"))
        database = "ok"
    except SQLAlchemyError:
        database = "unreachable"

    # API is "ok" only when the DB is reachable; otherwise "degraded".
    return HealthResponse(
        status="ok" if database == "ok" else "degraded",
        version=__version__,
        db_mode=get_settings().db_mode,
        database=database,
    )
