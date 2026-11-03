# ---------------------------------------------------------------
# Master-data API (M1).
#
#   GET   /api/master/{kind}             list (active only by default)
#   POST  /api/master/{kind}             add            [admin]
#   PATCH /api/master/{kind}/{id}        edit / disable [admin]
#     kind = stock-types | storage-types | units | states
#
#   GET   /api/master/cities?state_id=   list cities (optionally of one state)
#   POST  /api/master/cities             add            [admin]
#   PATCH /api/master/cities/{id}        edit / disable [admin]
#
# Reads are public (dropdowns need them). Writes need the admin key.
# Nothing is ever deleted: disable with {"is_active": false}.
# ---------------------------------------------------------------
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.db import get_session
from app.models import City, State, StockType, StorageType, Unit
from app.schemas.master import (
    CityCreate,
    CityOut,
    CityUpdate,
    LookupCreate,
    LookupOut,
    LookupUpdate,
)

router = APIRouter(prefix="/api/master", tags=["master data"])

# URL name -> table. One set of endpoints serves all four simple lists.
LOOKUP_MODELS = {
    "stock-types": StockType,
    "storage-types": StorageType,
    "units": Unit,
    "states": State,
}

# Short names for the dependencies used below.
DbSession = Annotated[Session, Depends(get_session)]
AdminOnly = Depends(require_admin)


# ---------- helpers ----------


def lookup_model(kind: str):
    """Turn the {kind} in the URL into a table, or 404 if unknown."""
    model = LOOKUP_MODELS.get(kind)
    if model is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown list '{kind}'")
    return model


def commit_or_409(session: Session, conflict_message: str) -> None:
    """
    Save changes. Two kinds of failure become HTTP 409 (Conflict):
      - IntegrityError: a unique rule was broken (duplicate code/name)
      - SQLSTATE 40001: DSQL optimistic-concurrency conflict; the
        client can simply try again
    """
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, conflict_message) from error
    except OperationalError as error:
        session.rollback()
        if getattr(error.orig, "sqlstate", None) == "40001":
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Changed by someone else at the same time, try again"
            ) from error
        raise


# ---------- cities (declared first so "/cities" isn't read as a {kind}) ----------


@router.get("/cities", response_model=list[CityOut])
def list_cities(
    session: DbSession,
    state_id: uuid.UUID | None = None,
    include_inactive: bool = False,
):
    query = select(City).order_by(City.name)
    if state_id is not None:
        query = query.where(City.state_id == state_id)
    if not include_inactive:
        query = query.where(City.is_active.is_(True))
    return session.scalars(query).all()


@router.post(
    "/cities",
    response_model=CityOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[AdminOnly],
)
def create_city(body: CityCreate, session: DbSession):
    if session.get(State, body.state_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "State not found")

    # Names are compared case-insensitively ("indore" == "Indore").
    duplicate = session.scalar(
        select(City.id).where(
            City.state_id == body.state_id, func.lower(City.name) == body.name.lower()
        )
    )
    if duplicate:
        raise HTTPException(status.HTTP_409_CONFLICT, "City already exists in this state")

    city = City(state_id=body.state_id, name=body.name)
    session.add(city)
    commit_or_409(session, "City already exists in this state")
    session.refresh(city)
    return city


@router.patch("/cities/{city_id}", response_model=CityOut, dependencies=[AdminOnly])
def update_city(city_id: uuid.UUID, body: CityUpdate, session: DbSession):
    city = session.get(City, city_id)
    if city is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "City not found")

    # exclude_unset: only change fields the client actually sent.
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(city, field, value)
    commit_or_409(session, "City already exists in this state")
    session.refresh(city)
    return city


# ---------- simple lists ----------


@router.get("/{kind}", response_model=list[LookupOut])
def list_items(kind: str, session: DbSession, include_inactive: bool = Query(False)):
    model = lookup_model(kind)
    query = select(model).order_by(model.sort_order, model.name)
    if not include_inactive:
        query = query.where(model.is_active.is_(True))
    return session.scalars(query).all()


@router.post(
    "/{kind}",
    response_model=LookupOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[AdminOnly],
)
def create_item(kind: str, body: LookupCreate, session: DbSession):
    model = lookup_model(kind)
    item = model(code=body.code, name=body.name, sort_order=body.sort_order)
    session.add(item)
    commit_or_409(session, f"Code '{body.code}' already exists")
    session.refresh(item)
    return item


@router.patch("/{kind}/{item_id}", response_model=LookupOut, dependencies=[AdminOnly])
def update_item(kind: str, item_id: uuid.UUID, body: LookupUpdate, session: DbSession):
    model = lookup_model(kind)
    item = session.get(model, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    commit_or_409(session, "Conflicting change")
    session.refresh(item)
    return item
