# ---------------------------------------------------------------
# Seed the master-data lists with a sensible starting set.
# Data only (DML) - kept separate from the table-creating (DDL)
# migrations, as Aurora DSQL requires. Admins can add, rename or
# disable any of these later from the admin screens.
#
# Revision ID: 0007_seed_master_data
# Revises: 0006_create_city
# Created: 2026-11-03
# ---------------------------------------------------------------
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Identifiers Alembic uses to order migrations.
revision: str = "0007_seed_master_data"
down_revision: str | None = "0006_create_city"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (code, name) - list order becomes sort_order (10, 20, 30, ...).
STOCK_TYPES = [
    ("WHEAT", "Wheat"),
    ("RICE", "Rice / Paddy"),
    ("POTATO", "Potato"),
    ("ONION", "Onion"),
    ("PULSES", "Pulses"),
    ("CHANA", "Chana (Gram)"),
    ("SOYBEAN", "Soybean"),
    ("MAIZE", "Maize"),
    ("MUSTARD", "Mustard"),
    ("COTTON", "Cotton"),
    ("SUGAR", "Sugar"),
    ("SPICES", "Spices"),
]

STORAGE_TYPES = [
    ("DRY", "Dry storage"),
    ("COLD", "Cold storage"),
    ("OPEN", "Open yard"),
]

UNITS = [
    ("BAG", "Bag"),
    ("SQFT", "Square feet"),
]

# 28 states + 8 union territories (short codes are internal keys).
STATES = [
    ("AP", "Andhra Pradesh"),
    ("AR", "Arunachal Pradesh"),
    ("AS", "Assam"),
    ("BR", "Bihar"),
    ("CG", "Chhattisgarh"),
    ("GA", "Goa"),
    ("GJ", "Gujarat"),
    ("HR", "Haryana"),
    ("HP", "Himachal Pradesh"),
    ("JH", "Jharkhand"),
    ("KA", "Karnataka"),
    ("KL", "Kerala"),
    ("MP", "Madhya Pradesh"),
    ("MH", "Maharashtra"),
    ("MN", "Manipur"),
    ("ML", "Meghalaya"),
    ("MZ", "Mizoram"),
    ("NL", "Nagaland"),
    ("OD", "Odisha"),
    ("PB", "Punjab"),
    ("RJ", "Rajasthan"),
    ("SK", "Sikkim"),
    ("TN", "Tamil Nadu"),
    ("TS", "Telangana"),
    ("TR", "Tripura"),
    ("UP", "Uttar Pradesh"),
    ("UK", "Uttarakhand"),
    ("WB", "West Bengal"),
    ("AN", "Andaman and Nicobar Islands"),
    ("CH", "Chandigarh"),
    ("DH", "Dadra and Nagar Haveli and Daman and Diu"),
    ("DL", "Delhi"),
    ("JK", "Jammu and Kashmir"),
    ("LA", "Ladakh"),
    ("LD", "Lakshadweep"),
    ("PY", "Puducherry"),
]

# Starter cities: major mandi / trading hubs. Admins add the rest.
CITIES = {
    "MP": ["Indore", "Bhopal", "Ujjain", "Gwalior", "Jabalpur"],
    "MH": ["Mumbai", "Pune", "Nagpur", "Nashik"],
    "UP": ["Lucknow", "Kanpur", "Agra"],
    "RJ": ["Jaipur", "Kota"],
    "GJ": ["Ahmedabad", "Rajkot"],
    "PB": ["Ludhiana", "Amritsar"],
    "HR": ["Karnal"],
    "DL": ["Delhi"],
    "KA": ["Bengaluru"],
    "TN": ["Chennai"],
    "TS": ["Hyderabad"],
    "WB": ["Kolkata"],
    "BR": ["Patna"],
}

LOOKUPS = {
    "stock_type": STOCK_TYPES,
    "storage_type": STORAGE_TYPES,
    "unit": UNITS,
    "state": STATES,
}


def lookup_table(name: str) -> sa.Table:
    """Minimal table description, enough for inserts/deletes."""
    return sa.table(
        name,
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("sort_order", sa.Integer),
    )


def upgrade() -> None:
    # Simple lists: one bulk insert per table.
    for table_name, rows in LOOKUPS.items():
        op.bulk_insert(
            lookup_table(table_name),
            [
                {"code": code, "name": name, "sort_order": (index + 1) * 10}
                for index, (code, name) in enumerate(rows)
            ],
        )

    # Cities: look up each state's generated id by its code.
    for state_code, city_names in CITIES.items():
        for city_name in city_names:
            op.execute(
                sa.text(
                    "INSERT INTO city (state_id, name) "
                    "SELECT id, :name FROM state WHERE code = :code"
                ).bindparams(name=city_name, code=state_code)
            )


def downgrade() -> None:
    # Remove exactly the seeded rows (cities first: they point at states).
    for state_code, city_names in CITIES.items():
        for city_name in city_names:
            op.execute(
                sa.text(
                    "DELETE FROM city WHERE name = :name "
                    "AND state_id = (SELECT id FROM state WHERE code = :code)"
                ).bindparams(name=city_name, code=state_code)
            )
    for table_name, rows in LOOKUPS.items():
        table = lookup_table(table_name)
        op.execute(table.delete().where(table.c.code.in_([code for code, _ in rows])))
