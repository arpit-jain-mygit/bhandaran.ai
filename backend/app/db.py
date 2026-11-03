# ---------------------------------------------------------------
# Database connection.
# One function builds the SQLAlchemy "engine" (connection pool) for
# either local PostgreSQL or Aurora DSQL, based on settings.db_mode.
# Everything else in the app just asks for a Session.
# ---------------------------------------------------------------
from collections.abc import Iterator
from functools import lru_cache

from aurora_dsql_sqlalchemy import create_dsql_engine
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings

# DSQL closes connections after 60 minutes, so recycle them a bit earlier.
DSQL_POOL_RECYCLE_SECONDS = 50 * 60


def build_engine(settings: Settings) -> Engine:
    """Create the connection pool for the configured database."""
    if settings.db_mode == "dsql":
        # AWS helper: fetches short-lived IAM auth tokens automatically
        # (no password stored anywhere) and enforces TLS.
        return create_dsql_engine(
            host=settings.dsql_endpoint,
            user=settings.dsql_user,
            driver="psycopg",
            application_name="bhandaran-api",
            pool_recycle=DSQL_POOL_RECYCLE_SECONDS,
            pool_pre_ping=True,
            connect_args={"region": settings.aws_region},
        )

    # Local PostgreSQL: a normal connection URL is enough.
    return create_engine(settings.local_database_url, pool_pre_ping=True)


@lru_cache
def get_engine() -> Engine:
    """One shared engine for the whole app (created on first use)."""
    return build_engine(get_settings())


def get_session() -> Iterator[Session]:
    """FastAPI dependency: gives each request its own Session, closed afterwards."""
    session_factory = sessionmaker(bind=get_engine())
    with session_factory() as session:
        yield session
