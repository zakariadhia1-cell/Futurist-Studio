"""Google OAuth connect/callback/status/disconnect. Calendar/Gmail *usage* happens
through Executive Agent tools (app/orchestrator/tools/calendar_email.py), not REST
endpoints here - this module is only about establishing/managing the connection."""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import crypto
from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, decode_token
from app.db.base import get_db
from app.integrations import google_oauth
from app.models.google_account import GoogleAccount
from app.models.user import User
from app.schemas.integrations import GoogleConnectResponse, GoogleStatusResponse

# Mounted under /auth/google (not /integrations/google) so the callback path is
# /api/v1/auth/google/callback - that's the exact value registered as an "Autorisierte
# Weiterleitungs-URI" in the Google Cloud Console OAuth client; it must match exactly.
router = APIRouter(prefix="/auth/google", tags=["integrations"])


@router.get("/status", response_model=GoogleStatusResponse)
async def google_status(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> GoogleStatusResponse:
    if not google_oauth.is_configured():
        return GoogleStatusResponse(configured=False, connected=False)
    result = await db.execute(select(GoogleAccount).where(GoogleAccount.user_id == user.id))
    account = result.scalar_one_or_none()
    return GoogleStatusResponse(
        configured=True, connected=account is not None, google_email=account.google_email if account else None
    )


@router.get("/connect", response_model=GoogleConnectResponse)
async def google_connect(user: User = Depends(get_current_user)) -> GoogleConnectResponse:
    if not google_oauth.is_configured():
        raise HTTPException(status_code=503, detail="Google OAuth ist nicht konfiguriert.")
    # The callback is hit directly by the browser via Google's redirect (no Authorization
    # header available there) - a short-lived signed JWT as `state` both identifies the
    # user and doubles as CSRF protection (an attacker can't forge a valid one).
    state = create_access_token(subject=str(user.id), extra_claims={"type": "google_oauth_state"})
    return GoogleConnectResponse(authorize_url=google_oauth.build_authorize_url(state))


@router.get("/callback")
async def google_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    settings = get_settings()
    frontend_origin = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:5173"

    def _redirect(result: str) -> RedirectResponse:
        return RedirectResponse(url=f"{frontend_origin}/settings?google={result}")

    if error or not code or not state:
        return _redirect("error")

    payload = decode_token(state)
    if payload is None or payload.get("type") != "google_oauth_state":
        return _redirect("error")

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        return _redirect("error")

    try:
        tokens = await google_oauth.exchange_code(code)
        userinfo = await google_oauth.get_userinfo(tokens["access_token"])
    except Exception:
        return _redirect("error")

    if "refresh_token" not in tokens:
        # Happens if the user has connected before and Google didn't re-issue one despite
        # prompt=consent (rare, but possible with certain account/org policies).
        return _redirect("error")

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))
    result = await db.execute(select(GoogleAccount).where(GoogleAccount.user_id == user_id))
    account = result.scalar_one_or_none()
    if account is None:
        account = GoogleAccount(user_id=user_id)
        db.add(account)

    account.google_email = userinfo.get("email", "")
    account.access_token_encrypted = crypto.encrypt(tokens["access_token"])
    account.refresh_token_encrypted = crypto.encrypt(tokens["refresh_token"])
    account.token_expires_at = expires_at
    account.scopes = tokens.get("scope", "")
    await db.commit()

    return _redirect("connected")


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def google_disconnect(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    result = await db.execute(select(GoogleAccount).where(GoogleAccount.user_id == user.id))
    account = result.scalar_one_or_none()
    if account is not None:
        await db.delete(account)
        await db.commit()
