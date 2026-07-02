<div align="center">

# The Last Commit
### Intelligent Candidate Discovery & Ranking · India Runs Track 1

Ranks the **top 100 of 100,000 candidates** for Redrob's *"Senior AI Engineer, Founding Team"* job description.

![runtime](https://img.shields.io/badge/rank_time-~12s_for_100K-6D28D9)
![compute](https://img.shields.io/badge/CPU_only-no_GPU-2ea44f)
![network](https://img.shields.io/badge/rank--time_network-zero-2ea44f)
![validator](https://img.shields.io/badge/official_validator-passing-2ea44f)
![traps](https://img.shields.io/badge/traps_in_top--100-0%2F0%2F0-6D28D9)

</div>

> We don't build a keyword matcher. We **reconstruct the recruiter's decision function**:
> a consensus-gated, fraud-hardened, explainable ranker that reads career history (not
> skill lists), hard-gates impossible profiles, weights real availability signals, and
> emits a falsifiable reason **plus one honest concern** for every pick. All of it in
> about 12 seconds, on a laptop CPU, fully offline.

---

## Results at a glance

**Gold-set evaluation.** 55 hand-labeled candidates (stratified across strong fits,
adjacents, keyword-stuffers, honeypots, and CV-primary profiles), scored on the
challenge's own composite formula:

| NDCG@10 | NDCG@50 | MAP | P@10 | Composite |
|:---:|:---:|:---:|:---:|:---:|
| 0.93 | 0.99 | 0.96 | 1.00 | **0.95** |

**Full-pool trap-leak test.** How many planted traps each ranker admits into the true
top-100 of 100,000:

| Ranker | Honeypots | Keyword-stuffers | CV-primary |
|---|:---:|:---:|:---:|
| **Ours** | **0** | **0** | **0** |
| Naive skill-keyword count (the trap the JD warns about) | 2 | 33 | 5 |
| Title + skill% + YoE weighted sum (the typical baseline) | 2 | 0 | 10 |

Removing any single defense still leaks zero. The layers overlap by design
(defense-in-depth): a trap must beat the role gate, the evidence reader,
skill-grounding, and the integrity layer at the same time.

---

## Reproduce the submission

```bash
pip install -r requirements.txt

# optional one-time offline prep (~12 min on CPU); a precomputed
# 2.3 MB artifact already ships in artifacts/, so you can skip this
python scripts/precompute_embeddings.py

# the ranking step: CPU-only, no network, budget 5 min, actual ~12 s
python rank.py --candidates ./data/candidates.jsonl --out ./the_last_commit.csv

# format check with the organizer's own validator
python validate_submission.py ./the_last_commit.csv   # -> "Submission is valid."
```

If `artifacts/semantic.json` is absent the ranker falls back to the keyword rubric:
still valid, slightly lower fidelity. The ranking step never loads a model and never
touches the network; it reads precomputed scalars.

**Try it in one click:** [Colab sandbox](https://colab.research.google.com/github/anshul23102/redrob-candidate-ranker/blob/main/notebooks/sandbox.ipynb)
runs the full pipeline on a 50-candidate sample, end to end. A Streamlit demo
(`streamlit run app/app.py`) does the same with a UI, on any uploaded sample of up
to 100 candidates.

---

## How it works

```
candidates.jsonl (100K)                          OFFLINE, ONCE
        |                                MiniLM embeddings of career text
        v                                   -> artifacts/semantic.json
+---- rank.py (CPU, no network, ~12 s) --------------------------------+
|                                                                      |
|  1. ROLE GATE        current + past titles vs the target role        |
|  2. EVIDENCE         career descriptions, keyword + semantic blend   |
|         core = sqrt(role_fit x evidence_fit)   <- consensus gate     |
|  3. REFINE           skill-trust · experience band · trajectory      |
|  4. WEIGHT           availability · location · integrity multipliers |
|  5. EXPLAIN          top-100 -> grounded reason + one honest concern |
|                                                                      |
+----> the_last_commit.csv  (candidate_id, rank, score, reasoning) ----+
```

### The three decisions that matter

**1. Consensus gate, not a weighted sum.**
`core = sqrt(role_fit x evidence_fit) x refinements`. A weighted sum lets a gaudy
skill list paper over a wrong title, which is exactly the dataset's keyword-stuffer
trap. A geometric gate collapses when either pillar fails: fraud can spike one
signal, but it cannot forge agreement across all of them.

**2. Evidence from the work, not the headline.**
All fit evidence is read from `career_history` descriptions, i.e. what the candidate
actually did. Headline and summary claims earn a token credit only. A semantic layer
(MiniLM, precomputed offline, blended as `max(kw, 0.55*kw + 0.45*sem)`) rescues
strong candidates who describe elite ranking work in plain language, the JD's
"Tier-5 gem" case, without letting raw embedding similarity stand alone.

**3. Hard-gate the impossible, soft-discount the noisy.**
Honeypot signatures (a role lasting longer than the time since it began, "expert"
skills with zero months of use, claimed tenure far beyond stated experience) are rare
(~44 in the pool) and hard-gated. The tempting-but-noisy inconsistency
(skill-duration exceeding years of experience) fires on 9% of the pool, so it is
soft-discounted only: hard-filtering it would false-negative thousands of real people.

### Explainability that survives review

Every ranked candidate ships a one-to-two sentence reason generated deterministically
from real profile fields, so hallucination is structurally impossible, plus **one
honest concern** drawn from the candidate's weakest actual signal, so tone always
matches rank. Example from our output:

> *"7.0y Staff Machine Learning Engineer; hands-on retrieval & ranking work at Paytm;
> active GitHub (score 68); replies to 95% of recruiter messages. Main caveat: average
> stint is only ~21 months across 4 roles."*

The cited facts and the concern both vary per candidate (rotated deterministically by
candidate id), so no two of the 100 rows read templated: 100/100 unique reasonings.

---

## Evaluation protocol (there is no leaderboard, so we built one)

1. **Hand-labeled gold set**: 55 candidates tiered 0 to 4 by holistic JD reading,
   independent of the scoring formula (`src/eval/gold_labels.json`).
2. **The challenge's own metrics**: NDCG@10/@50, MAP, P@10, composite
   (`src/eval/metrics.py`, `scripts/run_eval.py`), plus per-design ablations.
3. **Full-pool trap-leak tests** against naive baselines (`scripts/leak_test.py`).
4. **Decision discipline**: the semantic layer shipped only after this harness vetted
   it. An earlier, looser blend was measured, found to over-boost semantically
   adjacent mediocre profiles, and rejected. With effectively one submission attempt,
   we tune against measurements, never against hope.

Full write-up: [docs/METHODOLOGY.md](docs/METHODOLOGY.md), including the data-first
design story and what we deliberately did not build.

---

## Repo map

| Path | What it is |
|---|---|
| `rank.py` | The single reproduce command |
| `src/jd_rubric.py` | The JD, encoded as machine-readable evidence sets |
| `src/scoring/score.py` | Consensus-gated multi-signal scorer |
| `src/integrity/checks.py` | Honeypot / impossibility layer |
| `src/reasoning/reason.py` | Grounded reasoning + honest-concern generator |
| `src/retrieval/semantic.py` | Rank-time lookup of precomputed semantic scores |
| `scripts/precompute_embeddings.py` | Offline MiniLM embedding of career texts |
| `scripts/profile_data.py` | The 100K-pool profiler that drove the design |
| `src/eval/` + `scripts/run_eval.py` | Gold labels, challenge metrics, ablations |
| `scripts/leak_test.py` | Full-pool trap-leak comparison vs baselines |
| `app/app.py` | Streamlit sandbox (exact pipeline, small samples) |
| `notebooks/sandbox.ipynb` | One-click Colab sandbox |
| `docs/METHODOLOGY.md` | Methodology document |
| `submission_metadata.yaml` | Submission metadata (mirrors portal entries) |

## Team

**The Last Commit** · IIIT-Delhi
Tripti Kashyap (Lead) · Anshul Jain · Deepak Meena · Kartik Haritwal

*Built for India Runs by Redrob AI x Hack2skill, Track 1: The Data & AI Challenge.*
