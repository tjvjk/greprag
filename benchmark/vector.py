"""
Vector store benchmark using BRIGHT dataset for Recall@10 evaluation.

Compares semantic vector retrieval against the greprag search agent.

Usage:
    python -m benchmark.vector --split biology --limit 5
    python -m benchmark.vector --split biology --output results/vector_biology.json
"""

import argparse
import logging
from pathlib import Path
from typing import final

from benchmark.base import (
    BRIGHT_SPLITS,
    BaseBenchmark,
    BenchmarkResult,
    DataLoader,
    QueryResult,
    save,
)
from benchmark.metrics import mean_recall_at_k, recall_at_k
from benchmark.vector_store.database import SqliteVectorStorage
from benchmark.vector_store.embeddings import GemmaEmbedder
from benchmark.vector_store.retriever import VectorRetriever

logger = logging.getLogger(__name__)

TOP_K = 20


@final
class VectorBenchmark(BaseBenchmark):
    """
    BRIGHT benchmark runner for vector store evaluation.

    Loads BRIGHT dataset, indexes documents using embeddings,
    and evaluates retrieval quality using Recall@10.

    Example:
        >>> benchmark = VectorBenchmark("biology")
        >>> result = benchmark.run(limit=5)
        >>> print(f"Recall@10: {result.recall:.4f}")
    """

    def __init__(self, split: str, db: str | None = None):
        """
        Initialize benchmark for given split.

        Args:
            split: BRIGHT dataset split name
            db: Database file path, defaults to data/{split}.db
        """
        self._split = split
        self._db = db or f"data/{split}.db"
        self._loader = DataLoader(split)
        self._retriever: VectorRetriever | None = None

    def _index(self, documents: dict[str, str]) -> None:
        """
        Index documents into vector store.

        Args:
            documents: Dict mapping doc_id to content
        """
        path = Path(self._db)
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Initializing embedding model")
        encoder = GemmaEmbedder()
        storage = SqliteVectorStorage(str(path), encoder.dimension())
        self._retriever = VectorRetriever(encoder, storage)
        if storage.count() > 0:
            logger.info(f"Using existing index with {storage.count()} documents")
            return
        items = list(documents.items())
        logger.info(f"Indexing {len(items)} documents to {path}")
        self._retriever.index(items)
        logger.info("Indexing complete")

    def _evaluate(self, query: dict) -> QueryResult:
        """
        Evaluate single query against vector store.

        Args:
            query: Dict with id, query text, and gold_ids

        Returns:
            QueryResult with recall score
        """
        identifier = query["id"]
        text = query["query"]
        gold = query["gold_ids"]
        logger.debug(f"Evaluating query {identifier}")
        try:
            retrieved = self._retriever.retrieve(text, limit=TOP_K)
            recall = recall_at_k(retrieved, gold, k=TOP_K)
            return QueryResult(
                identifier=identifier,
                query=text,
                gold=gold,
                retrieved=retrieved,
                recall=recall,
            )
        except Exception as exc:
            logger.error(f"Query {identifier} failed: {exc}")
            return QueryResult(
                identifier=identifier,
                query=text,
                gold=gold,
                retrieved=[],
                recall=0.0,
                error=str(exc),
            )

    def run(self, limit: int | None = None) -> BenchmarkResult:
        """
        Execute benchmark on BRIGHT dataset split.

        Args:
            limit: Optional limit on number of queries

        Returns:
            BenchmarkResult with aggregated metrics
        """
        queries, documents = self._loader.load()
        self._index(documents)
        if limit:
            queries = queries[:limit]
        results = [self._evaluate(q) for q in queries]
        data = [{"retrieved_ids": r.retrieved, "gold_ids": r.gold} for r in results]
        recall = mean_recall_at_k(data, k=TOP_K)
        return BenchmarkResult(
            split=self._split,
            method="vector_store",
            recall=recall,
            evaluated=len(results),
            total=len(queries),
            queries=[
                {
                    "query_id": r.identifier,
                    "query": r.query,
                    "gold_ids": r.gold,
                    "retrieved_ids": r.retrieved,
                    "recall_at_10": r.recall,
                    "error": r.error,
                }
                for r in results
            ],
        )


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run BRIGHT benchmark on vector store retrieval"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="biology",
        choices=BRIGHT_SPLITS,
        help="BRIGHT dataset split to evaluate",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of queries to evaluate",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file path for results",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="Database file path, defaults to data/{split}.db",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    benchmark = VectorBenchmark(split=args.split, db=args.db)
    result = benchmark.run(limit=args.limit)
    if args.output:
        save(result, args.output)
    else:
        print(f"\n{'=' * 60}")
        print(f"Vector Store Benchmark Results: {result.split}")
        print(f"{'=' * 60}")
        print(f"Method: {result.method}")
        print(f"Mean Recall@10: {result.recall:.4f}")
        print(f"Evaluated queries: {result.evaluated}")
        print(f"{'=' * 60}\n")
        for q in result.queries:
            status = "ERROR" if q["error"] else f"R@10={q['recall_at_10']:.3f}"
            print(f"  [{q['query_id']}] {status}")


if __name__ == "__main__":
    main()
