"""Multilingual embeddings using sentence-transformers. Extensible for semantic search."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_embedding_model = None
_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def get_embedding_model():
    """Lazy-load the embedding model (heavy)."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _embedding_model = SentenceTransformer(_MODEL_NAME)
            logger.info("Loaded embedding model: %s", _MODEL_NAME)
        except Exception as e:
            logger.warning("Could not load sentence-transformers: %s", e)
    return _embedding_model


def compute_embedding(text: str) -> Optional[list[float]]:
    """Compute multilingual embedding for text. Returns None if model unavailable."""
    model = get_embedding_model()
    if model is None:
        return None
    try:
        return model.encode(text, convert_to_numpy=True).tolist()
    except Exception as e:
        logger.warning("Embedding failed: %s", e)
        return None
