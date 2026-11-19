from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..config import settings
from ..engines.llm_service import llm_service

router = APIRouter(prefix="/api/keys", tags=["API Keys & External Integrations"])

class UpdateKeysRequest(BaseModel):
    anthropicApiKey: Optional[str] = None
    geminiApiKey: Optional[str] = None
    openaiApiKey: Optional[str] = None
    slackWebhookUrl: Optional[str] = None

class TestKeyRequest(BaseModel):
    provider: str
    apiKey: str

@router.get("", response_model=dict)
def get_configured_keys():
    """Returns masked status of external API keys without exposing secrets."""
    return {
        "status": "ok",
        "keys": settings.get_masked_keys()
    }

@router.post("", response_model=dict)
def save_configured_keys(payload: UpdateKeysRequest):
    """Saves API keys to local environment and .env configuration."""
    update_dict = {}
    if payload.anthropicApiKey is not None:
        update_dict["ANTHROPIC_API_KEY"] = payload.anthropicApiKey
    if payload.geminiApiKey is not None:
        update_dict["GEMINI_API_KEY"] = payload.geminiApiKey
    if payload.openaiApiKey is not None:
        update_dict["OPENAI_API_KEY"] = payload.openaiApiKey
    if payload.slackWebhookUrl is not None:
        update_dict["SLACK_WEBHOOK_URL"] = payload.slackWebhookUrl

    success = settings.save_keys(update_dict)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save keys to .env")

    return {
        "success": True,
        "message": "API keys updated and saved to .env",
        "keys": settings.get_masked_keys()
    }

@router.post("/test", response_model=dict)
def test_external_key(payload: TestKeyRequest):
    """Pings the external provider to verify API key validity."""
    result = llm_service.test_key(payload.provider, payload.apiKey)
    return result
