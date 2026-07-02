#!/usr/bin/env python3
"""Full-pool trap-leak test: how many traps each scoring variant admits into the true top-100.

This is where design choices show their worth - the gold-set metrics saturate, but at the
100-of-100,000 boundary a weighted sum / a missing gate lets traps through. Ablation by
reconstruction from shared facets, so each column isolates exactly one design decision.
"""
from src.schema import load_candidates, skill_names
from src.scoring.score import score_candidate, AI_VOCAB
from src.integrity.checks import integrity
from src.retrieval.semantic import load_semantic, semantic_fit
from src import jd_rubric as R

W = R.WEIGHTS
AI_TITLE = ("machine learning", "ml engineer", "ai engineer", "data scientist", "nlp",
            "applied scientist", "ai research", "ml ", "ai ")
rows = []

sem_on = load_semantic()
print(f"(semantic layer: {'ON' if sem_on else 'OFF (keyword-only)'})")
for c in load_candidates("./data/candidates.jsonl"):
    _, f = score_candidate(c, integrity, sem_fit=semantic_fit(c["candidate_id"]))
    core, avail, loc = f["core"], f["availability"], f["location"]
    soft, hp, cvp = f["integ_soft"], f["honeypot"], f["cv_pen"]
    integ = 0.02 if hp else soft
    core_no_cv = core / cvp if cvp else core
    wcore = (W["role_fit"] * f["role_fit"] + W["evidence_fit"] * f["evidence_fit"]
             + W["skill_trust"] * f["skill_trust"] + W["experience_fit"] * f["experience_fit"]
             + W["trajectory_fit"] * f["trajectory_fit"]) * cvp

    p = c.get("profile") or {}
    title = (p.get("current_title") or "").lower()
    yoe = p.get("years_of_experience") or 0
    n_ai = sum(1 for n in skill_names(c) if n in AI_VOCAB)
    band = 1.0 if 5 <= yoe <= 9 else 0.5
    title_ai = 1.0 if any(k in title for k in AI_TITLE) else 0.0

    sv = {
        # --- our system + its ablations ---
        "FULL (ours)":              core * avail * loc * integ,
        "  ablate: weighted-sum":   wcore * avail * loc * integ,
        "  ablate: no honeypot gate": core * avail * loc * soft,
        "  ablate: no CV penalty":  core_no_cv * avail * loc * integ,
        # --- naive baselines other teams build ---
        "BASE: skill-keyword count": float(n_ai),                       # the JD's explicit trap
        "BASE: title+skill%+yoe":    0.5 * title_ai + 0.4 * min(1, n_ai / 8) + 0.1 * band,
    }
    is_stuffer = (f["role_class"] == "nontech" and n_ai >= 4)
    rows.append((c["candidate_id"], sv, hp, is_stuffer, cvp < 1.0))

variants = list(rows[0][1].keys())
print(f"Pool: {len(rows)} candidates. Traps present: "
      f"{sum(r[2] for r in rows)} honeypots, {sum(r[3] for r in rows)} stuffers, "
      f"{sum(r[4] for r in rows)} CV-primary.\n")
print(f"{'variant':<26}{'honeypots':>11}{'stuffers':>10}{'CV-primary':>12}   (count in top-100)")
print("-" * 72)
for v in variants:
    top = sorted(rows, key=lambda r: (-r[1][v], r[0]))[:100]
    hp = sum(1 for r in top if r[2])
    st = sum(1 for r in top if r[3])
    cv = sum(1 for r in top if r[4])
    print(f"{v:<26}{hp:>11}{st:>10}{cv:>12}")
