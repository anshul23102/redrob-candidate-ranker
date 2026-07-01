#!/usr/bin/env python3
"""Print full facet breakdown for specific candidate ids (diagnosis, not shipped logic)."""
import sys
from src.schema import load_candidates, avg_tenure_months
from src.scoring.score import score_candidate
from src.integrity.checks import integrity

IDS = set(sys.argv[1:]) or {
    "CAND_0076163",  # tier-4 LTR engineer, under-ranked
    "CAND_0018499",  # tier-4 top
    "CAND_0088385",  # tier-2 CV engineer, over-ranked
    "CAND_0067866",  # tier-3 SWE(ML)
    "CAND_0060726",  # keyword stuffer (HR Manager)
}

for c in load_candidates("./data/candidates.jsonl"):
    if c["candidate_id"] not in IDS:
        continue
    s, f = score_candidate(c, integrity)
    p = c["profile"]
    print(f"\n=== {c['candidate_id']}  final={s:.3f} ===")
    print(f"  title={p['current_title']!r} yoe={p['years_of_experience']} avg_tenure={avg_tenure_months(c):.0f}mo")
    print(f"  role_fit={f['role_fit']:.2f}({f['role_class']}) evidence_fit={f['evidence_fit']:.2f} ev={f['ev']}")
    print(f"  skill_trust={f['skill_trust']:.2f} experience_fit={f['experience_fit']:.2f} trajectory={f['trajectory_fit']:.2f}")
    print(f"  gate={f['gate']:.2f} core={f['core']:.2f} avail={f['availability']:.2f} loc={f['location']:.2f} honeypot={f['honeypot']}")
    print("  career:")
    for j in (c.get("career_history") or []):
        print(f"    {j.get('duration_months'):>3}mo {j.get('title')!r} @ {j.get('company')} :: {(j.get('description') or '')[:110]}")
