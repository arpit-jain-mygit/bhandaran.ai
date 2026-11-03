# ---------------------------------------------------------------
# Master data (M1): reference lists every other feature uses.
#   stock_type   - what is stored (Wheat, Potato, ...)
#   storage_type - kind of space (Dry, Cold, Open yard)
#   unit         - how space is measured/priced (Bag, Sq ft)
#   state > district > city   - where warehouses are
#                  (a city/town belongs to a district, which belongs
#                   to a state)
#
# Rows are never deleted, only disabled (is_active = false), so old
# bookings that point at them stay valid.
# ---------------------------------------------------------------
import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint
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

    # All districts in this state (used for convenience in code).
    districts: Mapped[list["District"]] = relationship(back_populates="state")


class District(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "district"
    # The same district name can't appear twice in one state.
    __table_args__ = (UniqueConstraint("state_id", "name", name="uq_district_state_name"),)

    # Foreign key: every district must belong to an existing state.
    state_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("state.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    state: Mapped[State] = relationship(back_populates="districts")
    cities: Mapped[list["City"]] = relationship(back_populates="district")


class City(UuidPkMixin, TimestampMixin, Base):
    """A city or town. Shown to users as "City / Town"."""

    __tablename__ = "city"
    # Same town name may exist in two districts, but not twice in one.
    __table_args__ = (Index("uq_city_district_name", "district_id", "name", unique=True),)

    # Every city/town belongs to a district. (In the database this is
    # enforced by a foreign key + a NOT NULL check constraint.)
    district_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("district.id", name="fk_city_district"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    district: Mapped[District] = relationship(back_populates="cities")

    @property
    def state_id(self) -> uuid.UUID:
        """The city's state, via its district (handy for the API)."""
        return self.district.state_id
