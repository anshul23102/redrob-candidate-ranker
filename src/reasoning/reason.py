"""Grounded reasoning + a devil's-advocate counter-signal for each ranked candidate.

Every claim is derived from real fields (zero hallucination) and the concern is chosen
from the candidate's actual weakest signal, so tone always matches rank (Stage-4 checks).
"""
from src import jd_rubric as R
from src.schema import joined_text, days_inactive


def _present(text, phrases, k=2):
    hits = [p for p in phrases if p in text]
    return hits[:k]


def make_reason(c, facets):
    p = c.get("profile") or {}
    rs = c.get("redrob_signals") or {}
    text = joined_text(c)
    title = p.get("current_title") or "candidate"
    yoe = p.get("years_of_experience") or 0

    # --- positive, grounded in evidence actually found ---
    bits = []
    core = _present(text, R.CORE_EVIDENCE, 2)
    ml = _present(text, R.ML_EVIDENCE, 1)
    if core:
        bits.append("career shows " + " & ".join(core))
    elif ml:
        bits.append("background in " + ml[0])
    gh = rs.get("github_activity_score")
    if gh and gh >= 40:
        bits.append(f"GitHub activity {gh:.0f}")
    resp = rs.get("recruiter_response_rate")
    if resp is not None and resp >= 0.6:
        bits.append(f"responsive to recruiters ({resp:.2f})")
    ev = facets["ev"]
    if ev["eval"]:
        bits.append("evaluation-metric experience (NDCG/MRR/A-B)")
    pos = f"{title}, {yoe:.1f}y" + ("; " + "; ".join(bits) if bits else "")

    # --- one honest concern: the candidate's most salient weakness ---
    di = days_inactive(c)
    notice = rs.get("notice_period_days")
    concern = None
    if facets["honeypot"]:
        concern = "profile has internal inconsistencies (" + \
                  (facets["integ_reasons"][0] if facets["integ_reasons"] else "flagged") + ")"
    elif facets["evidence_fit"] < 0.25:
        concern = "limited direct retrieval/ranking evidence in career history"
    elif facets["role_class"] == "nontech":
        concern = "current title is outside core engineering"
    elif resp is not None and resp < 0.25:
        concern = f"low recruiter response rate ({resp:.2f})"
    elif di > 200:
        concern = f"inactive on platform for ~{di} days"
    elif facets["trajectory_fit"] < 0.45:
        concern = "services-heavy background vs the JD's product-company preference"
    elif not (yoe and 5 <= yoe <= 9):
        concern = f"{yoe:.1f}y experience is outside the 5-9y target band"
    elif notice and notice > 60:
        concern = f"long notice period ({notice} days)"
    elif not rs.get("open_to_work_flag"):
        concern = "not marked open-to-work"
    else:
        concern = "few remaining concerns; verify recency of hands-on coding"

    reason = f"{pos}. Concern: {concern}."
    # keep it tidy for CSV / the 1-2 sentence spec
    return " ".join(reason.split())[:300]
