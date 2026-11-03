# ---------------------------------------------------------------
# Platform-settings API (M2). See app/platform_settings.py.
#
#   GET    /api/settings                        all settings + platform values
#   PUT    /api/settings/{key}        {value}   set platform value     [admin]
#   DELETE /api/settings/{key}                  back to code default   [admin]
#
#   GET    /api/settings/owners/{owner_id}               effective values for an owner
#   PUT    /api/settings/owners/{owner_id}/{key} {value} set owner override  [admin*]
#   DELETE /api/settings/owners/{owner_id}/{key}         remove override     [admin*]
#
# * TEMPORARY: until owner login exists (M3/M4), the admin key sets
#   owner overrides. Later, owners change their own.
# ---------------------------------------------------------------
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.common import commit_or_409
from app.auth import require_admin
from app.db import get_session
from app.models import OwnerSetting, PlatformSetting
from app.platform_settings import (
    SETTINGS,
    SettingDef,
    effective_settings,
    to_stored,
    validate_value,
)
from app.schemas.settings import EffectiveSettingOut, SettingOut, SettingValueIn

router = APIRouter(prefix="/api/settings", tags=["platform settings"])

DbSession = Annotated[Session, Depends(get_session)]
AdminOnly = Depends(require_admin)


# ---------- helpers ----------


def setting_or_404(key: str) -> SettingDef:
    setting = SETTINGS.get(key)
    if setting is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown setting '{key}'")
    return setting


def checked_value(setting: SettingDef, body: SettingValueIn):
    """Validate against the setting's rules; bad values become HTTP 422."""
    try:
        return validate_value(setting, body.value)
    except ValueError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f"{setting.key} {error}"
        ) from error


def platform_view(session: Session) -> list[SettingOut]:
    effective = effective_settings(session)
    return [
        SettingOut(
            key=s.key,
            label=s.label,
            description=s.description,
            type=s.type,
            choices=list(s.choices),
            min=s.min,
            max=s.max,
            owner_can_override=s.owner_can_override,
            default=s.default,
            value=effective[s.key].value,
            source=effective[s.key].source,  # "platform" or "default" here
        )
        for s in SETTINGS.values()
    ]


def owner_view(session: Session, owner_id: uuid.UUID) -> list[EffectiveSettingOut]:
    effective = effective_settings(session, owner_id)
    return [
        EffectiveSettingOut(
            key=key, label=SETTINGS[key].label, value=item.value, source=item.source
        )
        for key, item in effective.items()
    ]


# ---------- platform-wide ----------


@router.get("", response_model=list[SettingOut])
def list_settings(session: DbSession):
    return platform_view(session)


@router.put("/{key}", response_model=list[SettingOut], dependencies=[AdminOnly])
def set_platform_value(key: str, body: SettingValueIn, session: DbSession):
    setting = setting_or_404(key)
    stored = to_stored(checked_value(setting, body))

    row = session.get(PlatformSetting, key)
    if row is None:
        session.add(PlatformSetting(key=key, value=stored))
    else:
        row.value = stored
    commit_or_409(session, "Setting was changed at the same time, try again")
    return platform_view(session)


@router.delete("/{key}", response_model=list[SettingOut], dependencies=[AdminOnly])
def reset_platform_value(key: str, session: DbSession):
    setting_or_404(key)
    row = session.get(PlatformSetting, key)
    if row is not None:
        session.delete(row)
        commit_or_409(session, "Setting was changed at the same time, try again")
    return platform_view(session)


# ---------- per owner ----------


@router.get("/owners/{owner_id}", response_model=list[EffectiveSettingOut])
def list_owner_settings(owner_id: uuid.UUID, session: DbSession):
    return owner_view(session, owner_id)


@router.put(
    "/owners/{owner_id}/{key}",
    response_model=list[EffectiveSettingOut],
    dependencies=[AdminOnly],
)
def set_owner_value(owner_id: uuid.UUID, key: str, body: SettingValueIn, session: DbSession):
    setting = setting_or_404(key)
    if not setting.owner_can_override:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Owners can't change '{key}'")
    stored = to_stored(checked_value(setting, body))

    row = session.scalar(
        select(OwnerSetting).where(OwnerSetting.owner_id == owner_id, OwnerSetting.key == key)
    )
    if row is None:
        session.add(OwnerSetting(owner_id=owner_id, key=key, value=stored))
    else:
        row.value = stored
    commit_or_409(session, "Setting was changed at the same time, try again")
    return owner_view(session, owner_id)


@router.delete(
    "/owners/{owner_id}/{key}",
    response_model=list[EffectiveSettingOut],
    dependencies=[AdminOnly],
)
def reset_owner_value(owner_id: uuid.UUID, key: str, session: DbSession):
    setting_or_404(key)
    row = session.scalar(
        select(OwnerSetting).where(OwnerSetting.owner_id == owner_id, OwnerSetting.key == key)
    )
    if row is not None:
        session.delete(row)
        commit_or_409(session, "Setting was changed at the same time, try again")
    return owner_view(session, owner_id)
