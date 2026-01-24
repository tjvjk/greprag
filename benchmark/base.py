"""Common base classes and utilities for benchmarks."""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from datasets import load_dataset

logger = logging.getLogger(__name__)

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

    identifier: str
    query: str
    gold: list[str]
    retrieved: list[str]
    recall: float
    error: str | None = None


@dataclass
class BenchmarkResult:
    """Overall benchmark result."""

    split: str
    method: str
    recall: float
    evaluated: int
    total: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    queries: list[dict] = field(default_factory=list)


class DataLoader:
    """
    Loads BRIGHT dataset from HuggingFace.

    Provides standardized access to queries and documents
    for any BRIGHT dataset split.

    Example:
        >>> loader = DataLoader("biology")
        >>> queries, documents = loader.load()
        >>> len(queries) > 0
        True
    """

    def __init__(self, split: str):
        """
        Initialize loader for given split.

        Args:
            split: BRIGHT dataset split name
        """
        if split not in BRIGHT_SPLITS:
            raise ValueError(f"Unknown split: {split}, available: {BRIGHT_SPLITS}")
        self._split = split

    def load(self) -> tuple[list[dict], dict[str, str]]:
        """
        Load queries and documents from BRIGHT dataset.

        Returns:
            Tuple of (queries, documents) where queries contain
            id, query text, and gold document IDs
        """
        logger.info(f"Loading BRIGHT dataset split: {self._split}")
        examples = load_dataset("xlangai/BRIGHT", "examples", split=self._split)
        documents = load_dataset("xlangai/BRIGHT", "long_documents", split=self._split)
        queries = []
        for example in examples:
            identifier = example.get("id", example.get("query_id", str(len(queries))))
            gold_raw = example.get("gold_ids_long", [])
            if isinstance(gold_raw, str):
                gold = json.loads(gold_raw)
            else:
                gold = list(gold_raw)
            queries.append({
                "id": identifier,
                "query": example["query"],
                "gold_ids": gold,
            })
        docs = {}
        for doc in documents:
            identifier = doc.get("id", doc.get("doc_id"))
            content = doc.get("content", doc.get("text", ""))
            docs[identifier] = content
        logger.info(f"Loaded {len(queries)} queries and {len(docs)} documents")
        return queries, docs


class BaseBenchmark(ABC):
    """
    Abstract base for benchmark runners.

    Provides common infrastructure for loading data,
    running evaluations, and producing results.
    """

    @abstractmethod
    def run(self, limit: int | None = None) -> BenchmarkResult:
        """
        Execute benchmark and return results.

        Args:
            limit: Optional limit on number of queries

        Returns:
            BenchmarkResult with aggregated metrics
        """
        ...


def save(result: BenchmarkResult, path: str) -> None:
    """
    Save benchmark results to JSON file.

    Args:
        result: Benchmark results to save
        path: Output file path
    """
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "split": result.split,
        "method": result.method,
        "mean_recall_at_k": result.recall,
        "evaluated_queries": result.evaluated,
        "total_queries": result.total,
        "timestamp": result.timestamp,
        "queries": result.queries,
    }
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Results saved to {path}")
