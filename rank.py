#!/usr/bin/env python3
"""Produce the top-100 ranked CSV from candidates.jsonl.

Single reproduce command (per submission_spec 10.3):
    python rank.py --candidates ./data/candidates.jsonl --out ./the_last_commit.csv

CPU-only, no network, streaming (low memory). Two passes over the file: pass 1 scores
every candidate keeping only (score, id); pass 2 re-fetches the 100 winners for reasoning.
"""
import argparse, csv, sys, time

from src.schema import load_candidates
from src.scoring.score import score_candidate
from src.integrity.checks import integrity
from src.reasoning.reason import make_reason
from src.retrieval.semantic import load_semantic, semantic_fit

HEADER = ["candidate_id", "rank", "score", "reasoning"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default="./data/candidates.jsonl")
    ap.add_argument("--out", default="./the_last_commit.csv")
    ap.add_argument("--topk", type=int, default=100)
    args = ap.parse_args()

    t0 = time.time()
    has_sem = load_semantic()   # precomputed artifact; falls back to keyword-only if absent

    # Pass 1 — score everyone, keep only (score, id) (tiny memory).
    scored = []
    n = 0
    for c in load_candidates(args.candidates):
        s, _ = score_candidate(c, integrity, sem_fit=semantic_fit(c["candidate_id"]))
        scored.append((s, c["candidate_id"]))
        n += 1
    # Rank by score desc; ties broken by candidate_id ascending (validator rule).
    scored.sort(key=lambda t: (-t[0], t[1]))
    top = scored[: args.topk]
    top_ids = {cid for _, cid in top}
    t1 = time.time()

    # Pass 2 — re-fetch the winners for grounded reasoning.
    by_id = {}
    for c in load_candidates(args.candidates):
        cid = c["candidate_id"]
        if cid in top_ids:
            s, facets = score_candidate(c, integrity, sem_fit=semantic_fit(cid))
            by_id[cid] = (c, facets)
            if len(by_id) == len(top_ids):
                break

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        for rank, (s, cid) in enumerate(top, start=1):
            c, facets = by_id[cid]
            w.writerow([cid, rank, f"{s:.6f}", make_reason(c, facets)])

    dt = time.time() - t0
    print(f"Scored {n} candidates in {t1 - t0:.1f}s, wrote top-{args.topk} to {args.out} "
          f"(total {dt:.1f}s).", file=sys.stderr)
    # quick sanity peek
    for (s, cid) in top[:5]:
        c, facets = by_id[cid]
        print(f"  #{cid}  score={s:.4f}  {c['profile']['current_title']}  "
              f"role={facets['role_class']} ev={facets['evidence_fit']:.2f}", file=sys.stderr)


if __name__ == "__main__":
    main()
