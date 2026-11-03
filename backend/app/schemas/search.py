# ---------------------------------------------------------------
# JSON shapes for searching approved godowns (M7). Public: no owner
# contact details here; renters book through the app (M8/M9).
# ---------------------------------------------------------------
import uuid
from decimal import Decimal

from pydantic import BaseModel


class SearchResult(BaseModel):
    id: uuid.UUID
    name: str
    city_name: str
    district_name: str
    state_name: str
    pincode: str
    storage_type_name: str
    unit_name: str
    # Free space. Until bookings exist (M8) this is the total capacity.
    available_capacity: int
    price_per_unit_month: Decimal
    stock_types: list[str]
    photo_url: str | None  # first photo, if any


class SearchDetail(SearchResult):
    address: str
    capacity: int
    photo_urls: list[str]
