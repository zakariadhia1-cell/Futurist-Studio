from pydantic import BaseModel


class TerminalSessionRead(BaseModel):
    id: str


class TerminalSessionList(BaseModel):
    sessions: list[str]
