import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.config import settings
from .embed import get_text_embedding, EMBEDDING_DIM

logger = logging.getLogger("qdrant_client")

_client: Optional[QdrantClient] = None

def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        if settings.QDRANT_URL and settings.QDRANT_API_KEY:
            logger.info(f"Connecting to Qdrant Cloud at {settings.QDRANT_URL}")
            _client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=15.0
            )
        else:
            logger.info("Connecting to local in-memory Qdrant instance for development/testing")
            _client = QdrantClient(":memory:")
    return _client

def init_qdrant_collection() -> bool:
    """Ensure the nabard_benchmarks collection exists in Qdrant."""
    client = get_qdrant_client()
    collection_name = settings.QDRANT_COLLECTION_NAME

    try:
        collections = client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        if not exists:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
            )
            logger.info(f"Created Qdrant collection '{collection_name}' with dim {EMBEDDING_DIM}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant collection: {e}")
        return False

def upsert_benchmarks(benchmarks: List[Dict[str, Any]]) -> int:
    """
    Embed and upsert NABARD benchmarks into Qdrant.
    Payload: {trade, district, state, capex, opex, annual_revenue, dscr, source, description}
    """
    client = get_qdrant_client()
    init_qdrant_collection()
    points = []

    for idx, item in enumerate(benchmarks):
        text_to_embed = f"Trade: {item.get('trade', '')}. District: {item.get('district', '')}, State: {item.get('state', '')}. {item.get('description', '')}"
        vector = get_text_embedding(text_to_embed)

        point_id = item.get("id") or idx + 1
        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=item
            )
        )

    client.upsert(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        points=points
    )
    logger.info(f"Upserted {len(points)} benchmarks into Qdrant collection '{settings.QDRANT_COLLECTION_NAME}'")
    return len(points)

def search_trade_benchmarks(trade: str, district: str = "", limit: int = 3) -> List[Dict[str, Any]]:
    """Retrieve top-k closest NABARD unit cost benchmarks matching trade and location."""
    client = get_qdrant_client()
    init_qdrant_collection()

    query_text = f"Trade: {trade}. District: {district}"
    query_vector = get_text_embedding(query_text)

    try:
        if hasattr(client, "query_points"):
            response = client.query_points(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query=query_vector,
                limit=limit
            )
            benchmarks = [hit.payload for hit in response.points if hit.payload]
        elif hasattr(client, "search"):
            results = client.search(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query_vector=query_vector,
                limit=limit
            )
            benchmarks = [hit.payload for hit in results if hit.payload]
        else:
            benchmarks = []
        return benchmarks
    except Exception as e:
        logger.error(f"Qdrant vector search failed: {e}")
        return []
