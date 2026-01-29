"""Benchmark module for evaluating retrieval systems."""

from benchmark.metrics import mean_recall_at_k, recall_at_k

__all__ = ["recall_at_k", "mean_recall_at_k"]
