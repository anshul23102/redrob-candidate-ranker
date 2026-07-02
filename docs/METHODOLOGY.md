# Methodology — The Last Commit
### Intelligent Candidate Discovery & Ranking · India Runs Track 1

## 1. The premise: reconstruct the recruiter, don't approximate the keywords
The JD's closing section tells participants exactly how the ground truth thinks: read the
gap between what a profile *says* and what the candidate *did*; distrust keyword-perfect
profiles on wrong roles; down-weight unavailable people; expect planted traps. We treated
that section as a specification and built it as code. Every layer below maps to a sentence
in the JD or a property we measured in the data.

## 2. Data before architecture
Before any scoring code, we profiled all 100,000 candidates (`scripts/profile_data.py`).
The pool's signals dictated the design:
- Relevant titles are rare (ML Engineer: 167, AI Research Engineer: 153, Data Scientist:
  145 of 100K) → this is needle-finding, so **recall of genuine builders** matters more
  than fine-grained ordering of mediocre fits.
- Honeypot signatures are **sharp and rare** (~20 each: a role lasting longer than the
  time since it began; "expert" skills with 0 months of use; total tenure far exceeding
  stated experience) → safe to hard-gate.
- The plausible-looking inconsistency (skill-duration > years-of-experience) fires on
  **9,231 real-looking profiles** → hard-filtering it would false-negative ~9% of the
  pool; it must only soft-discount.
- Every candidate is ≥36 days inactive (median 141) → recency is a *relative* signal.

## 3. Scoring: consensus gate over weighted sum
`core = sqrt(role_fit × evidence_fit) × (0.55 + 0.20·experience + 0.15·skill_trust + 0.10·trajectory)`

A weighted sum lets a stuffed skill list compensate for a wrong title — exactly the
planted trap. A geometric gate collapses when either pillar fails: fraud can spike one
signal but cannot forge agreement across all of them.

- **role_fit** — current/past titles vs the intelligence-layer role (strong / adjacent /
  non-technical), with past-title rescue for people transitioning into ML.
- **evidence_fit** — read from `career_history` descriptions (what they *did*), not the
  headline (what they *claim*). Keyword rubric ⊕ a semantic channel: MiniLM embeddings of
  career text vs five JD facets, precomputed offline, blended as
  `max(kw, 0.55·kw + 0.45·sem)` — semantic **augments**, never replaces, evidence. This
  rescues the JD's "Tier-5 gem" (elite ranking work described in plain language).
- **skill_trust** — proficiency × endorsements × months-used, discounted when a claimed
  skill never appears in the described work.
- **Trajectory / experience** — 6–8y ideal band; anti-title-chaser tenure factor;
  services-only-career discount; CV/speech/robotics-primary penalty (all explicit JD
  disqualifiers).
- **Availability multiplier** — recruiter response rate, recency, open-to-work, notice
  period. A perfect profile that won't reply is not a hire (JD, verbatim).
- **Integrity layer** — hard-gates the impossible (honeypots), soft-discounts the noisy.
- **Reasoning** — deterministic, field-grounded justification + one honest concern per
  ranked candidate. Hallucination is structurally impossible; tone tracks rank.

## 4. Evaluation without a leaderboard
No feedback loop exists, so we built one:
- **Gold set** — 55 hand-labeled candidates (stratified: strong fits, adjacents,
  keyword-stuffers, honeypots, CV-primary), tiered 0–4 by holistic JD reading,
  independent of the scoring formula. Scored on the challenge's own composite:
  **NDCG@10 0.93 · NDCG@50 0.99 · MAP 0.96 · P@10 1.00 · composite 0.95.**
- **Full-pool trap-leak test** — traps admitted to the true top-100 of 100,000:
  **ours 0/0/0** (honeypots/stuffers/CV-primary) vs 2/33/5 for a naive skill-keyword
  scorer and 2/0/10 for a typical title+skill%+YoE weighted sum.
- **Ablations** — removing any single defense still leaks 0: the layers overlap by
  design (defense-in-depth), so no single forged signal has a path to the top.
- **Decision discipline** — the semantic layer was adopted only after this harness
  vetted it (an earlier, looser blend was rejected for over-boosting semantically
  adjacent tier-2s). With effectively one submission attempt, we tune against our own
  measurements, never against hope.

## 5. Compute honesty
Rank step: ~12 s for 100K on a laptop CPU, no network, <200 MB RAM (constraints: 5 min /
16 GB / offline). The only heavy step (embedding 100K career texts, ~12 min) runs offline
once; its 2.3 MB output ships with the repo, so judges can reproduce the ranking with one
command without re-embedding:

```
python rank.py --candidates ./data/candidates.jsonl --out ./the_last_commit.csv
```

## 6. What we deliberately did not do
- **No LLM calls at rank time** — banned by the rules, and unscalable for a 200K-pool
  production system (the challenge's own stated rationale).
- **No learned black-box ranker** — we prototyped the idea and dropped it: with 55 labels
  it would overfit, and it can't explain a single decision in a Stage-5 interview.
- **No hard filters on noisy signals** — measured 9% false-negative cost; discounts only.
