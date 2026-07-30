"""Google OAuth (Calendar + Gmail scopes) - authorization-code flow via direct REST calls
to Google's endpoints, no googleapiclient SDK. Consistent with the rest of this codebase's
integrations (call_api, seo_analyze, n8n) - they all speak REST directly via httpx rather
than pulling in provider-specific SDKs.
"""
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

SCOPES = [
    "openid",
    "email",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


def is_configured() -> bool:
    settings = get_settings()
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def build_authorize_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        # offline + consent: without both, Google only ever returns a refresh_token on
        # a user's very first-ever consent for this app - reconnecting after a revoke
        # would otherwise silently fail to get one.
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_userinfo(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        resp.raise_for_status()
        return resp.json()
