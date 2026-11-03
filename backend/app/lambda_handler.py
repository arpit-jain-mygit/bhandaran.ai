# ---------------------------------------------------------------
# AWS Lambda entry point.
# API Gateway sends each HTTP request to Lambda as an "event";
# Mangum converts that event into a normal ASGI request for FastAPI
# and converts FastAPI's response back. The same app runs locally
# with uvicorn and in AWS with this handler.
#
# Lambda setting: handler = app.lambda_handler.handler
# ---------------------------------------------------------------
from mangum import Mangum

from app.main import app

# lifespan="off": the app has no startup/shutdown hooks to run.
handler = Mangum(app, lifespan="off")
