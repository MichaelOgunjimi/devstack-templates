"""Async Elasticsearch client wrapper.

Usage:
    from services.search import search_client, index_document, search_documents

    # Index a document
    await index_document("products", "123", {"name": "Widget", "price": 9.99})

    # Search
    hits = await search_documents("products", {"match": {"name": "widget"}})

Requires ELASTICSEARCH_URL in .env (set by `devstack add elasticsearch`).
"""

import structlog
from elasticsearch import AsyncElasticsearch

from core.config import settings

logger = structlog.get_logger(__name__)

search_client = AsyncElasticsearch(settings.ELASTICSEARCH_URL)


async def index_document(index: str, doc_id: str, body: dict) -> dict:
    """Index a single document."""
    logger.info("search.index", index=index, doc_id=doc_id)
    result = await search_client.index(index=index, id=doc_id, document=body)
    return dict(result)


async def delete_document(index: str, doc_id: str) -> dict:
    """Delete a document by ID."""
    logger.info("search.delete", index=index, doc_id=doc_id)
    result = await search_client.delete(index=index, id=doc_id, ignore=[404])
    return dict(result)


async def search_documents(
    index: str,
    query: dict,
    *,
    size: int = 10,
    from_: int = 0,
) -> list[dict]:
    """Run a search query and return hits."""
    logger.info("search.query", index=index, size=size)
    result = await search_client.search(
        index=index,
        query=query,
        size=size,
        from_=from_,
    )
    return [hit["_source"] for hit in result["hits"]["hits"]]


async def ensure_index(index: str, mappings: dict | None = None) -> None:
    """Create an index if it doesn't exist."""
    exists = await search_client.indices.exists(index=index)
    if not exists:
        body: dict = {}
        if mappings:
            body["mappings"] = mappings
        await search_client.indices.create(index=index, body=body)
        logger.info("search.index_created", index=index)


async def close_client() -> None:
    """Close the Elasticsearch client (call on app shutdown)."""
    await search_client.close()
