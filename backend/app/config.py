# ---------------------------------------------------------------
# App settings, read from environment variables or a .env file.
# Example: DB_MODE=dsql  ->  settings.db_mode == "dsql"
# See .env.example for every setting.
# ---------------------------------------------------------------
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Read a local .env file if present; real env vars win over it.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "local" = plain PostgreSQL on your machine (fast, free, offline)
    # "dsql"  = Aurora DSQL in AWS (IAM auth, used for integration/prod)
    db_mode: Literal["local", "dsql"] = "local"

    # Used when db_mode = "local".
    local_database_url: str = "postgresql+psycopg://localhost:5432/bhandaran"

    # Used when db_mode = "dsql" (values from `terraform output` in infra/envs/dev).
    dsql_endpoint: str = ""
    dsql_user: str = "admin"
    aws_region: str = "ap-south-1"

    # Browser origins allowed to call the API (the Angular dev server).
    cors_origins: list[str] = ["http://localhost:4200"]

    # TEMPORARY (until M3 login): secret that admin write requests must
    # send in the X-Admin-Key header. Empty = all admin writes refused.
    admin_api_key: str = ""


# lru_cache = read settings once, then reuse the same object everywhere.
@lru_cache
def get_settings() -> Settings:
    return Settings()
