"""Tests for vector store components."""

import secrets

import pytest

try:
    from benchmark.vector_store.database import SqliteVectorStorage
    from benchmark.vector_store.embeddings import GemmaEmbedder
    from benchmark.vector_store.retriever import VectorRetriever

    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not VECTOR_AVAILABLE,
    reason="Vector store dependencies not installed",
)


class TestSqliteVectorStorage:
    """Tests for SqliteVectorStorage."""

    def test_insert_stores_document_in_database(self) -> None:
        """Storage stores document when insert called."""
        dim = 8
        identifier = f"doc_{secrets.token_hex(4)}"
        content = f"content_{secrets.token_hex(4)}"
        embedding = [secrets.randbelow(100) / 100 for _ in range(dim)]
        storage = SqliteVectorStorage(":memory:", dim)
        storage.insert(identifier, content, embedding)
        assert storage.count() == 1, "Storage should contain one document after insert"

    def test_search_returns_similar_documents(self) -> None:
        """Storage returns documents ordered by similarity."""
        dim = 8
        storage = SqliteVectorStorage(":memory:", dim)
        embedding_a = [1.0] * dim
        embedding_b = [0.5] * dim
        storage.insert("doc_a", "content_a", embedding_a)
        storage.insert("doc_b", "content_b", embedding_b)
        query = [0.9] * dim
        results = storage.search(query, limit=2)
        assert "doc_a" in results, "Search should return similar document"

    def test_count_returns_correct_total(self) -> None:
        """Storage count reflects number of inserted documents."""
        dim = 4
        storage = SqliteVectorStorage(":memory:", dim)
        count = secrets.randbelow(5) + 2
        for i in range(count):
            embedding = [secrets.randbelow(100) / 100 for _ in range(dim)]
            storage.insert(f"doc_{i}", f"content_{i}", embedding)
        assert storage.count() == count, "Count should equal number of inserted documents"


class TestGemmaEmbedder:
    """Tests for GemmaEmbedder."""

    @pytest.fixture
    def encoder(self) -> GemmaEmbedder:
        """Provide initialized encoder instance."""
        return GemmaEmbedder()

    def test_encode_returns_vector_of_correct_dimension(
        self,
        encoder: GemmaEmbedder,
    ) -> None:
        """Encoder produces vector matching model dimension."""
        text = f"random text {secrets.token_hex(8)}"
        vector = encoder.encode(text)
        expected = encoder.dimension()
        assert len(vector) == expected, "Embedding dimension should match model config"

    def test_encode_handles_unicode_text(self, encoder: GemmaEmbedder) -> None:
        """Encoder processes non-ASCII characters correctly."""
        text = f"Привет мир 你好世界 {secrets.token_hex(4)}"
        vector = encoder.encode(text)
        assert len(vector) > 0, "Encoder should handle unicode text"

    def test_dimension_returns_positive_integer(self, encoder: GemmaEmbedder) -> None:
        """Encoder dimension is valid positive integer."""
        dim = encoder.dimension()
        assert dim > 0, "Dimension should be positive"


class TestVectorRetriever:
    """Tests for VectorRetriever."""

    @pytest.fixture
    def retriever(self) -> VectorRetriever:
        """Provide initialized retriever instance."""
        encoder = GemmaEmbedder()
        storage = SqliteVectorStorage(":memory:", encoder.dimension())
        return VectorRetriever(encoder, storage)

    def test_index_stores_documents(self, retriever: VectorRetriever) -> None:
        """Retriever indexes provided documents."""
        documents = [
            (f"id_{secrets.token_hex(4)}", f"content_{secrets.token_hex(8)}"),
            (f"id_{secrets.token_hex(4)}", f"content_{secrets.token_hex(8)}"),
        ]
        retriever.index(documents)
        result = retriever.retrieve("test query", limit=10)
        assert len(result) == 2, "Retriever should return indexed documents"

    def test_retrieve_returns_relevant_documents(
        self,
        retriever: VectorRetriever,
    ) -> None:
        """Retriever finds semantically similar documents."""
        documents = [
            ("ml_doc", "Machine learning and artificial intelligence research"),
            ("cooking_doc", "Cooking recipes for delicious pasta dishes"),
        ]
        retriever.index(documents)
        results = retriever.retrieve("neural networks and deep learning", limit=1)
        assert results[0] == "ml_doc", "Retriever should rank ML document higher for ML query"
