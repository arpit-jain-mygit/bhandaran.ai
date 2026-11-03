# ---------------------------------------------------------------
# Helpers shared by several API modules.
# ---------------------------------------------------------------
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session


def commit_or_409(session: Session, conflict_message: str) -> None:
    """
    Save changes. Two kinds of failure become HTTP 409 (Conflict):
      - IntegrityError: a unique rule was broken (duplicate code/name)
      - SQLSTATE 40001: DSQL optimistic-concurrency conflict; the
        client can simply try again
    """
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, conflict_message) from error
    except OperationalError as error:
        session.rollback()
        if getattr(error.orig, "sqlstate", None) == "40001":
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Changed by someone else at the same time, try again"
            ) from error
        raise
