# The Last Commit — Intelligent Candidate Ranker (India Runs · Track 1)

Ranks the **top 100 of 100,000 candidates** for Redrob's *"Senior AI Engineer — Founding Team"* JD.

> We don't build a keyword matcher. We **reconstruct the recruiter's decision function**:
> a two-stage, consensus-gated ranker that reads career history (not just skill lists),
> filters impossible/"honeypot" profiles, weights real availability signals, and emits a
> falsifiable reason **plus one honest concern** for every pick — in seconds, on CPU, offline.

## Reproduce the submission
```bash
pip install -r requirements.txt
python rank.py --candidates ./data/candidates.jsonl --out ./the_last_commit.csv
python validate_submission.py ./the_last_commit.csv   # must print "Submission is valid."
```
Ranking step is **CPU-only, no network, < 5 min, < 16 GB** — per the challenge compute constraints.
Any semantic embeddings/indexes are **precomputed offline** (see `scripts/`), never fetched at rank time.

## Architecture (overview)
1. **JD → structured rubric** — must-haves, nice-to-haves, hard disqualifiers, availability weighting.
2. **Stage A — high-recall retrieval** — hybrid (bi-encoder + BM25 via RRF) + soft structured filters → shortlist.
3. **Stage B — multi-signal judgment** — semantic career-fit + skill-trust + trajectory + availability.
4. **Consensus gating** — top ranks require agreement across facets (not a weighted sum a stuffer can game).
5. **Integrity layer** — impossibility/honeypot detection → soft discount, hard gate at the top.
6. **Calibration** — evidence-weighted shrinkage so thin profiles don't get false top ranks.
7. **Grounded reasoning + counter-signal** — fact-bound, zero hallucination, reproducible.
8. **Eval harness** — local proxy labels + NDCG@10/@50 / MAP / P@10, with ablations.

## Status
Scaffold + data profiling in progress. See `docs/` for the official spec, JD, and signals reference.
