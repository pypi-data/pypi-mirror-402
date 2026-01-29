"""Local embedding generation using sentence-transformers.

This module provides embedding generation with robust timeout handling
to prevent hangs during model loading. The model loading happens in a
subprocess that can be killed if it takes too long.
"""

import json
import logging
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np

from ..utils.ids import generate_embedding_id
from ..utils.timestamps import now_iso

logger = logging.getLogger(__name__)

# Model configuration
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384
EMBEDDING_TIMEOUT = 60  # seconds - timeout for embedding generation

# Security: allowed model name pattern (alphanumeric, hyphens, underscores, forward slashes for org/model)
MODEL_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-/]+$')


def is_model_available() -> bool:
    """Check if sentence-transformers is available.

    Returns:
        True if the package is installed
    """
    try:
        import sentence_transformers
        return True
    except ImportError:
        return False


def _validate_model_name(model_name: str) -> None:
    """Validate model name to prevent code injection.

    Args:
        model_name: The model name to validate

    Raises:
        ValueError: If model name contains invalid characters
    """
    if not MODEL_NAME_PATTERN.match(model_name):
        raise ValueError(
            f"Invalid model name '{model_name}'. "
            "Model names may only contain letters, numbers, hyphens, underscores, and forward slashes."
        )


def _generate_embedding_subprocess(text: str, model_name: str, timeout: float) -> Optional[np.ndarray]:
    """Generate embedding using a subprocess with timeout.

    This runs the embedding generation in a completely separate process
    that can be killed if it hangs during model loading.

    Args:
        text: Text to embed
        model_name: Model name
        timeout: Timeout in seconds

    Returns:
        Numpy array of embedding values, or None if failed/timed out
    """
    # Validate model name to prevent code injection
    _validate_model_name(model_name)

    # Python script to run in subprocess
    script = f'''
import sys
import json
import numpy as np

try:
    from sentence_transformers import SentenceTransformer

    # Load model and generate embedding
    model = SentenceTransformer("{model_name}")
    embedding = model.encode(sys.stdin.read(), convert_to_numpy=True)

    # Output as JSON list
    print(json.dumps(embedding.tolist()))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
    sys.exit(1)
'''

    try:
        # Run embedding generation in subprocess
        result = subprocess.run(
            [sys.executable, "-c", script],
            input=text,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logger.error(f"Embedding subprocess failed: {error_msg}")
            return None

        # Parse output
        output = result.stdout.strip()
        if not output:
            logger.error("Embedding subprocess returned empty output")
            return None

        data = json.loads(output)

        if isinstance(data, dict) and "error" in data:
            logger.error(f"Embedding generation error: {data['error']}")
            return None

        return np.array(data, dtype=np.float32)

    except subprocess.TimeoutExpired:
        logger.warning(f"Embedding generation timed out after {timeout}s")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse embedding output: {e}")
        return None
    except Exception as e:
        logger.error(f"Embedding subprocess error: {e}")
        return None


def generate_embedding(
    text: str,
    model_name: str = DEFAULT_MODEL_NAME,
    timeout: float = EMBEDDING_TIMEOUT,
) -> np.ndarray:
    """Generate embedding for a text string.

    Uses subprocess with timeout to prevent hangs during model loading.

    Args:
        text: Text to embed
        model_name: Name of the model to use
        timeout: Timeout in seconds

    Returns:
        Numpy array of embedding values (384 dimensions)

    Raises:
        RuntimeError: If embedding generation fails or times out
    """
    if not is_model_available():
        raise ImportError(
            "sentence-transformers is required for embeddings. "
            "Install with: pip install sentence-transformers"
        )

    embedding = _generate_embedding_subprocess(text, model_name, timeout)

    if embedding is None:
        raise RuntimeError(
            f"Embedding generation failed or timed out after {timeout}s. "
            "This may happen on first run while the model downloads (~90MB). "
            "Try again or disable embeddings with embedding_enabled: false in config."
        )

    return embedding


def generate_embeddings_batch(
    texts: list[str],
    model_name: str = DEFAULT_MODEL_NAME,
    timeout: float = EMBEDDING_TIMEOUT,
) -> list[np.ndarray]:
    """Generate embeddings for multiple texts.

    Note: Currently processes one at a time for reliability.
    Batch processing could be added later for performance.

    Args:
        texts: List of texts to embed
        model_name: Name of the model to use
        timeout: Timeout per text in seconds

    Returns:
        List of embedding arrays (may be shorter than input if some fail)
    """
    embeddings = []
    for text in texts:
        try:
            embedding = generate_embedding(text, model_name, timeout)
            embeddings.append(embedding)
        except Exception as e:
            logger.warning(f"Failed to generate embedding: {e}")
            # Continue with remaining texts
    return embeddings


def vector_to_blob(vector: np.ndarray) -> bytes:
    """Convert numpy array to SQLite BLOB.

    Args:
        vector: Numpy array of float32 values

    Returns:
        Bytes representation
    """
    vector = vector.astype(np.float32)
    return vector.tobytes()


def blob_to_vector(blob: bytes) -> np.ndarray:
    """Convert SQLite BLOB to numpy array.

    Args:
        blob: Bytes from database

    Returns:
        Numpy array of float32 values
    """
    return np.frombuffer(blob, dtype=np.float32)


def store_embedding(
    conn: sqlite3.Connection,
    memory_id: str,
    vector: np.ndarray,
    model_name: str = DEFAULT_MODEL_NAME,
) -> str:
    """Store an embedding in the database.

    Args:
        conn: Database connection
        memory_id: ID of the memory
        vector: Embedding vector
        model_name: Model used to generate the embedding

    Returns:
        Embedding ID
    """
    embedding_id = generate_embedding_id()
    blob = vector_to_blob(vector)

    cursor = conn.cursor()

    # Insert or replace embedding
    cursor.execute(
        """
        INSERT OR REPLACE INTO embeddings (id, memory_id, model_name, vector, dimensions, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (embedding_id, memory_id, model_name, blob, len(vector), now_iso()),
    )

    # Update memory's has_embedding flag
    cursor.execute(
        "UPDATE memories SET has_embedding = 1 WHERE id = ?",
        (memory_id,),
    )

    conn.commit()
    return embedding_id


def get_embedding(
    conn: sqlite3.Connection,
    memory_id: str,
) -> Optional[np.ndarray]:
    """Get the embedding for a memory.

    Args:
        conn: Database connection
        memory_id: Memory ID

    Returns:
        Embedding vector or None if not found
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT vector FROM embeddings WHERE memory_id = ?",
        (memory_id,),
    )
    row = cursor.fetchone()

    if not row:
        return None

    return blob_to_vector(row["vector"])


def get_all_embeddings(
    conn: sqlite3.Connection,
) -> list[tuple[str, np.ndarray]]:
    """Get all embeddings from the database.

    Returns:
        List of (memory_id, vector) tuples
    """
    cursor = conn.cursor()
    cursor.execute("SELECT memory_id, vector FROM embeddings")

    results = []
    for row in cursor.fetchall():
        vector = blob_to_vector(row["vector"])
        results.append((row["memory_id"], vector))

    return results


def delete_embedding(
    conn: sqlite3.Connection,
    memory_id: str,
) -> bool:
    """Delete embedding for a memory.

    Args:
        conn: Database connection
        memory_id: Memory ID

    Returns:
        True if deleted
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM embeddings WHERE memory_id = ?", (memory_id,))

    if cursor.rowcount > 0:
        cursor.execute(
            "UPDATE memories SET has_embedding = 0 WHERE id = ?",
            (memory_id,),
        )
        conn.commit()
        return True

    return False


def generate_and_store_embedding(
    conn: sqlite3.Connection,
    memory_id: str,
    content: str,
    context: Optional[str] = None,
    model_name: str = DEFAULT_MODEL_NAME,
    timeout: float = EMBEDDING_TIMEOUT,
) -> Optional[str]:
    """Generate and store embedding for a memory.

    Args:
        conn: Database connection
        memory_id: Memory ID
        content: Memory content
        context: Optional context
        model_name: Model to use
        timeout: Timeout in seconds

    Returns:
        Embedding ID or None if failed
    """
    try:
        # Combine content and context for embedding
        text = content
        if context:
            text = f"{content}\n\nContext: {context}"

        vector = generate_embedding(text, model_name, timeout)
        embedding_id = store_embedding(conn, memory_id, vector, model_name)

        logger.debug(f"Generated embedding for memory {memory_id}")
        return embedding_id

    except Exception as e:
        logger.warning(f"Failed to generate embedding for {memory_id}: {e}")
        return None


def get_memories_without_embeddings(
    conn: sqlite3.Connection,
    limit: int = 100,
) -> list[tuple[str, str, Optional[str]]]:
    """Get memories that don't have embeddings.

    Args:
        conn: Database connection
        limit: Maximum number to return

    Returns:
        List of (memory_id, content, context) tuples
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, content, context
        FROM memories
        WHERE has_embedding = 0
        LIMIT ?
        """,
        (limit,),
    )

    return [(row["id"], row["content"], row["context"]) for row in cursor.fetchall()]


def backfill_embeddings(
    conn: sqlite3.Connection,
    model_name: str = DEFAULT_MODEL_NAME,
    timeout_per_memory: float = EMBEDDING_TIMEOUT,
) -> int:
    """Generate embeddings for all memories that don't have them.

    Args:
        conn: Database connection
        model_name: Model to use
        timeout_per_memory: Timeout per memory in seconds

    Returns:
        Number of embeddings generated
    """
    total_generated = 0

    while True:
        # Get batch of memories without embeddings
        memories = get_memories_without_embeddings(conn, limit=10)

        if not memories:
            break

        for memory_id, content, context in memories:
            result = generate_and_store_embedding(
                conn, memory_id, content, context, model_name, timeout_per_memory
            )
            if result:
                total_generated += 1
                logger.info(f"Generated embedding {total_generated}: {memory_id}")

    return total_generated
