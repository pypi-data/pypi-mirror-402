"""Embedding generation for semantic search."""

from .local import (
    DEFAULT_MODEL_NAME,
    EMBEDDING_DIMENSIONS,
    generate_embedding,
    generate_embeddings_batch,
    generate_and_store_embedding,
    get_embedding,
    get_all_embeddings,
    store_embedding,
    delete_embedding,
    vector_to_blob,
    blob_to_vector,
    get_memories_without_embeddings,
    backfill_embeddings,
    is_model_available,
)

__all__ = [
    "DEFAULT_MODEL_NAME",
    "EMBEDDING_DIMENSIONS",
    "generate_embedding",
    "generate_embeddings_batch",
    "generate_and_store_embedding",
    "get_embedding",
    "get_all_embeddings",
    "store_embedding",
    "delete_embedding",
    "vector_to_blob",
    "blob_to_vector",
    "get_memories_without_embeddings",
    "backfill_embeddings",
    "is_model_available",
]
