"""Authenticated Calendar/Gmail REST calls for a user's connected Google account, with
automatic access-token refresh. No local sync/cache of events or emails - every call goes
live to Google. Simpler and always up to date; a local `calendar_events`/`emails` mirror
(as sketched in the architecture doc) would need its own sync engine and conflict
handling, which isn't worth the complexity for a personal-use assistant that just needs
to read/create a handful of items per request.
"""
import base64
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import crypto
from app.integrations import google_oauth
from app.models.google_account import GoogleAccount

CALENDAR_API = "https://www.googleapis.com/calendar/v3"
GMAIL_API = "https://gmail.googleapis.com/gmail/v1"


async def get_valid_access_token(db: AsyncSession, account: GoogleAccount) -> str:
    now = datetime.now(timezone.utc)
    if account.token_expires_at > now + timedelta(seconds=60):
        return crypto.decrypt(account.access_token_encrypted)

    refresh_token = crypto.decrypt(account.refresh_token_encrypted)
    tokens = await google_oauth.refresh_access_token(refresh_token)
    account.access_token_encrypted = crypto.encrypt(tokens["access_token"])
    account.token_expires_at = now + timedelta(seconds=tokens.get("expires_in", 3600))
    await db.commit()
    return tokens["access_token"]


async def list_calendar_events(db: AsyncSession, account: GoogleAccount, *, max_results: int = 10) -> list[dict]:
    token = await get_valid_access_token(db, account)
    now = datetime.now(timezone.utc)
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{CALENDAR_API}/calendars/primary/events",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "timeMin": now.isoformat(),
                "maxResults": max_results,
                "singleEvents": "true",
                "orderBy": "startTime",
            },
        )
        resp.raise_for_status()
    return resp.json().get("items", [])


async def create_calendar_event(
    db: AsyncSession,
    account: GoogleAccount,
    *,
    summary: str,
    start_iso: str,
    end_iso: str,
    description: str | None = None,
) -> dict:
    token = await get_valid_access_token(db, account)
    body = {
        "summary": summary,
        "start": {"dateTime": start_iso},
        "end": {"dateTime": end_iso},
    }
    if description:
        body["description"] = description
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{CALENDAR_API}/calendars/primary/events",
            headers={"Authorization": f"Bearer {token}"},
            json=body,
        )
        resp.raise_for_status()
    return resp.json()


async def list_recent_messages(db: AsyncSession, account: GoogleAccount, *, max_results: int = 10) -> list[dict]:
    token = await get_valid_access_token(db, account)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=15) as client:
        list_resp = await client.get(
            f"{GMAIL_API}/users/me/messages", headers=headers, params={"maxResults": max_results}
        )
        list_resp.raise_for_status()
        message_ids = [m["id"] for m in list_resp.json().get("messages", [])]

        messages = []
        for message_id in message_ids:
            detail_resp = await client.get(
                f"{GMAIL_API}/users/me/messages/{message_id}",
                headers=headers,
                params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]},
            )
            detail_resp.raise_for_status()
            data = detail_resp.json()
            header_map = {h["name"]: h["value"] for h in data.get("payload", {}).get("headers", [])}
            messages.append(
                {
                    "id": message_id,
                    "from": header_map.get("From", ""),
                    "subject": header_map.get("Subject", "(kein Betreff)"),
                    "date": header_map.get("Date", ""),
                    "snippet": data.get("snippet", ""),
                }
            )
        return messages


async def send_email(db: AsyncSession, account: GoogleAccount, *, to: str, subject: str, body: str) -> dict:
    token = await get_valid_access_token(db, account)
    mime_message = MIMEText(body)
    mime_message["to"] = to
    mime_message["subject"] = subject
    raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{GMAIL_API}/users/me/messages/send",
            headers={"Authorization": f"Bearer {token}"},
            json={"raw": raw},
        )
        resp.raise_for_status()
    return resp.json()
