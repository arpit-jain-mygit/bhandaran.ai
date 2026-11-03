# ---------------------------------------------------------------
# Warehouse photos in S3 (M5). The browser uploads straight to S3
# with a short-lived presigned PUT link, so photo bytes never pass
# through the Lambda. Photos stay private: viewing uses presigned
# GET links that expire after an hour.
# ---------------------------------------------------------------
import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

MAX_PHOTO_BYTES = 5 * 1024 * 1024
UPLOAD_LINK_SECONDS = 600
VIEW_LINK_SECONDS = 3600

# Content type -> file extension for the S3 key.
ALLOWED_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def _s3():
    return boto3.client("s3", region_name=get_settings().aws_region)


def upload_link(key: str, content_type: str) -> str:
    """A link the browser can PUT one photo to, for UPLOAD_LINK_SECONDS."""
    return _s3().generate_presigned_url(
        "put_object",
        Params={"Bucket": get_settings().photo_bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=UPLOAD_LINK_SECONDS,
    )


def view_link(key: str) -> str:
    """A link the browser can GET the photo from, for VIEW_LINK_SECONDS."""
    return _s3().generate_presigned_url(
        "get_object",
        Params={"Bucket": get_settings().photo_bucket, "Key": key},
        ExpiresIn=VIEW_LINK_SECONDS,
    )


def stored_object(key: str) -> dict | None:
    """Size and type of the uploaded object, or None if it isn't there."""
    try:
        head = _s3().head_object(Bucket=get_settings().photo_bucket, Key=key)
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
            return None
        raise
    except BotoCoreError:
        raise
    return {"size": head["ContentLength"], "content_type": head.get("ContentType")}


def delete_object(key: str) -> None:
    _s3().delete_object(Bucket=get_settings().photo_bucket, Key=key)
