# ---------------------------------------------------------------
# Warehouse listings (M5): an owner describes a godown, adds photos,
# and submits it for admin review (M6).
#
#   GET    /api/warehouses                          my listings
#   POST   /api/warehouses                          new DRAFT listing
#   GET    /api/warehouses/{id}                     one listing
#   PUT    /api/warehouses/{id}                     edit (DRAFT only)
#   POST   /api/warehouses/{id}/submit              DRAFT -> PENDING_REVIEW
#   POST   /api/warehouses/{id}/photos              get an upload link
#   POST   /api/warehouses/{id}/photos/{pid}/confirm  check the upload
#   DELETE /api/warehouses/{id}/photos/{pid}        remove a photo (DRAFT only)
#
# Only the owner who created a listing can see or change it.
# ---------------------------------------------------------------
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app import photos
from app.api.common import commit_or_409
from app.auth import require_owner
from app.db import get_session
from app.models import (
    City,
    StockType,
    StorageType,
    Unit,
    User,
    Warehouse,
    WarehousePhoto,
    WarehouseStockType,
)
from app.schemas.warehouse import PhotoOut, PhotoRequest, PhotoUploadOut, WarehouseIn, WarehouseOut

router = APIRouter(prefix="/api/warehouses", tags=["warehouses"])

DbSession = Annotated[Session, Depends(get_session)]
OwnerUser = Annotated[User, Depends(require_owner)]

EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
MAX_PHOTOS = 10


# ---------- helpers ----------


def my_warehouse(session: Session, owner: User, warehouse_id: uuid.UUID) -> Warehouse:
    """The listing, but only if this owner made it (otherwise 404)."""
    warehouse = session.get(Warehouse, warehouse_id)
    if warehouse is None or warehouse.owner_id != owner.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Listing not found")
    return warehouse


def require_draft(warehouse: Warehouse) -> None:
    if warehouse.status != "DRAFT":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "This listing is under review and can't be changed"
        )


def check_lookups(session: Session, body: WarehouseIn) -> None:
    """Every choice must be a real, active row."""
    checks = [
        (City, body.city_id, "city"),
        (Unit, body.unit_id, "unit"),
        (StorageType, body.storage_type_id, "storage type"),
    ]
    for model, row_id, label in checks:
        if session.get(model, row_id) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Pick a valid {label}")
    for stock_id in body.stock_type_ids:
        if session.get(StockType, stock_id) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Pick valid stock types")


def set_stock_types(session: Session, warehouse: Warehouse, stock_ids: list[uuid.UUID]) -> None:
    session.execute(
        delete(WarehouseStockType).where(WarehouseStockType.warehouse_id == warehouse.id)
    )
    for stock_id in set(stock_ids):
        session.add(WarehouseStockType(warehouse_id=warehouse.id, stock_type_id=stock_id))


def photo_out(photo: WarehousePhoto) -> PhotoOut:
    view = photos.view_link(photo.s3_key) if photo.status == "UPLOADED" else None
    return PhotoOut(id=photo.id, status=photo.status, view_url=view)


def missing_items(session: Session, warehouse: Warehouse) -> list[str]:
    """What still stops the owner from submitting. Empty = ready."""
    missing = []
    stock_count = session.scalar(
        select(WarehouseStockType.id)
        .where(WarehouseStockType.warehouse_id == warehouse.id)
        .limit(1)
    )
    if stock_count is None:
        missing.append("Choose at least one stock type")
    uploaded = session.scalar(
        select(WarehousePhoto.id)
        .where(WarehousePhoto.warehouse_id == warehouse.id, WarehousePhoto.status == "UPLOADED")
        .limit(1)
    )
    if uploaded is None:
        missing.append("Add at least one photo")
    return missing


def warehouse_out(session: Session, warehouse: Warehouse) -> WarehouseOut:
    city = session.get(City, warehouse.city_id)
    unit = session.get(Unit, warehouse.unit_id)
    storage = session.get(StorageType, warehouse.storage_type_id)
    stock_ids = list(
        session.scalars(
            select(WarehouseStockType.stock_type_id).where(
                WarehouseStockType.warehouse_id == warehouse.id
            )
        )
    )
    photo_rows = session.scalars(
        select(WarehousePhoto)
        .where(WarehousePhoto.warehouse_id == warehouse.id)
        .order_by(WarehousePhoto.created_at)
    ).all()
    return WarehouseOut(
        id=warehouse.id,
        name=warehouse.name,
        address=warehouse.address,
        city_id=warehouse.city_id,
        city_name=city.name if city else None,
        pincode=warehouse.pincode,
        capacity=warehouse.capacity,
        unit_id=warehouse.unit_id,
        unit_name=unit.name if unit else None,
        storage_type_id=warehouse.storage_type_id,
        storage_type_name=storage.name if storage else None,
        stock_type_ids=stock_ids,
        price_per_unit_month=warehouse.price_per_unit_month,
        status=warehouse.status,
        photos=[photo_out(p) for p in photo_rows],
        missing=missing_items(session, warehouse),
    )


# ---------- listings ----------


@router.get("", response_model=list[WarehouseOut])
def my_listings(owner: OwnerUser, session: DbSession):
    rows = session.scalars(
        select(Warehouse).where(Warehouse.owner_id == owner.id).order_by(Warehouse.created_at)
    ).all()
    return [warehouse_out(session, row) for row in rows]


@router.post("", response_model=WarehouseOut, status_code=status.HTTP_201_CREATED)
def create_listing(body: WarehouseIn, owner: OwnerUser, session: DbSession):
    check_lookups(session, body)
    warehouse = Warehouse(
        owner_id=owner.id,
        name=body.name,
        address=body.address,
        city_id=body.city_id,
        pincode=body.pincode,
        capacity=body.capacity,
        unit_id=body.unit_id,
        storage_type_id=body.storage_type_id,
        price_per_unit_month=body.price_per_unit_month,
        status="DRAFT",
    )
    session.add(warehouse)
    session.flush()  # gives the listing its id
    set_stock_types(session, warehouse, body.stock_type_ids)
    commit_or_409(session, "Please try again")
    session.refresh(warehouse)
    return warehouse_out(session, warehouse)


@router.get("/{warehouse_id}", response_model=WarehouseOut)
def get_listing(warehouse_id: uuid.UUID, owner: OwnerUser, session: DbSession):
    return warehouse_out(session, my_warehouse(session, owner, warehouse_id))


@router.put("/{warehouse_id}", response_model=WarehouseOut)
def update_listing(
    warehouse_id: uuid.UUID, body: WarehouseIn, owner: OwnerUser, session: DbSession
):
    warehouse = my_warehouse(session, owner, warehouse_id)
    require_draft(warehouse)
    check_lookups(session, body)
    warehouse.name = body.name
    warehouse.address = body.address
    warehouse.city_id = body.city_id
    warehouse.pincode = body.pincode
    warehouse.capacity = body.capacity
    warehouse.unit_id = body.unit_id
    warehouse.storage_type_id = body.storage_type_id
    warehouse.price_per_unit_month = body.price_per_unit_month
    set_stock_types(session, warehouse, body.stock_type_ids)
    commit_or_409(session, "Listing was changed at the same time, try again")
    session.refresh(warehouse)
    return warehouse_out(session, warehouse)


@router.post("/{warehouse_id}/submit", response_model=WarehouseOut)
def submit_listing(warehouse_id: uuid.UUID, owner: OwnerUser, session: DbSession):
    warehouse = my_warehouse(session, owner, warehouse_id)
    require_draft(warehouse)
    problems = missing_items(session, warehouse)
    if problems:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "; ".join(problems))
    warehouse.status = "PENDING_REVIEW"
    commit_or_409(session, "Listing was changed at the same time, try again")
    session.refresh(warehouse)
    return warehouse_out(session, warehouse)


# ---------- photos ----------


@router.post(
    "/{warehouse_id}/photos", response_model=PhotoUploadOut, status_code=status.HTTP_201_CREATED
)
def request_photo_upload(
    warehouse_id: uuid.UUID, body: PhotoRequest, owner: OwnerUser, session: DbSession
):
    warehouse = my_warehouse(session, owner, warehouse_id)
    require_draft(warehouse)
    count = len(
        session.scalars(
            select(WarehousePhoto.id).where(WarehousePhoto.warehouse_id == warehouse.id)
        ).all()
    )
    if count >= MAX_PHOTOS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"At most {MAX_PHOTOS} photos")

    photo_id = uuid.uuid4()
    key = f"warehouses/{warehouse.id}/{photo_id}.{EXTENSIONS[body.content_type]}"
    session.add(
        WarehousePhoto(
            id=photo_id,
            warehouse_id=warehouse.id,
            s3_key=key,
            content_type=body.content_type,
            status="PENDING",
        )
    )
    commit_or_409(session, "Please try again")
    return PhotoUploadOut(
        photo_id=photo_id,
        upload_url=photos.upload_link(key, body.content_type),
        content_type=body.content_type,
    )


@router.post("/{warehouse_id}/photos/{photo_id}/confirm", response_model=WarehouseOut)
def confirm_photo(
    warehouse_id: uuid.UUID, photo_id: uuid.UUID, owner: OwnerUser, session: DbSession
):
    warehouse = my_warehouse(session, owner, warehouse_id)
    require_draft(warehouse)
    photo = session.get(WarehousePhoto, photo_id)
    if photo is None or photo.warehouse_id != warehouse.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Photo not found")

    stored = photos.stored_object(photo.s3_key)
    if stored is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "The photo hasn't finished uploading")
    if stored["size"] > photos.MAX_PHOTO_BYTES or stored["content_type"] != photo.content_type:
        photos.delete_object(photo.s3_key)
        session.delete(photo)
        commit_or_409(session, "Please try again")
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Photo must be a JPG, PNG or WebP under 5 MB"
        )

    photo.status = "UPLOADED"
    photo.size_bytes = stored["size"]
    commit_or_409(session, "Please try again")
    session.refresh(warehouse)
    return warehouse_out(session, warehouse)


@router.delete("/{warehouse_id}/photos/{photo_id}", response_model=WarehouseOut)
def delete_photo(
    warehouse_id: uuid.UUID, photo_id: uuid.UUID, owner: OwnerUser, session: DbSession
):
    warehouse = my_warehouse(session, owner, warehouse_id)
    require_draft(warehouse)
    photo = session.get(WarehousePhoto, photo_id)
    if photo is None or photo.warehouse_id != warehouse.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Photo not found")
    photos.delete_object(photo.s3_key)
    session.delete(photo)
    commit_or_409(session, "Please try again")
    session.refresh(warehouse)
    return warehouse_out(session, warehouse)
