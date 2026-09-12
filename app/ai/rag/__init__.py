"""RAG module using local embeddings and Qdrant."""
from .embed import get_text_embedding, get_batch_embeddings, EMBEDDING_DIM
from .qdrant_client import init_qdrant_collection, search_trade_benchmarks, upsert_benchmarks

__all__ = [
    "get_text_embedding",
    "get_batch_embeddings",
    "EMBEDDING_DIM",
    "init_qdrant_collection",
    "search_trade_benchmarks",
    "upsert_benchmarks",
]
