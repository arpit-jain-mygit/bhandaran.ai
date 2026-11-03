# ---------------------------------------------------------------
# All ORM models. Importing this package registers every table on
# Base.metadata (Alembic and tests rely on that).
# ---------------------------------------------------------------
from app.models.base import Base
from app.models.mail import EmailSuppression
from app.models.master import City, District, State, StockType, StorageType, Unit
from app.models.settings import OwnerSetting, PlatformSetting
from app.models.users import ROLES, OtpChallenge, User, UserRole
from app.models.warehouse import Warehouse, WarehousePhoto, WarehouseStockType

__all__ = [
    "Base",
    "City",
    "District",
    "EmailSuppression",
    "OtpChallenge",
    "OwnerSetting",
    "PlatformSetting",
    "ROLES",
    "State",
    "StockType",
    "StorageType",
    "Unit",
    "User",
    "UserRole",
    "Warehouse",
    "WarehousePhoto",
    "WarehouseStockType",
]
