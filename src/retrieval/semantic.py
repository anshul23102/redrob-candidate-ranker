"""Rank-time semantic lookup: loads precomputed per-candidate JD-relevance scalars.

No model, no network, no matrix math at rank time - just a dict lookup of the artifact
produced offline by scripts/precompute_embeddings.py. Raw max-cosine is rescaled to [0,1]
using pool percentiles (p50 -> 0, p98 -> 1) so it blends cleanly with the keyword evidence.
"""
import json

_STATE = {}


def load_semantic(path="artifacts/semantic.json"):
    try:
        raw = json.load(open(path))
    except FileNotFoundError:
        _STATE.clear()
        return False
    vals = sorted(raw.values())
    n = len(vals)
    _STATE["raw"] = raw
    _STATE["lo"] = vals[int(0.50 * n)]
    _STATE["hi"] = vals[min(n - 1, int(0.98 * n))]
    return True


def semantic_fit(cid):
    """Rescaled semantic relevance in [0,1], or None if unavailable (keyword-only fallback)."""
    raw = _STATE.get("raw")
    if not raw or cid not in raw:
        return None
    x, lo, hi = raw[cid], _STATE["lo"], _STATE["hi"]
    return max(0.0, min(1.0, (x - lo) / (hi - lo))) if hi > lo else 0.0
