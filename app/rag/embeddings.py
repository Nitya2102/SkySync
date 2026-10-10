"""Embedding helper with local sentence-transformers and graceful degradation."""
from __future__ import annotations

import logging
from typing import Optional
import numpy as np

from app.config import EMBED_MODEL

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages sentence-transformers embeddings with graceful BM25 fallback."""

    def __init__(self, model_name: str = EMBED_MODEL):
        self.model_name = model_name
        self._model = None
        self._is_available = False
        self._initialized = False

    def initialize(self) -> bool:
        if self._initialized:
            return self._is_available

        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Attempting to load sentence-transformers model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
            self._is_available = True
            logger.info("SentenceTransformer '%s' successfully loaded.", self.model_name)
        except Exception as e:
            logger.warning(
                "Could not load SentenceTransformer '%s': %s. Degraded to BM25-only.",
                self.model_name,
                e,
            )
            self._model = None
            self._is_available = False
        finally:
            self._initialized = True

        return self._is_available

    @property
    def is_available(self) -> bool:
        if not self._initialized:
            self.initialize()
        return self._is_available

    def encode(self, texts: list[str]) -> Optional[np.ndarray]:
        if not self.is_available or self._model is None:
            return None
        try:
            embeddings = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            logger.warning("Error encoding texts with SentenceTransformer: %s", e)
            return None

    def encode_query(self, query: str) -> Optional[np.ndarray]:
        res = self.encode([query])
        if res is not None and len(res) > 0:
            return res[0]
        return None


# Global singleton
embedding_manager = EmbeddingManager()
