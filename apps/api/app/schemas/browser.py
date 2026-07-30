from pydantic import BaseModel


class BrowserSessionRead(BaseModel):
    id: str


class BrowserSessionList(BaseModel):
    sessions: list[str]
