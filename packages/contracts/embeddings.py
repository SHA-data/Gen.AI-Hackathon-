"""Embedding Provider protocol and Fake implementation."""
import hashlib
from typing import List, Protocol

class EmbeddingProvider(Protocol):
    """Protocol for generating vector embeddings."""
    async def embed_text(self, text: str) -> List[float]:
        ...

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        ...

class FakeEmbeddingProvider:
    """Generates deterministic pseudo-normalized 1536-dimensional embeddings."""
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    def _hash_to_vector(self, text: str) -> List[float]:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = []
        for i in range(self.dimension):
            byte_val = h[i % len(h)]
            # normalize to [-1.0, 1.0]
            val = (byte_val / 127.5) - 1.0
            vec.append(round(val, 4))
        # Norm approximation
        norm = sum(x * x for x in vec) ** 0.5 or 1.0
        return [round(x / norm, 4) for x in vec]

    async def embed_text(self, text: str) -> List[float]:
        return self._hash_to_vector(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_to_vector(t) for t in texts]
