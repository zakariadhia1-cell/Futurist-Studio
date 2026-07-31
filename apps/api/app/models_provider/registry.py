"""Resolves a provider slug (as stored in model_configs.provider) to a ModelProvider instance."""
from app.core.config import get_settings
from app.models_provider.anthropic_provider import AnthropicProvider
from app.models_provider.base import ModelProvider
from app.models_provider.embeddings import EmbeddingProvider
from app.models_provider.fake_embeddings import FakeEmbeddingProvider
from app.models_provider.ollama_provider import OllamaProvider
from app.models_provider.openai_embeddings import OpenAIEmbeddingProvider
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


def get_embedding_provider() -> EmbeddingProvider:
    """OpenAI if configured (real semantic embeddings); otherwise a deterministic
    bag-of-words fallback so the knowledge base still works with zero setup."""
    settings = get_settings()
    if settings.OPENAI_API_KEY:
        return OpenAIEmbeddingProvider(api_key=settings.OPENAI_API_KEY)
    return FakeEmbeddingProvider()
