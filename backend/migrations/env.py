# ---------------------------------------------------------------
# Alembic environment: how migrations connect to the database.
#
# Aurora DSQL rules this file handles (also safe for local Postgres):
#   1. A transaction may hold only ONE DDL statement, and DDL cannot
#      be mixed with DML (e.g. Alembic's version-table UPDATE).
#      -> run in AUTOCOMMIT: every statement is its own transaction.
#   2. Alembic must know the "auroradsql" dialect name.
#      -> register a small Postgres-based implementation below.
#
# Team rule: keep ONE schema change per migration file, so a failed
# migration never leaves the schema half-changed.
# ---------------------------------------------------------------
from logging.config import fileConfig

from alembic import context
from alembic.ddl.postgresql import PostgresqlImpl

from app.config import get_settings
from app.db import build_engine


# Tell Alembic to treat "auroradsql" like PostgreSQL, but without
# wrapping DDL in transactions (DSQL does not allow mixing).
class AuroraDSQLImpl(PostgresqlImpl):
    __dialect__ = "auroradsql"
    transactional_ddl = False


# Set up logging from alembic.ini.
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Table definitions for "alembic revision --autogenerate".
# Stays None until ORM models exist (M1 onwards).
target_metadata = None


def run_migrations_offline() -> None:
    """Print SQL instead of running it:  alembic upgrade head --sql"""
    context.configure(
        url=get_settings().local_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the configured database (local or DSQL) and migrate."""
    engine = build_engine(get_settings())

    # AUTOCOMMIT = each DDL / version update commits on its own (rule 1).
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
