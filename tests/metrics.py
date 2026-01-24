"""Metrics for evaluating search quality."""


def recall_at_k(retrieved_ids: list[str], gold_ids: list[str], k: int = 10) -> float:
    """
    Calculate Recall@K for a single query.

    Args:
        retrieved_ids: List of retrieved document IDs (in order of retrieval)
        gold_ids: List of relevant (gold) document IDs
        k: Number of top results to consider

    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if not gold_ids:
        return 0.0

    retrieved_top_k = set(retrieved_ids[:k])
    gold_set = set(gold_ids)
    hits = len(retrieved_top_k & gold_set)
    return hits / len(gold_set)


def mean_recall_at_k(
    results: list[dict[str, list[str]]],
    k: int = 10,
) -> float:
    """
    Calculate mean Recall@K across all queries.

    Args:
        results: List of dicts with 'retrieved_ids' and 'gold_ids' keys
        k: Number of top results to consider

    Returns:
        Mean Recall@K score (0.0 to 1.0)
    """
    if not results:
        return 0.0

    recalls = [
        recall_at_k(r["retrieved_ids"], r["gold_ids"], k)
        for r in results
    ]
    return sum(recalls) / len(recalls)
