"""Resolves a provider slug (as stored in model_configs.provider) to a ModelProvider instance."""
from app.core.config import get_settings
from app.models_provider.anthropic_provider import AnthropicProvider
from app.models_provider.base import ModelProvider
from app.models_provider.ollama_provider import OllamaProvider
from app.models_provider.openai_provider import OpenAIProvider

_SUPPORTED_PROVIDERS = ("openai", "anthropic", "ollama")


def get_provider(provider: str) -> ModelProvider:
    settings = get_settings()
    if provider == "openai":
        return OpenAIProvider(api_key=settings.OPENAI_API_KEY)
    if provider == "anthropic":
        return AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY)
    if provider == "ollama":
        return OllamaProvider(base_url=settings.OLLAMA_BASE_URL)
    raise ValueError(f"Unbekannter Model-Provider: '{provider}'. Unterstuetzt: {_SUPPORTED_PROVIDERS}")
