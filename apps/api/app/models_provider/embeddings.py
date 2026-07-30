"""Embedding provider interface, mirroring ModelProvider's provider-agnostic shape."""
from abc import ABC, abstractmethod

EMBEDDING_DIM = 1536  # matches document_chunks.embedding / memory_facts.embedding column width


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector (length EMBEDDING_DIM) per input text, same order."""
        raise NotImplementedError
