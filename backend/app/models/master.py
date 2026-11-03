# ---------------------------------------------------------------
# Master data (M1): reference lists every other feature uses.
#   stock_type   - what is stored (Wheat, Potato, ...)
#   storage_type - kind of space (Dry, Cold, Open yard)
#   unit         - how space is measured/priced (Bag, Sq ft)
#   state, city  - where warehouses are (city belongs to a state)
#
# Rows are never deleted, only disabled (is_active = false), so old
# bookings that point at them stay valid.
# ---------------------------------------------------------------
import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, LookupMixin, TimestampMixin, UuidPkMixin


class StockType(LookupMixin, Base):
    __tablename__ = "stock_type"


class StorageType(LookupMixin, Base):
    __tablename__ = "storage_type"


class Unit(LookupMixin, Base):
    __tablename__ = "unit"


class State(LookupMixin, Base):
    __tablename__ = "state"

    # All cities in this state (used for convenience in code).
    cities: Mapped[list["City"]] = relationship(back_populates="state")


class City(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "city"
    # The same city name can't appear twice in one state.
    __table_args__ = (UniqueConstraint("state_id", "name", name="uq_city_state_name"),)

    # Foreign key: every city must belong to an existing state.
    state_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("state.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    state: Mapped[State] = relationship(back_populates="cities")
