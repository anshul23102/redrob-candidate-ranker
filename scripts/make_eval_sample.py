#!/usr/bin/env python3
"""Build a stratified sample for hand-labeling a gold eval set.

Strata: top-by-score, mid, low, keyword-stuffers (trap), honeypots (trap),
and plain-language gems (med/other title but real retrieval/recsys evidence).
Prints a compact card per candidate so we can assign relevance tiers by eye.
"""
import json, random
from src.schema import load_candidates, joined_text, skill_names, days_inactive
from src.scoring.score import score_candidate, AI_VOCAB
from src.integrity.checks import integrity
from src import jd_rubric as R

random.seed(7)
cands = {}
scored = []
for c in load_candidates("./data/candidates.jsonl"):
    s, f = score_candidate(c, integrity)
    cands[c["candidate_id"]] = (c, s, f)
    scored.append((s, c["candidate_id"]))
scored.sort(key=lambda t: (-t[0], t[1]))
order = [cid for _, cid in scored]
rankpos = {cid: i for i, cid in enumerate(order)}

def card(cid, tag):
    c, s, f = cands[cid]
    p = c["profile"]; rs = c.get("redrob_signals", {})
    text = joined_text(c)
    ev = [e for e in R.CORE_EVIDENCE if e in text][:3]
    ml = [e for e in R.ML_EVIDENCE if e in text][:3]
    aiskills = [n for n in skill_names(c) if n in AI_VOCAB][:6]
    print(f"[{tag}] {cid} rankpos={rankpos[cid]+1} score={s:.3f} honeypot={f['honeypot']}")
    print(f"    title={p['current_title']!r} yoe={p['years_of_experience']} loc={p.get('location')} ind={p.get('current_industry')}")
    print(f"    core_ev={ev} ml_ev={ml} ai_skills={aiskills}")
    print(f"    signals: resp={rs.get('recruiter_response_rate')} inactive={days_inactive(c)}d open={rs.get('open_to_work_flag')} gh={rs.get('github_activity_score')} notice={rs.get('notice_period_days')}")
    # one career description snippet
    ch = c.get("career_history") or []
    if ch:
        print(f"    role0: {ch[0].get('title')} @ {ch[0].get('company')} :: {(ch[0].get('description') or '')[:160]}")
    print()

picked = set()
def take(cid, tag):
    if cid not in picked:
        picked.add(cid); card(cid, tag)

print("############ TOP 15 BY SCORE ############\n")
for cid in order[:15]: take(cid, "TOP")
print("############ MID (rank 200-260 sample) ############\n")
for cid in order[200:260:6]: take(cid, "MID")
print("############ LOW (random from bottom half) ############\n")
for cid in random.sample(order[50000:], 8): take(cid, "LOW")

print("############ KEYWORD-STUFFERS (nontech title + >=4 AI skills) ############\n")
cnt = 0
for cid in order:
    c, s, f = cands[cid]
    if f["role_class"] == "nontech" and sum(1 for n in skill_names(c) if n in AI_VOCAB) >= 4:
        take(cid, "STUFFER"); cnt += 1
        if cnt >= 8: break

print("############ HONEYPOTS (integrity hard flag) ############\n")
cnt = 0
for cid in order:
    if cands[cid][2]["honeypot"]:
        take(cid, "HONEYPOT"); cnt += 1
        if cnt >= 6: break

print("############ PLAIN-LANGUAGE GEMS (med/other title + real retrieval/ML evidence) ############\n")
cnt = 0
for cid in order:
    c, s, f = cands[cid]
    text = joined_text(c)
    core = sum(1 for e in R.CORE_EVIDENCE if e in text)
    if f["role_class"] in ("med", "other") and core >= 2 and not f["honeypot"]:
        take(cid, "GEM"); cnt += 1
        if cnt >= 10: break
