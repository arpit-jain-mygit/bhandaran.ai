# ---------------------------------------------------------------
# JSON shapes for the master-data API.
#   ...Create  = body of POST (add a new item)
#   ...Update  = body of PATCH (change some fields; others stay as-is)
#   ...Out     = what the API returns
# ---------------------------------------------------------------
import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Reusable field rules. strip_whitespace removes accidental spaces.
Code = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"^[A-Za-z0-9_]{1,20}$"),
]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
SortOrder = Annotated[int, Field(ge=0, le=9999)]


# ---------- Simple lists: stock types, storage types, units, states ----------


class LookupCreate(BaseModel):
    code: Code  # e.g. "wheat" -> stored as "WHEAT"
    name: Name
    sort_order: SortOrder = 0


class LookupUpdate(BaseModel):
    name: Name | None = None
    sort_order: SortOrder | None = None
    is_active: bool | None = None


class LookupOut(BaseModel):
    # from_attributes: build this directly from an ORM object.
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    sort_order: int
    is_active: bool


# ---------- Districts (belong to a state) ----------


class DistrictCreate(BaseModel):
    state_id: uuid.UUID
    name: Name


class DistrictUpdate(BaseModel):
    name: Name | None = None
    is_active: bool | None = None


class DistrictOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    state_id: uuid.UUID
    name: str
    is_active: bool


# ---------- Cities / towns (belong to a district) ----------


class CityCreate(BaseModel):
    district_id: uuid.UUID
    name: Name


class CityUpdate(BaseModel):
    name: Name | None = None
    is_active: bool | None = None


class CityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    district_id: uuid.UUID
    state_id: uuid.UUID  # derived from the district, for convenience
    name: str
    is_active: bool
