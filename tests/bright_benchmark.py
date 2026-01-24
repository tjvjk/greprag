"""
BRIGHT benchmark integration for evaluating greprag search quality.

BRIGHT (Benchmark for Realistic and Instructed Reasoning over Grounded Text)
is a dataset for evaluating retrieval systems on complex reasoning queries.

Usage:
    python -m tests.bright_benchmark --split biology --limit 5
    python -m tests.bright_benchmark --split biology --output results/biology.json
"""

import argparse
import asyncio
import json
import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from datasets import load_dataset

import settings
from search_agent.agent import run_agent
from tests.metrics import mean_recall_at_k, recall_at_k

logger = logging.getLogger(__name__)

CONCURRENCY = 20

BRIGHT_SPLITS = [
    "biology",
    "earth_science",
    "economics",
    "psychology",
    "robotics",
    "stackoverflow",
    "sustainable_living",
    "leetcode",
    "pony",
    "aops",
    "theoremqa_theorems",
    "theoremqa_questions",
]


@dataclass
class QueryResult:
    """Result of evaluating a single query."""

    query_id: str
    query: str
    gold_ids: list[str]
    retrieved_ids: list[str]
    recall_at_10: float
    error: str | None = None


@dataclass
class BenchmarkResult:
    """Overall benchmark result."""

    split: str
    mean_recall_at_10: float
    evaluated_queries: int
    total_queries: int
    queries: list[dict] = field(default_factory=list)


class BrightBenchmark:
    """BRIGHT benchmark runner for greprag evaluation."""

    def __init__(self, split: str, temp_dir: Path | None = None):
        """
        Initialize the benchmark.

        Args:
            split: BRIGHT dataset split to use (e.g., 'biology')
            temp_dir: Optional temporary directory for documents
        """
        if split not in BRIGHT_SPLITS:
            raise ValueError(f"Unknown split: {split}. Available: {BRIGHT_SPLITS}")

        self.split = split
        self.temp_dir = temp_dir or Path(tempfile.mkdtemp(prefix="bright_"))
        self.doc_id_to_filename: dict[str, str] = {}
        self.filename_to_doc_id: dict[str, str] = {}
        self._original_docs_folder = settings.DOCS_FOLDER

    def load_data(self) -> tuple[list[dict], dict[str, str]]:
        """
        Load BRIGHT dataset from HuggingFace.

        Returns:
            Tuple of (queries, documents) where:
                - queries: List of query dicts with 'id', 'query', 'gold_ids'
                - documents: Dict mapping doc_id to document text
        """
        logger.info(f"Loading BRIGHT dataset split: {self.split}")
        examples_ds = load_dataset(
            "xlangai/BRIGHT",
            "examples",
            split=self.split,
        )
        documents_ds = load_dataset(
            "xlangai/BRIGHT",
            "long_documents",
            split=self.split,
        )
        queries = []
        for example in examples_ds:
            query_id = example.get("id", example.get("query_id", str(len(queries))))
            gold_ids_raw = example.get("gold_ids_long", [])
            if isinstance(gold_ids_raw, str):
                gold_ids = json.loads(gold_ids_raw)
            else:
                gold_ids = list(gold_ids_raw)

            queries.append({
                "id": query_id,
                "query": example["query"],
                "gold_ids": gold_ids,
            })
        documents = {}
        for doc in documents_ds:
            doc_id = doc.get("id", doc.get("doc_id"))
            content = doc.get("content", doc.get("text", ""))
            documents[doc_id] = content

        logger.info(f"Loaded {len(queries)} queries and {len(documents)} documents")
        return queries, documents

    def prepare_documents(self, documents: dict[str, str]) -> None:
        """
        Write documents to temporary directory as .txt files.

        Args:
            documents: Dict mapping doc_id to document text
        """
        logger.info(f"Preparing documents in {self.temp_dir}")
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.doc_id_to_filename = {}
        self.filename_to_doc_id = {}

        for doc_id, content in documents.items():
            safe_name = doc_id.replace("/", "_").replace("\\", "_")
            if not safe_name.endswith(".txt"):
                safe_name += ".txt"

            filepath = self.temp_dir / safe_name
            filepath.write_text(content, encoding="utf-8")

            self.doc_id_to_filename[doc_id] = safe_name
            self.filename_to_doc_id[safe_name] = doc_id
        sample_mappings = list(self.filename_to_doc_id.items())[:3]
        logger.debug(f"Sample filename->doc_id mappings: {sample_mappings}")
        logger.info(f"Wrote {len(documents)} documents to {self.temp_dir}")

    def _patch_settings(self) -> None:
        """Patch settings.DOCS_FOLDER to use temporary directory."""
        settings.DOCS_FOLDER = str(self.temp_dir)
        logger.debug(f"Patched DOCS_FOLDER to {settings.DOCS_FOLDER}")

    def _restore_settings(self) -> None:
        """Restore original settings.DOCS_FOLDER."""
        settings.DOCS_FOLDER = self._original_docs_folder
        logger.debug(f"Restored DOCS_FOLDER to {settings.DOCS_FOLDER}")

    def _extract_doc_ids_from_citations(self, citations: list) -> list[str]:
        """
        Extract document IDs from agent citations.

        Args:
            citations: List of Citation objects from AgentResult

        Returns:
            List of original document IDs (mapped back from filenames)
        """
        doc_ids = []
        seen = set()

        for citation in citations:
            location = citation.location
            if location in self.filename_to_doc_id:
                doc_id = self.filename_to_doc_id[location]
            else:
                filename = Path(location).name
                doc_id = self.filename_to_doc_id.get(filename)
                if doc_id is None:
                    for known_filename, known_doc_id in self.filename_to_doc_id.items():
                        if filename in known_filename or known_filename in filename:
                            doc_id = known_doc_id
                            break

            if doc_id and doc_id not in seen:
                doc_ids.append(doc_id)
                seen.add(doc_id)

        return doc_ids

    async def evaluate_query(self, query_data: dict) -> QueryResult:
        """
        Evaluate a single query using the search agent.

        Args:
            query_data: Dict with 'id', 'query', 'gold_ids'

        Returns:
            QueryResult with evaluation metrics
        """
        query_id = query_data["id"]
        query = query_data["query"]
        gold_ids = query_data["gold_ids"]

        logger.info(f"Evaluating query {query_id}: {query[:100]}...")

        try:
            result = await run_agent(query)
            citations = result.response.citations or []
            retrieved_ids = self._extract_doc_ids_from_citations(citations)
            logger.debug(f"Gold IDs: {gold_ids[:5]}")
            logger.debug(f"Retrieved IDs (top 10): {retrieved_ids[:10]}")
            logger.debug(f"Citation locations: {[c.location for c in citations[:5]]}")
            recall = recall_at_k(retrieved_ids, gold_ids, k=10)
            logger.info(
                f"Query {query_id}: retrieved {len(retrieved_ids)} docs, "
                f"gold {len(gold_ids)} docs, recall@10={recall:.3f}"
            )

            return QueryResult(
                query_id=query_id,
                query=query,
                gold_ids=gold_ids,
                retrieved_ids=retrieved_ids,
                recall_at_10=recall,
            )

        except Exception as e:
            logger.error(f"Error evaluating query {query_id}: {e}")
            return QueryResult(
                query_id=query_id,
                query=query,
                gold_ids=gold_ids,
                retrieved_ids=[],
                recall_at_10=0.0,
                error=str(e),
            )

    async def run(self, limit: int | None = None) -> BenchmarkResult:
        """
        Run the benchmark.

        Args:
            limit: Optional limit on number of queries to evaluate

        Returns:
            BenchmarkResult with overall metrics
        """
        queries, documents = self.load_data()
        self.prepare_documents(documents)

        if limit:
            queries = queries[:limit]

        self._patch_settings()

        try:
            sem = asyncio.Semaphore(CONCURRENCY)
            async def limited(query_data: dict) -> QueryResult:
                async with sem:
                    return await self.evaluate_query(query_data)
            results = await asyncio.gather(*[limited(q) for q in queries])
            recall_data = [
                {"retrieved_ids": r.retrieved_ids, "gold_ids": r.gold_ids}
                for r in results
            ]
            mean_recall = mean_recall_at_k(recall_data, k=10)
            benchmark_result = BenchmarkResult(
                split=self.split,
                mean_recall_at_10=mean_recall,
                evaluated_queries=len(results),
                total_queries=len(queries),
                queries=[
                    {
                        "query_id": r.query_id,
                        "query": r.query,
                        "gold_ids": r.gold_ids,
                        "retrieved_ids": r.retrieved_ids,
                        "recall_at_10": r.recall_at_10,
                        "error": r.error,
                    }
                    for r in results
                ],
            )

            logger.info(
                f"Benchmark complete: mean_recall@10={mean_recall:.4f} "
                f"({len(results)} queries)"
            )

            return benchmark_result

        finally:
            self._restore_settings()

    def cleanup(self) -> None:
        """Remove temporary directory."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up {self.temp_dir}")


def save_results(result: BenchmarkResult, output_path: str) -> None:
    """Save benchmark results to JSON file."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "split": result.split,
        "mean_recall_at_10": result.mean_recall_at_10,
        "evaluated_queries": result.evaluated_queries,
        "total_queries": result.total_queries,
        "queries": result.queries,
    }
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Results saved to {output_path}")


async def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run BRIGHT benchmark on greprag search agent"
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
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    benchmark = BrightBenchmark(split=args.split)

    try:
        result = await benchmark.run(limit=args.limit)

        if args.output:
            save_results(result, args.output)
        else:
            print(f"\n{'=' * 60}")
            print(f"BRIGHT Benchmark Results: {result.split}")
            print(f"{'=' * 60}")
            print(f"Mean Recall@10: {result.mean_recall_at_10:.4f}")
            print(f"Evaluated queries: {result.evaluated_queries}")
            print(f"{'=' * 60}\n")
            for q in result.queries:
                status = "ERROR" if q["error"] else f"R@10={q['recall_at_10']:.3f}"
                print(f"  [{q['query_id']}] {status}")

    finally:
        benchmark.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
