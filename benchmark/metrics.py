"""Metrics for evaluating search quality."""


def recall_at_k(retrieved: list[str], gold: list[str], k: int = 10) -> float:
    """
    Calculate Recall@K for a single query.

    Args:
        retrieved: List of retrieved document IDs in order
        gold: List of relevant document IDs
        k: Number of top results to consider

    Returns:
        Recall@K score between 0.0 and 1.0
    """
    if not gold:
        return 0.0
    top_k = set(retrieved[:k])
    hits = len(top_k & set(gold))
    return hits / len(gold)


def mean_recall_at_k(results: list[dict[str, list[str]]], k: int = 10) -> float:
    """
    Calculate mean Recall@K across all queries.

    Args:
        results: List of dicts with 'retrieved_ids' and 'gold_ids' keys
        k: Number of top results to consider

    Returns:
        Mean Recall@K score between 0.0 and 1.0
    """
    if not results:
        return 0.0
    recalls = [recall_at_k(r["retrieved_ids"], r["gold_ids"], k) for r in results]
    return sum(recalls) / len(recalls)
