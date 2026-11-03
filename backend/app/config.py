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

    # ---------- Login (M3) ----------

    # Secret used to sign login tokens and hash OTP codes. Must be long
    # and random; changing it logs everyone out. Empty = login refused.
    app_secret_key: str = ""

    # Where OTP codes go:
    #   "log"      - written to the server log only (dev in AWS: CloudWatch)
    #   "response" - also returned in the API reply, so the login page can
    #                show it. Only honoured when db_mode = "local".
    #   "email"    - emailed through Amazon SES (dev and prod).
    # Real SMS arrives with notifications (M12).
    otp_delivery: Literal["log", "response", "email"] = "log"

    # Verified SES sender address for login emails (MAIL_FROM).
    mail_from: str = ""

    # S3 bucket for warehouse photos (PHOTO_BUCKET). Empty = photos off.
    photo_bucket: str = ""

    # SES configuration set that reports bounces and complaints
    # (MAIL_CONFIGURATION_SET). Empty = no reports.
    mail_configuration_set: str = ""

    # Send the session cookie only over HTTPS. Set false for plain
    # http://localhost if your browser refuses the cookie.
    cookie_secure: bool = True

    # How long a login lasts before the user must log in again.
    session_days: int = 7


# lru_cache = read settings once, then reuse the same object everywhere.
@lru_cache
def get_settings() -> Settings:
    return Settings()
