import hashlib
import math
import logging
from typing import List

logger = logging.getLogger("fastembed_embedder")

EMBEDDING_DIM = 384
MODEL_NAME = "BAAI/bge-small-en-v1.5"

_model = None

def _get_fastembed_model():
    global _model
    if _model is None:
        try:
            from fastembed import TextEmbedding
            _model = TextEmbedding(model_name=MODEL_NAME)
            logger.info(f"Loaded local FastEmbed model: {MODEL_NAME}")
        except Exception as e:
            logger.warning(f"FastEmbed not loaded ({e}). Using deterministic 384-dim fallback.")
            _model = False
    return _model

def _deterministic_fallback_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """Fallback deterministic 384-dim vector for testing/offline CPU environments."""
    words = text.lower().split()
    vector = [0.0] * dim
    for i, word in enumerate(words):
        h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        val = ((h >> 8) % 1000) / 500.0 - 1.0
        vector[idx] += val
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [round(x / norm, 6) for x in vector]

def get_text_embedding(text: str) -> List[float]:
    """Generate 384-dim embedding using local FastEmbed bge-small-en-v1.5."""
    model = _get_fastembed_model()
    if model and model is not False:
        try:
            embeddings = list(model.embed([text]))
            return embeddings[0].tolist()
        except Exception as e:
            logger.error(f"FastEmbed embedding generation failed: {e}")
    return _deterministic_fallback_embedding(text)

def get_batch_embeddings(texts: List[str]) -> List[List[float]]:
    """Batch embed texts locally without network calls."""
    model = _get_fastembed_model()
    if model and model is not False:
        try:
            embeddings = list(model.embed(texts))
            return [e.tolist() for e in embeddings]
        except Exception as e:
            logger.error(f"FastEmbed batch failed: {e}")
    return [_deterministic_fallback_embedding(t) for t in texts]
