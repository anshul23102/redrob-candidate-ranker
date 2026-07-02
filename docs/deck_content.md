# Deck content — paste into the mandatory Redrob/H2S Slides template
(Make a copy of the template from the Submissions page; keep their layout, use this text.)

---
## Slide 1 — Cover (template fields)
- **Team Name:** The Last Commit
- **Team Leader Name:** Tripti Kashyap
- **Problem Statement:** The Data & AI Challenge — Intelligent Candidate Discovery & Ranking

---
## Slide 2 — The problem, restated in our words
Keyword filters can't see what matters. In this 100K pool, the perfect-looking profiles
are often the *worst* answers: keyword-stuffed skill lists on non-technical titles,
"impossible" honeypot profiles, and unavailable candidates. Meanwhile the best hires
describe elite ranking work in plain language and never say "RAG" or "Pinecone."

**Our thesis: don't build a better keyword matcher — reconstruct the recruiter's
decision function.** The JD tells you what a great recruiter checks; we turned that
into code, layer by layer.

---
## Slide 3 — What we built (architecture)
- **Consensus gate, not weighted sum** — `sqrt(role_fit × evidence_fit)`: evidence
  can't rescue a wrong title, a title can't rescue empty evidence. Stuffers die here.
- **Evidence from the work** — fit is read from career-history descriptions (what they
  actually did), not headlines. A precomputed local-embedding layer (MiniLM) catches
  strong candidates who describe ranking systems in plain words.
- **Integrity layer** — impossible profiles (role longer than time-since-start,
  "expert" skills never used, tenure ≫ experience) are hard-gated; noisy
  inconsistencies only discounted (hard-filtering would drop 9% of real people).
- **Availability multiplier** — response rate, recency, notice period, open-to-work:
  a perfect profile that won't reply isn't a hire (straight from the JD).
- **Grounded reasoning + one honest concern per candidate** — every claim traceable
  to a profile field; zero hallucination; tone matches rank.
- **Compute:** 100K candidates ranked in ~11s, CPU-only, fully offline. Scales to
  Redrob's 200K-pool production reality.

---
## Slide 4 — Why you can trust it (we measured, no leaderboard needed)
**Gold-set eval** (55 hand-labeled candidates, the challenge's own composite):
NDCG@10 **0.931** · NDCG@50 0.987 · MAP 0.944 · composite **0.953**

**Full-pool trap-leak test** (traps admitted into the true top-100 of 100,000):
| ranker | honeypots | stuffers | CV-primary |
|---|---|---|---|
| **ours** | **0** | **0** | **0** |
| naive skill-keyword (the JD's stated trap) | 2 | 33 | 5 |
| title+skill%+YoE (typical weighted sum) | 2 | 0 | 10 |

Defense-in-depth: removing any single layer still leaks 0 — a trap must beat the
role gate AND the evidence reader AND skill-grounding AND integrity simultaneously.

---
## Slide 5 — Why this matters to Redrob (beyond the hackathon)
This is the JD's own 90-day plan, built: hybrid evidence (lexical ⊕ semantic),
an evaluation framework (gold labels, NDCG/MAP, ablations, trap-leak tests), and
recruiter-trustable output (reasons + honest concerns). It's JD-agnostic — swap the
rubric, re-run, done — and the latency-quality tradeoff (precompute heavy, rank
light) is exactly how a 200K-candidate production system has to work.

**Demo:** [sandbox link] — upload any candidate sample, watch it rank, read the reasons.
**Repo:** [github link] — one command reproduces our submission CSV.
