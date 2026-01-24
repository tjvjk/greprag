"""
GrepRAG benchmark using BRIGHT dataset for Recall@10 evaluation.

Evaluates the greprag search agent on complex reasoning queries.

Usage:
    python -m benchmark.grep --split biology --limit 5
    python -m benchmark.grep --split biology --output results/grep_biology.json
"""

import argparse
import asyncio
import json
import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import settings
from benchmark.base import BRIGHT_SPLITS, DataLoader
from benchmark.metrics import mean_recall_at_k, recall_at_k
from search_agent.agent import run_agent

logger = logging.getLogger(__name__)

CONCURRENCY = 20
TOP_K = 20


@dataclass
class AgentQueryResult:
    """Result of evaluating a single query with the agent."""

    query_id: str
    query: str
    gold_ids: list[str]
    retrieved_ids: list[str]
    recall_at_10: float
    error: str | None = None


@dataclass
class AgentBenchmarkResult:
    """Overall agent benchmark result."""

    split: str
    mean_recall_at_10: float
    evaluated_queries: int
    total_queries: int
    queries: list[dict] = field(default_factory=list)


class GrepBenchmark:
    """GrepRAG benchmark runner using BRIGHT dataset."""

    def __init__(self, split: str, temp_dir: Path | None = None):
        """
        Initialize the benchmark.

        Args:
            split: BRIGHT dataset split to use (e.g., 'biology')
            temp_dir: Optional temporary directory for documents
        """
        if split not in BRIGHT_SPLITS:
            raise ValueError(f"Unknown split: {split}. Available: {BRIGHT_SPLITS}")
        self._split = split
        self._temp_dir = temp_dir or Path(tempfile.mkdtemp(prefix="bright_"))
        self._doc_to_file: dict[str, str] = {}
        self._file_to_doc: dict[str, str] = {}
        self._original_folder = settings.DOCS_FOLDER
        self._loader = DataLoader(split)

    def _load(self) -> tuple[list[dict], dict[str, str]]:
        """
        Load BRIGHT dataset using common loader.

        Returns:
            Tuple of (queries, documents)
        """
        return self._loader.load()

    def _prepare(self, documents: dict[str, str]) -> None:
        """
        Write documents to temporary directory as .txt files.

        Args:
            documents: Dict mapping doc_id to document text
        """
        logger.info(f"Preparing documents in {self._temp_dir}")
        if self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)
        self._temp_dir.mkdir(parents=True, exist_ok=True)
        self._doc_to_file = {}
        self._file_to_doc = {}
        for identifier, content in documents.items():
            name = identifier.replace("/", "_").replace("\\", "_")
            if not name.endswith(".txt"):
                name += ".txt"
            path = self._temp_dir / name
            path.write_text(content, encoding="utf-8")
            self._doc_to_file[identifier] = name
            self._file_to_doc[name] = identifier
        logger.info(f"Wrote {len(documents)} documents to {self._temp_dir}")

    def _patch(self) -> None:
        """Patch settings.DOCS_FOLDER to use temporary directory."""
        settings.DOCS_FOLDER = str(self._temp_dir)
        logger.debug(f"Patched DOCS_FOLDER to {settings.DOCS_FOLDER}")

    def _restore(self) -> None:
        """Restore original settings.DOCS_FOLDER."""
        settings.DOCS_FOLDER = self._original_folder
        logger.debug(f"Restored DOCS_FOLDER to {settings.DOCS_FOLDER}")

    def _extract(self, citations: list) -> list[str]:
        """
        Extract document IDs from agent citations.

        Args:
            citations: List of Citation objects from AgentResult

        Returns:
            List of original document IDs mapped from filenames
        """
        identifiers = []
        seen = set()
        for citation in citations:
            location = citation.location
            if location in self._file_to_doc:
                identifier = self._file_to_doc[location]
            else:
                filename = Path(location).name
                identifier = self._file_to_doc.get(filename)
                if identifier is None:
                    for known, doc_id in self._file_to_doc.items():
                        if filename in known or known in filename:
                            identifier = doc_id
                            break
            if identifier and identifier not in seen:
                identifiers.append(identifier)
                seen.add(identifier)
        return identifiers

    async def _evaluate(self, data: dict) -> AgentQueryResult:
        """
        Evaluate a single query using the search agent.

        Args:
            data: Dict with 'id', 'query', 'gold_ids'

        Returns:
            AgentQueryResult with evaluation metrics
        """
        identifier = data["id"]
        text = data["query"]
        gold = data["gold_ids"]
        logger.info(f"Evaluating query {identifier}: {text[:100]}...")
        try:
            result = await run_agent(text)
            citations = result.response.citations or []
            retrieved = self._extract(citations)
            logger.debug(f"Gold IDs: {gold[:5]}")
            logger.debug(f"Retrieved IDs (top 10): {retrieved[:10]}")
            recall = recall_at_k(retrieved, gold, k=TOP_K)
            logger.info(
                f"Query {identifier}: retrieved {len(retrieved)} docs, "
                f"gold {len(gold)} docs, recall@10={recall:.3f}"
            )
            return AgentQueryResult(
                query_id=identifier,
                query=text,
                gold_ids=gold,
                retrieved_ids=retrieved,
                recall_at_10=recall,
            )
        except Exception as exc:
            logger.error(f"Error evaluating query {identifier}: {exc}")
            return AgentQueryResult(
                query_id=identifier,
                query=text,
                gold_ids=gold,
                retrieved_ids=[],
                recall_at_10=0.0,
                error=str(exc),
            )

    async def run(self, limit: int | None = None) -> AgentBenchmarkResult:
        """
        Run the benchmark.

        Args:
            limit: Optional limit on number of queries to evaluate

        Returns:
            AgentBenchmarkResult with overall metrics
        """
        queries, documents = self._load()
        self._prepare(documents)
        if limit:
            queries = queries[:limit]
        self._patch()
        try:
            sem = asyncio.Semaphore(CONCURRENCY)
            async def bounded(data: dict) -> AgentQueryResult:
                async with sem:
                    return await self._evaluate(data)
            results = await asyncio.gather(*[bounded(q) for q in queries])
            data = [
                {"retrieved_ids": r.retrieved_ids, "gold_ids": r.gold_ids}
                for r in results
            ]
            recall = mean_recall_at_k(data, k=TOP_K)
            output = AgentBenchmarkResult(
                split=self._split,
                mean_recall_at_10=recall,
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
                f"Benchmark complete: mean_recall@10={recall:.4f} "
                f"({len(results)} queries)"
            )
            return output
        finally:
            self._restore()

    def cleanup(self) -> None:
        """Remove temporary directory."""
        if self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)
            logger.info(f"Cleaned up {self._temp_dir}")


def save(result: AgentBenchmarkResult, path: str) -> None:
    """Save benchmark results to JSON file."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "split": result.split,
        "method": "greprag_agent",
        "mean_recall_at_10": result.mean_recall_at_10,
        "evaluated_queries": result.evaluated_queries,
        "total_queries": result.total_queries,
        "queries": result.queries,
    }
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Results saved to {path}")


async def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run GrepRAG benchmark using BRIGHT dataset"
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

    benchmark = GrepBenchmark(split=args.split)

    try:
        result = await benchmark.run(limit=args.limit)

        if args.output:
            save(result, args.output)
        else:
            print(f"\n{'=' * 60}")
            print(f"GrepRAG Benchmark Results: {result.split}")
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
