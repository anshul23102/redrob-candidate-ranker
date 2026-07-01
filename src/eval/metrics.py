"""Ranking metrics matching the challenge's composite: NDCG@k, MAP, P@k.

Composite = 0.50*NDCG@10 + 0.30*NDCG@50 + 0.15*MAP + 0.05*P@10  (submission_spec sec 4).
Graded NDCG uses gain = 2^rel - 1. 'relevant' for MAP/P@k means tier >= 3.
"""
from math import log2

REL_THRESHOLD = 3


def _dcg(rels):
    return sum((2 ** r - 1) / log2(i + 2) for i, r in enumerate(rels))


def ndcg_at_k(ranked_rels, k):
    ideal = sorted(ranked_rels, reverse=True)
    idcg = _dcg(ideal[:k])
    return _dcg(ranked_rels[:k]) / idcg if idcg > 0 else 0.0


def precision_at_k(ranked_rels, k, thresh=REL_THRESHOLD):
    top = ranked_rels[:k]
    return sum(1 for r in top if r >= thresh) / k if k else 0.0


def average_precision(ranked_rels, thresh=REL_THRESHOLD):
    hits, ap = 0, 0.0
    for i, r in enumerate(ranked_rels, start=1):
        if r >= thresh:
            hits += 1
            ap += hits / i
    total_rel = sum(1 for r in ranked_rels if r >= thresh)
    return ap / total_rel if total_rel else 0.0


def composite(ranked_rels):
    ndcg10 = ndcg_at_k(ranked_rels, 10)
    ndcg50 = ndcg_at_k(ranked_rels, 50)
    mapv = average_precision(ranked_rels)
    p10 = precision_at_k(ranked_rels, 10)
    comp = 0.50 * ndcg10 + 0.30 * ndcg50 + 0.15 * mapv + 0.05 * p10
    return dict(NDCG10=ndcg10, NDCG50=ndcg50, MAP=mapv, P10=p10, composite=comp)
