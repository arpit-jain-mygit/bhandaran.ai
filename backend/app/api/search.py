# ---------------------------------------------------------------
# Search (M7): anyone can find APPROVED godowns. No login needed.
#
#   GET /api/search/warehouses?state_id=&district_id=&city_id=&pincode=
#        &storage_type_id=&stock_type_id=&max_price=&min_capacity=
#   GET /api/search/warehouses/{id}      one approved godown
#
# Results are sorted cheapest first, at most MAX_RESULTS.
# Free space = total capacity until bookings arrive (M8).
# ---------------------------------------------------------------
import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app import photos
from app.db import get_session
from app.models import (
    City,
    District,
    State,
    StockType,
    StorageType,
    Unit,
    Warehouse,
    WarehousePhoto,
    WarehouseStockType,
)
from app.schemas.search import SearchDetail, SearchResult

router = APIRouter(prefix="/api/search", tags=["search"])

DbSession = Annotated[Session, Depends(get_session)]
MAX_RESULTS = 50


# ---------- helpers ----------


def available_capacity(warehouse: Warehouse) -> int:
    """Free space. Bookings (M8) will subtract booked space here."""
    return warehouse.capacity


def photo_urls(session: Session, warehouse: Warehouse) -> list[str]:
    keys = session.scalars(
        select(WarehousePhoto.s3_key)
        .where(WarehousePhoto.warehouse_id == warehouse.id, WarehousePhoto.status == "UPLOADED")
        .order_by(WarehousePhoto.created_at)
    ).all()
    return [photos.view_link(key) for key in keys]


def result_fields(session: Session, warehouse: Warehouse, urls: list[str]) -> dict:
    city = session.get(City, warehouse.city_id)
    district = session.get(District, city.district_id)
    state = session.get(State, district.state_id)
    stock_names = session.scalars(
        select(StockType.name)
        .join(WarehouseStockType, WarehouseStockType.stock_type_id == StockType.id)
        .where(WarehouseStockType.warehouse_id == warehouse.id)
        .order_by(StockType.sort_order, StockType.name)
    ).all()
    return {
        "id": warehouse.id,
        "name": warehouse.name,
        "city_name": city.name,
        "district_name": district.name,
        "state_name": state.name,
        "pincode": warehouse.pincode,
        "storage_type_name": session.get(StorageType, warehouse.storage_type_id).name,
        "unit_name": session.get(Unit, warehouse.unit_id).name,
        "available_capacity": available_capacity(warehouse),
        "price_per_unit_month": warehouse.price_per_unit_month,
        "stock_types": list(stock_names),
        "photo_url": urls[0] if urls else None,
    }


# ---------- endpoints ----------


@router.get("/warehouses", response_model=list[SearchResult])
def search(
    session: DbSession,
    state_id: uuid.UUID | None = None,
    district_id: uuid.UUID | None = None,
    city_id: uuid.UUID | None = None,
    pincode: Annotated[str | None, Query(pattern=r"^\d{6}$")] = None,
    storage_type_id: uuid.UUID | None = None,
    stock_type_id: uuid.UUID | None = None,
    max_price: Annotated[Decimal | None, Query(ge=0)] = None,
    min_capacity: Annotated[int | None, Query(ge=1)] = None,
):
    query = (
        select(Warehouse)
        .join(City, City.id == Warehouse.city_id)
        .join(District, District.id == City.district_id)
        .where(Warehouse.status == "APPROVED")
    )
    if state_id:
        query = query.where(District.state_id == state_id)
    if district_id:
        query = query.where(City.district_id == district_id)
    if city_id:
        query = query.where(Warehouse.city_id == city_id)
    if pincode:
        query = query.where(Warehouse.pincode == pincode)
    if storage_type_id:
        query = query.where(Warehouse.storage_type_id == storage_type_id)
    if stock_type_id:
        query = query.where(
            exists().where(
                WarehouseStockType.warehouse_id == Warehouse.id,
                WarehouseStockType.stock_type_id == stock_type_id,
            )
        )
    if max_price is not None:
        query = query.where(Warehouse.price_per_unit_month <= max_price)
    if min_capacity is not None:
        # Until bookings exist, free space = total capacity.
        query = query.where(Warehouse.capacity >= min_capacity)

    rows = session.scalars(
        query.order_by(Warehouse.price_per_unit_month, Warehouse.name).limit(MAX_RESULTS)
    ).all()
    results = []
    for warehouse in rows:
        urls = photo_urls(session, warehouse)
        results.append(SearchResult(**result_fields(session, warehouse, urls[:1])))
    return results


@router.get("/warehouses/{warehouse_id}", response_model=SearchDetail)
def detail(warehouse_id: uuid.UUID, session: DbSession):
    warehouse = session.get(Warehouse, warehouse_id)
    if warehouse is None or warehouse.status != "APPROVED":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Godown not found")
    urls = photo_urls(session, warehouse)
    return SearchDetail(
        **result_fields(session, warehouse, urls),
        address=warehouse.address,
        capacity=warehouse.capacity,
        photo_urls=urls,
    )
