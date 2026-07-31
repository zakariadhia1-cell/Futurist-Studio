from pydantic import BaseModel


class ImageAnalysisResponse(BaseModel):
    description: str


class OcrResponse(BaseModel):
    text: str
