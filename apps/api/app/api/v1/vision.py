"""Vision/OCR: describe or read text from an uploaded image.

Uses whichever model_config is both the default and vision-capable (falls back to the
first vision-capable one) - no separate vision-specific API key to configure, since this
reuses the same Anthropic/OpenAI credentials as chat.
"""
import base64

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.models.model_config import ModelConfig
from app.models.user import User
from app.models_provider import registry
from app.schemas.vision import ImageAnalysisResponse, OcrResponse

router = APIRouter(prefix="/vision", tags=["vision"])

_MAX_IMAGE_BYTES = 10 * 1024 * 1024
_OCR_INSTRUCTION = (
    "Extrahiere den gesamten sichtbaren Text aus diesem Bild woertlich, ohne Kommentar. "
    "Wenn kein Text erkennbar ist, antworte mit einem leeren String."
)


async def _get_vision_model_config(db: AsyncSession) -> ModelConfig:
    result = await db.execute(select(ModelConfig))
    configs = result.scalars().all()
    vision_configs = [c for c in configs if (c.capabilities or {}).get("vision")]
    if not vision_configs:
        raise HTTPException(status_code=503, detail="Kein vision-faehiges Modell konfiguriert.")
    for config in vision_configs:
        if config.is_default:
            return config
    return vision_configs[0]


async def _analyze(file: UploadFile, instruction: str, db: AsyncSession) -> str:
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Keine Bilddatei erhalten.")
    if len(image_bytes) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Bild ist zu gross (max. 10 MB).")

    model_config = await _get_vision_model_config(db)
    provider = registry.get_provider(model_config.provider)
    media_type = file.content_type or "image/png"
    image_b64 = base64.standard_b64encode(image_bytes).decode("ascii")

    try:
        return await provider.analyze_image(image_b64, media_type, instruction, model_config.model_name)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Bildanalyse fehlgeschlagen: {exc}") from exc


@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    instruction: str = Form("Beschreibe, was auf diesem Bild zu sehen ist."),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ImageAnalysisResponse:
    description = await _analyze(file, instruction, db)
    return ImageAnalysisResponse(description=description)


@router.post("/ocr", response_model=OcrResponse)
async def ocr(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> OcrResponse:
    text = await _analyze(file, _OCR_INSTRUCTION, db)
    return OcrResponse(text=text)
