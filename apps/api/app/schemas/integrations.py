from pydantic import BaseModel


class GoogleConnectResponse(BaseModel):
    authorize_url: str


class GoogleStatusResponse(BaseModel):
    configured: bool
    connected: bool
    google_email: str | None = None
