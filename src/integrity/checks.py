"""Profile-integrity / honeypot detection.

Design decision (from data profiling): the spec's ~80 honeypots are 'subtly impossible'
profiles. The SHARP, rare signatures (each ~20 in the pool) are true honeypots; the noisy
`skill_duration > YoE` (fires ~9K times) is a soft inconsistency, NOT a honeypot flag.

We HARD-gate hard-impossibilities out of the top, and only SOFT-discount soft ones -
because hard-filtering soft signals creates false negatives on real people (JD's spirit).
"""
from src.schema import parse_date, TODAY


def integrity(c):
    """Return (is_honeypot: bool, trust_multiplier in (0,1], reasons: list[str])."""
    reasons = []
    hard = False
    soft = 1.0

    yoe = (c.get("profile") or {}).get("years_of_experience") or 0
    ch = c.get("career_history") or []
    sk = c.get("skills") or []

    # --- HARD impossibilities (honeypots) -----------------------------------
    sumdur = sum((j.get("duration_months") or 0) for j in ch)
    if yoe > 0 and sumdur > yoe * 12 + 24:
        hard = True
        reasons.append(f"claimed tenure ({sumdur} mo) far exceeds {yoe:.0f}y experience")

    for j in ch:
        sd = parse_date(j.get("start_date"))
        ed = parse_date(j.get("end_date")) if j.get("end_date") else None
        dm = j.get("duration_months") or 0
        if sd and dm > 0 and dm > ((TODAY - sd).days / 30.4) + 3:
            hard = True
            reasons.append(f"role duration ({dm} mo) longer than time since it began")
            break
        if sd and ed and ed < sd:
            hard = True; reasons.append("a role ends before it starts"); break
        if sd and sd > TODAY:
            hard = True; reasons.append("a role starts in the future"); break

    n_expert0 = sum(1 for s in sk if s.get("proficiency") == "expert"
                    and (s.get("duration_months") or 0) == 0)
    if n_expert0 >= 2:
        hard = True
        reasons.append(f"{n_expert0} 'expert' skills with 0 months of use")

    # --- SOFT inconsistencies (discount, never gate) ------------------------
    n_skilldur_over = sum(1 for s in sk
                          if yoe > 0 and (s.get("duration_months") or 0) > yoe * 12 + 12)
    if n_skilldur_over:
        soft *= max(0.85, 1 - 0.03 * n_skilldur_over)

    completeness = (c.get("redrob_signals") or {}).get("profile_completeness_score") or 0
    if completeness < 35:
        soft *= 0.95  # thin profile → mild uncertainty discount

    return hard, soft, reasons
