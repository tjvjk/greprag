"""SQLite-based vector storage using sqlite-vec extension."""

import json
import sqlite3
from typing import final

import sqlite_vec

from benchmark.vector_store.base import Storage


@final
class SqliteVectorStorage(Storage):
    """
    Vector storage using SQLite with sqlite-vec extension.

    Stores documents and their embeddings in SQLite database,
    supporting cosine similarity search via virtual table.

    Example:
        >>> storage = SqliteVectorStorage(":memory:", 768)
        >>> storage.insert("doc1", "Hello", [0.1] * 768)
        >>> storage.count()
        1
    """

    def __init__(self, path: str, dim: int):
        """
        Initialize SQLite vector storage.

        Args:
            path: Database file path or ":memory:" for in-memory
            dim: Embedding vector dimensionality
        """
        self._path = path
        self._dim = dim
        self._connection = self._connect()

    def _connect(self) -> sqlite3.Connection:
        """
        Establish database connection with vector extension.

        Returns:
            Configured SQLite connection
        """
        connection = sqlite3.connect(self._path)
        connection.enable_load_extension(True)
        sqlite_vec.load(connection)
        connection.enable_load_extension(False)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL
            )
        """)
        connection.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS embeddings USING vec0(
                doc_id TEXT PRIMARY KEY,
                embedding FLOAT[{self._dim}]
            )
        """)
        connection.commit()
        return connection

    def insert(self, identifier: str, content: str, embedding: list[float]) -> None:
        """
        Store document with its embedding vector.

        Args:
            identifier: Unique document ID
            content: Document text content
            embedding: Vector representation
        """
        self._connection.execute(
            "INSERT OR REPLACE INTO documents (id, content) VALUES (?, ?)",
            (identifier, content),
        )
        blob = json.dumps(embedding)
        self._connection.execute(
            "INSERT OR REPLACE INTO embeddings (doc_id, embedding) VALUES (?, ?)",
            (identifier, blob),
        )
        self._connection.commit()

    def search(self, embedding: list[float], limit: int) -> list[str]:
        """
        Find similar documents by cosine similarity.

        Args:
            embedding: Query vector
            limit: Maximum results to return

        Returns:
            List of document IDs ordered by similarity (most similar first)
        """
        blob = json.dumps(embedding)
        cursor = self._connection.execute(
            """
            SELECT doc_id
            FROM embeddings
            WHERE embedding MATCH ?
            ORDER BY distance
            LIMIT ?
            """,
            (blob, limit),
        )
        return [row[0] for row in cursor.fetchall()]

    def count(self) -> int:
        """
        Return number of indexed documents.

        Returns:
            Total document count
        """
        cursor = self._connection.execute("SELECT COUNT(*) FROM documents")
        return cursor.fetchone()[0]
