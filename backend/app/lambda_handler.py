# ---------------------------------------------------------------
# AWS Lambda entry point.
# API Gateway sends each HTTP request to Lambda as an "event";
# Mangum converts that event into a normal ASGI request for FastAPI
# and converts FastAPI's response back. The same app runs locally
# with uvicorn and in AWS with this handler.
#
# Keep-warm: an EventBridge schedule (infra/modules/api_lambda) sends
# {"warmup": true} every few minutes. That keeps this Lambda instance
# and its database connection alive, so real visitors rarely hit a
# slow "cold start". It never goes through API Gateway.
#
# Lambda setting: handler = app.lambda_handler.handler
# ---------------------------------------------------------------
import logging

from mangum import Mangum
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import get_engine
from app.main import app

logger = logging.getLogger(__name__)

# lifespan="off": the app has no startup/shutdown hooks to run.
asgi_handler = Mangum(app, lifespan="off")


def warm_up() -> dict:
    """Run the cheapest query so the pooled DB connection stays open."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"warm": True}
    except SQLAlchemyError as error:
        # Don't fail the schedule; the next real request reconnects.
        logger.warning("Warm-up database ping failed: %s", error)
        return {"warm": False}


def handler(event, context):
    """Lambda calls this for every event (HTTP request or warm-up ping)."""
    if isinstance(event, dict) and event.get("warmup") is True:
        return warm_up()
    return asgi_handler(event, context)
