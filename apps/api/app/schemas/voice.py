from pydantic import BaseModel


class TranscriptionResponse(BaseModel):
    text: str


class SpeakRequest(BaseModel):
    text: str
