# ---------------------------------------------------------------
# Warehouse listings (M5): an owner's godown, the stock types it
# accepts, and its photos.
#
#   warehouse             - one listing; starts as DRAFT, then
#                           PENDING_REVIEW when the owner submits it
#   warehouse_stock_type  - which stock types a listing accepts
#   warehouse_photo       - a photo in S3 (PENDING until confirmed)
# ---------------------------------------------------------------
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UuidPkMixin

WAREHOUSE_STATUSES = ("DRAFT", "PENDING_REVIEW")
PHOTO_STATUSES = ("PENDING", "UPLOADED")


class Warehouse(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "warehouse"
    __table_args__ = (
        CheckConstraint(f"status IN {WAREHOUSE_STATUSES}", name="ck_warehouse_status"),
        CheckConstraint("capacity > 0", name="ck_warehouse_capacity_positive"),
        CheckConstraint("price_per_unit_month >= 0", name="ck_warehouse_price_not_negative"),
        Index("ix_warehouse_owner_created", "owner_id", "created_at"),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    city_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    pincode: Mapped[str] = mapped_column(String(6), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    storage_type_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    price_per_unit_month: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="DRAFT")


class WarehouseStockType(UuidPkMixin, Base):
    __tablename__ = "warehouse_stock_type"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "stock_type_id", name="uq_warehouse_stock_type"),
    )

    warehouse_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    stock_type_id: Mapped[uuid.UUID] = mapped_column(nullable=False)


class WarehousePhoto(UuidPkMixin, Base):
    __tablename__ = "warehouse_photo"
    __table_args__ = (
        CheckConstraint(f"status IN {PHOTO_STATUSES}", name="ck_warehouse_photo_status"),
    )

    warehouse_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    s3_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(30), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="PENDING")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
