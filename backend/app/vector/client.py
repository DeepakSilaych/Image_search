from functools import lru_cache

from qdrant_client import QdrantClient

from app.config import get_settings


@lru_cache
def get_qdrant() -> QdrantClient:
    return QdrantClient(url=get_settings().qdrant_url)
