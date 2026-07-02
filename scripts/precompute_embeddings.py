#!/usr/bin/env python3
"""OFFLINE precompute: semantic similarity of each candidate's WORK to the JD's core facets.

Runs once (may use network/GPU — this is NOT the ranking step). Ships two artifacts so
rank.py stays offline/CPU/<5min:
  artifacts/semantic.json   {candidate_id: max-cosine-to-JD-facets in [~0,1]}  (small, committable)
  artifacts/cand_emb.npy    full embedding matrix (gitignored; for demo / future rerank)
  artifacts/cand_ids.json   row order for the matrix

Evidence is embedded from career_text (the work), not the headline — same anti-stuffing
principle as the keyword layer. This rescues concise strong profiles that describe elite
work in few keywords (e.g. "owned the ranking layer ... learning-to-rank model").
"""
import json, time
import numpy as np
from sentence_transformers import SentenceTransformer
from src.schema import load_candidates, career_text, headline_text

MODEL = "all-MiniLM-L6-v2"           # 384-d, fast on CPU, reliable
# JD-derived facet queries (the intelligence-layer work the role owns)
FACETS = [
    "production experience building embedding-based retrieval and ranking systems deployed to real users",
    "recommendation systems and search relevance at scale in a product company",
    "vector search, hybrid retrieval, dense and sparse, and reranking infrastructure",
    "evaluating ranking systems offline and online with NDCG, MRR, MAP and A/B testing",
    "applied machine learning engineer working on LLMs, NLP and information retrieval",
]


def main():
    t0 = time.time()
    model = SentenceTransformer(MODEL)
    Q = model.encode(FACETS, normalize_embeddings=True, convert_to_numpy=True)

    ids, texts = [], []
    for c in load_candidates("./data/candidates.jsonl"):
        ids.append(c["candidate_id"])
        t = career_text(c) or headline_text(c)
        texts.append(t[:1200])          # cap length; descriptions are short anyway
    print(f"Encoding {len(texts)} candidates with {MODEL} ...", flush=True)

    emb = model.encode(texts, batch_size=256, normalize_embeddings=True,
                       convert_to_numpy=True, show_progress_bar=True)
    sims = emb @ Q.T                    # (N, 5) cosine to each facet
    maxcos = sims.max(axis=1)           # best-matching facet per candidate

    np.save("artifacts/cand_emb.npy", emb.astype(np.float32))
    json.dump(ids, open("artifacts/cand_ids.json", "w"))
    json.dump({cid: round(float(s), 4) for cid, s in zip(ids, maxcos)},
              open("artifacts/semantic.json", "w"))

    p = np.percentile(maxcos, [5, 25, 50, 75, 90, 95, 99])
    print(f"\nmax-cosine distribution: p5={p[0]:.3f} p25={p[1]:.3f} p50={p[2]:.3f} "
          f"p75={p[3]:.3f} p90={p[4]:.3f} p95={p[5]:.3f} p99={p[6]:.3f}")
    print(f"Done in {time.time()-t0:.1f}s. Artifacts written to artifacts/.")


if __name__ == "__main__":
    main()
