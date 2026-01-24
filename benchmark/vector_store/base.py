"""Abstract base classes for vector store components."""

from abc import ABC, abstractmethod


class Encoder(ABC):
    """
    Abstract base for text embedding encoders.

    Encoders transform text into dense vector representations
    suitable for semantic similarity search.
    """

    @abstractmethod
    def encode(self, text: str) -> list[float]:
        """
        Transform text into embedding vector.

        Args:
            text: Input text to encode

        Returns:
            Dense vector representation as list of floats
        """
        ...

    @abstractmethod
    def dimension(self) -> int:
        """
        Return the dimensionality of embeddings.

        Returns:
            Integer dimension of output vectors
        """
        ...


class Storage(ABC):
    """
    Abstract base for vector storage backends.

    Storage backends persist document embeddings and
    support similarity-based retrieval.
    """

    @abstractmethod
    def insert(self, identifier: str, content: str, embedding: list[float]) -> None:
        """
        Store document with its embedding.

        Args:
            identifier: Unique document ID
            content: Document text content
            embedding: Vector representation
        """
        ...

    @abstractmethod
    def search(self, embedding: list[float], limit: int) -> list[str]:
        """
        Find similar documents by vector similarity.

        Args:
            embedding: Query vector
            limit: Maximum results to return

        Returns:
            List of document IDs ordered by similarity
        """
        ...

    @abstractmethod
    def count(self) -> int:
        """
        Return number of stored documents.

        Returns:
            Total document count
        """
        ...


class Retriever(ABC):
    """
    Abstract base for document retrieval.

    Retrievers combine encoding and storage to provide
    end-to-end semantic search capability.
    """

    @abstractmethod
    def index(self, documents: list[tuple[str, str]]) -> None:
        """
        Index documents for retrieval.

        Args:
            documents: List of (doc_id, content) tuples
        """
        ...

    @abstractmethod
    def retrieve(self, query: str, limit: int) -> list[str]:
        """
        Find relevant documents for query.

        Args:
            query: Search query text
            limit: Maximum results to return

        Returns:
            List of document IDs ordered by relevance
        """
        ...
