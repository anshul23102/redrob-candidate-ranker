#!/usr/bin/env python3
"""Evaluate the ranker on the hand-labeled gold set, with ablations.

Reconstructs variant scores from the shared facet values so each ablation isolates
exactly one design choice. Reports the challenge composite for each.
"""
import json
from src.schema import load_candidates
from src.scoring.score import score_candidate
from src.integrity.checks import integrity
from src.retrieval.semantic import load_semantic, semantic_fit
from src import jd_rubric as R
from src.eval.metrics import composite

GOLD = json.load(open("src/eval/gold_labels.json"))["labels"]
W = R.WEIGHTS


def variants(c, f):
    core, avail, loc = f["core"], f["availability"], f["location"]
    soft, hp = f["integ_soft"], f["honeypot"]
    integ = 0.02 if hp else soft
    wcore = (W["role_fit"] * f["role_fit"] + W["evidence_fit"] * f["evidence_fit"]
             + W["skill_trust"] * f["skill_trust"] + W["experience_fit"] * f["experience_fit"]
             + W["trajectory_fit"] * f["trajectory_fit"])
    return {
        "FULL (ours)":            core * avail * loc * integ,
        "ablate: weighted-sum":   wcore * avail * loc * integ,      # no consensus gate
        "ablate: no honeypot gate": core * avail * loc * soft,      # honeypots not buried
        "ablate: no availability": core * loc * integ,              # ignore signals
        "ablate: no integrity":    core * avail * loc,              # no fraud layer
    }


def main():
    sem_on = load_semantic()
    print(f"(semantic layer: {'ON' if sem_on else 'OFF (keyword-only)'})")
    rows = {}          # cid -> (tier, {variant: score}, honeypot)
    for c in load_candidates("./data/candidates.jsonl"):
        cid = c["candidate_id"]
        if cid in GOLD:
            _, f = score_candidate(c, integrity, sem_fit=semantic_fit(cid))
            rows[cid] = (GOLD[cid], variants(c, f), f["honeypot"])
            if len(rows) == len(GOLD):
                break

    names = list(next(iter(rows.values()))[1].keys())
    print(f"Gold set: {len(rows)} candidates "
          f"({sum(1 for t,_,_ in rows.values() if t>=3)} relevant tier>=3, "
          f"{sum(1 for _,_,h in rows.values() if h)} honeypots)\n")
    print(f"{'variant':<26}{'NDCG@10':>9}{'NDCG@50':>9}{'MAP':>8}{'P@10':>8}{'COMPOSITE':>11}{'HP@10':>7}")
    print("-" * 78)
    for nm in names:
        ranked = sorted(rows.items(), key=lambda kv: (-kv[1][1][nm], kv[0]))
        rels = [tier for _, (tier, _, _) in ranked]
        hp_top10 = sum(1 for _, (_, _, h) in ranked[:10] if h)
        m = composite(rels)
        print(f"{nm:<26}{m['NDCG10']:>9.3f}{m['NDCG50']:>9.3f}{m['MAP']:>8.3f}"
              f"{m['P10']:>8.3f}{m['composite']:>11.3f}{hp_top10:>7d}")

    # show FULL model's ordering of the gold set
    print("\nFULL model — gold set in ranked order (tier | score | id):")
    ranked = sorted(rows.items(), key=lambda kv: (-kv[1][1]["FULL (ours)"], kv[0]))
    for cid, (tier, sc, hp) in ranked:
        flag = "  <-- HONEYPOT" if hp else ""
        print(f"  t{tier}  {sc['FULL (ours)']:.3f}  {cid}{flag}")


if __name__ == "__main__":
    main()
