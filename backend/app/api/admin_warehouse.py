# ---------------------------------------------------------------
# Admin review of warehouse listings (M6).
#
#   GET  /api/admin/warehouses?status=PENDING_REVIEW   listings to review
#   GET  /api/admin/warehouses/{id}                    one listing
#   POST /api/admin/warehouses/{id}/approve            -> APPROVED
#   POST /api/admin/warehouses/{id}/reject  {reason}   -> back to DRAFT
#
# Rejecting sends the listing back to the owner as a DRAFT with the
# reason shown, so they can fix it and submit again.
# ---------------------------------------------------------------
import uuid
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.common import commit_or_409
from app.api.warehouse import warehouse_out
from app.auth import require_admin
from app.db import get_session
from app.models import User, Warehouse
from app.schemas.warehouse import RejectIn, WarehouseOut

router = APIRouter(prefix="/api/admin/warehouses", tags=["admin review"])

DbSession = Annotated[Session, Depends(get_session)]
AdminUser = Annotated[User, Depends(require_admin)]


def listing_or_404(session: Session, warehouse_id: uuid.UUID) -> Warehouse:
    warehouse = session.get(Warehouse, warehouse_id)
    if warehouse is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Listing not found")
    return warehouse


def require_pending(warehouse: Warehouse) -> None:
    if warehouse.status != "PENDING_REVIEW":
        raise HTTPException(status.HTTP_409_CONFLICT, "This listing isn't waiting for review")


def mark_reviewed(warehouse: Warehouse, admin: User) -> None:
    warehouse.reviewed_at = datetime.now(UTC)
    warehouse.reviewed_by_id = admin.id


@router.get("", response_model=list[WarehouseOut])
def listings(
    admin: AdminUser,
    session: DbSession,
    status_filter: Annotated[
        Literal["DRAFT", "PENDING_REVIEW", "APPROVED"], Query(alias="status")
    ] = "PENDING_REVIEW",
):
    rows = session.scalars(
        select(Warehouse).where(Warehouse.status == status_filter).order_by(Warehouse.updated_at)
    ).all()
    return [warehouse_out(session, row, with_owner=True) for row in rows]


@router.get("/{warehouse_id}", response_model=WarehouseOut)
def listing(warehouse_id: uuid.UUID, admin: AdminUser, session: DbSession):
    return warehouse_out(session, listing_or_404(session, warehouse_id), with_owner=True)


@router.post("/{warehouse_id}/approve", response_model=WarehouseOut)
def approve(warehouse_id: uuid.UUID, admin: AdminUser, session: DbSession):
    warehouse = listing_or_404(session, warehouse_id)
    require_pending(warehouse)
    warehouse.status = "APPROVED"
    warehouse.review_note = None
    mark_reviewed(warehouse, admin)
    commit_or_409(session, "Listing was changed at the same time, try again")
    session.refresh(warehouse)
    return warehouse_out(session, warehouse, with_owner=True)


@router.post("/{warehouse_id}/reject", response_model=WarehouseOut)
def reject(warehouse_id: uuid.UUID, body: RejectIn, admin: AdminUser, session: DbSession):
    warehouse = listing_or_404(session, warehouse_id)
    require_pending(warehouse)
    warehouse.status = "DRAFT"
    warehouse.review_note = body.reason
    mark_reviewed(warehouse, admin)
    commit_or_409(session, "Listing was changed at the same time, try again")
    session.refresh(warehouse)
    return warehouse_out(session, warehouse, with_owner=True)
