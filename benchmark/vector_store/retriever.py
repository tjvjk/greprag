"""Combined retriever using embeddings and vector storage."""

from typing import final

from benchmark.vector_store.base import Encoder, Retriever, Storage


@final
class VectorRetriever(Retriever):
    """
    Semantic document retriever combining encoder and storage.

    Indexes documents by computing embeddings and storing them,
    then retrieves by encoding queries and searching for similar vectors.

    Example:
        >>> from benchmark.vector_store.embeddings import GemmaEmbedder
        >>> from benchmark.vector_store.database import SqliteVectorStorage
        >>> encoder = GemmaEmbedder()
        >>> storage = SqliteVectorStorage(":memory:", encoder.dimension())
        >>> retriever = VectorRetriever(encoder, storage)
        >>> retriever.index([("doc1", "Machine learning is great")])
        >>> retriever.retrieve("AI and ML", 10)
        ['doc1']
    """

    def __init__(self, encoder: Encoder, storage: Storage):
        """
        Initialize retriever with encoder and storage.

        Args:
            encoder: Text embedding encoder
            storage: Vector storage backend
        """
        self._encoder = encoder
        self._storage = storage

    def index(self, documents: list[tuple[str, str]]) -> None:
        """
        Index documents for semantic retrieval.

        Computes embeddings for each document and stores them
        in the vector storage for later similarity search.

        Args:
            documents: List of (doc_id, content) tuples to index
        """
        for identifier, content in documents:
            embedding = self._encoder.encode(content)
            self._storage.insert(identifier, content, embedding)

    def retrieve(self, query: str, limit: int = 10) -> list[str]:
        """
        Find relevant documents for query.

        Encodes the query and searches for similar document vectors.

        Args:
            query: Search query text
            limit: Maximum results to return

        Returns:
            List of document IDs ordered by semantic similarity
        """
        embedding = self._encoder.encode(query)
        return self._storage.search(embedding, limit)
