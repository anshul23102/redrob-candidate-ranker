# The Last Commit — Intelligent Candidate Ranker (India Runs · Track 1)

Ranks the **top 100 of 100,000 candidates** for Redrob's *"Senior AI Engineer — Founding Team"* JD.

> We don't build a keyword matcher. We **reconstruct the recruiter's decision function**:
> a consensus-gated, fraud-hardened, explainable ranker that reads career history (not
> skill lists), hard-gates impossible profiles, weights real availability signals, and
> emits a falsifiable reason **plus one honest concern** for every pick — in ~11 seconds,
> on CPU, fully offline.

## Reproduce the submission
```bash
pip install -r requirements.txt

# (optional, one-time, offline-prep) precompute semantic scores — ~12 min on CPU
python scripts/precompute_embeddings.py

# the ranking step (CPU-only, no network, <5 min — actual: ~11s)
python rank.py --candidates ./data/candidates.jsonl --out ./the_last_commit.csv
python validate_submission.py ./the_last_commit.csv   # -> "Submission is valid."
```
If `artifacts/semantic.json` is absent, the ranker falls back to the keyword rubric —
still valid, slightly lower fidelity. The ranking step never loads a model or touches
the network; it reads precomputed scalars.

## Why this design (the three decisions that matter)

**1. Consensus gate, not weighted sum.** `core = sqrt(role_fit × evidence_fit) × refinements`.
A weighted sum lets a gaudy skill list paper over a wrong title — exactly the dataset's
keyword-stuffer trap. A geometric gate collapses when either pillar fails: fraud can
spike one signal, it can't forge agreement across all of them.

**2. Evidence from the work, not the headline.** All fit evidence is read from
`career_history` descriptions (what the candidate actually did). Headline/summary
claims get a token credit (≤0.06). A semantic layer (MiniLM, precomputed offline)
rescues strong candidates who describe elite ranking work in plain language — the
JD's "Tier-5 gem" case.

**3. Integrity: hard-gate the impossible, soft-discount the noisy.** Honeypot
signatures (role duration > time-since-start, ≥2 "expert" skills with 0 months used,
claimed tenure ≫ stated experience) are rare (~44 in the pool) and hard-gated.
Noisy inconsistencies (skill-duration > YoE — fires on 9% of the pool) are only
soft-discounted: hard-filtering them would false-negative thousands of real people.

## Results (no leaderboard exists — we measure ourselves)

**Gold-set eval** — 55 hand-labeled candidates (stratified: strong fits, adjacents,
stuffers, honeypots, CV-primary), scored on the challenge's own composite:

| metric | NDCG@10 | NDCG@50 | MAP | P@10 | composite |
|---|---|---|---|---|---|
| full model | 0.931 | 0.987 | 0.944 | 1.000 | **0.953** |

**Full-pool trap-leak test** — traps admitted into the true top-100 of 100,000:

| ranker | honeypots | keyword-stuffers | CV-primary |
|---|---|---|---|
| **ours** | **0** | **0** | **0** |
| naive skill-keyword count (the JD's stated trap) | 2 | 33 | 5 |
| title + skill% + YoE (typical weighted-sum) | 2 | 0 | 10 |

Ablations (removing any single defense) stay at 0/0/0 — the defenses overlap by
design (**defense-in-depth**): a trap must simultaneously beat the role gate, the
evidence-from-work reader, skill-grounding, and the integrity layer.

## Architecture
```
candidates.jsonl (100K)                        [offline, once]
      │                                        MiniLM embeddings of career_text
      ▼                                            → artifacts/semantic.json
┌─ rank.py (CPU, no network, ~11s) ──────────────────────────────┐
│ role consensus gate ── evidence-from-work (keyword ⊕ semantic) │
│        × skill-trust × experience-band × trajectory            │
│        × availability (signals) × location × integrity         │
│ → top-100 → grounded reasoning + one honest concern → CSV      │
└─────────────────────────────────────────────────────────────────┘
```

## Methodology
Full write-up: [docs/METHODOLOGY.md](docs/METHODOLOGY.md) — the data-first design story, scoring math, eval protocol, and what we deliberately did not build.

## Repo map
- `rank.py` — the single reproduce command
- `src/scoring/score.py` — consensus-gated scorer · `src/jd_rubric.py` — JD as code
- `src/integrity/checks.py` — honeypot/impossibility layer
- `src/reasoning/reason.py` — grounded reasoning + counter-signal
- `src/retrieval/semantic.py` + `scripts/precompute_embeddings.py` — semantic layer
- `src/eval/` + `scripts/run_eval.py` — gold labels, challenge metrics, ablations
- `scripts/leak_test.py` — full-pool trap-leak comparison vs naive baselines
- `app/app.py` — Streamlit sandbox (runs the exact pipeline on ≤100-candidate samples)
