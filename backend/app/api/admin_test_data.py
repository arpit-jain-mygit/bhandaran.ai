# ---------------------------------------------------------------
# Delete test data (admin only). Two steps, so nothing is removed by
# accident:
#
#   POST /api/admin/test-data/preview  {emails, warehouse_ids}
#       -> what would be removed (nothing is deleted)
#   POST /api/admin/test-data/delete   {emails, warehouse_ids, confirm: "DELETE"}
#       -> removes it
#
# See app/cleanup.py for the rules.
# ---------------------------------------------------------------
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import cleanup
from app.api.common import commit_or_409
from app.auth import require_admin
from app.db import get_session
from app.models import User
from app.schemas.cleanup import CleanupDeleteIn, CleanupIn, CleanupOut

router = APIRouter(prefix="/api/admin/test-data", tags=["admin test data"])

DbSession = Annotated[Session, Depends(get_session)]
AdminUser = Annotated[User, Depends(require_admin)]


def summary(chosen: cleanup.Plan, *, deleted: bool, photo_files_left: int = 0) -> CleanupOut:
    return CleanupOut(
        accounts=chosen.accounts,
        missing_emails=chosen.missing_emails,
        warehouses=len(chosen.warehouse_ids),
        missing_warehouse_ids=chosen.missing_warehouse_ids,
        bookings=chosen.bookings,
        photos=len(chosen.photo_keys),
        login_codes=chosen.login_codes,
        owner_settings=chosen.owner_settings,
        suppressed_emails=chosen.suppressed_emails,
        invitees_released=chosen.invitees_released,
        deleted=deleted,
        photo_files_left=photo_files_left,
    )


@router.post("/preview", response_model=CleanupOut)
def preview(body: CleanupIn, admin: AdminUser, session: DbSession):
    chosen = cleanup.plan(
        session, admin=admin, raw_emails=body.emails, warehouse_ids=body.warehouse_ids
    )
    return summary(chosen, deleted=False)


@router.post("/delete", response_model=CleanupOut)
def delete(body: CleanupDeleteIn, admin: AdminUser, session: DbSession):
    chosen = cleanup.plan(
        session, admin=admin, raw_emails=body.emails, warehouse_ids=body.warehouse_ids
    )
    if not chosen.user_ids and not chosen.warehouse_ids:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nothing matches those emails or IDs")

    photo_keys = cleanup.remove(session, chosen)
    commit_or_409(session, "Something changed at the same time, try again")
    # Files go only after the rows are gone, so a failed delete never
    # leaves a photo row pointing at a deleted file.
    failed = cleanup.delete_photo_files(photo_keys)
    return summary(chosen, deleted=True, photo_files_left=failed)
