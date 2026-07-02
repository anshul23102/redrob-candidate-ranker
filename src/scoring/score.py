"""Consensus-gated multi-signal scorer.

Not a weighted sum. role_fit and evidence_fit are the two pillars, combined with a
GEOMETRIC gate (sqrt(role*evidence)) so either pillar being weak collapses the score -
this is what makes keyword-stuffers (great skills, wrong title) unable to reach the top.
Supporting facets (experience, skill-trust, trajectory) only refine ordering.
Availability + integrity + location apply as bounded multipliers.
"""
from src import jd_rubric as R
from src.schema import (joined_text, career_text, headline_text, skill_names,
                        avg_tenure_months, days_inactive)

PROF_W = {"beginner": 0.3, "intermediate": 0.6, "advanced": 0.85, "expert": 1.0}
AI_VOCAB = set(R.CORE_EVIDENCE) | set(R.ML_EVIDENCE) | set(R.INFRA_EVIDENCE)


def _sat(n, k):
    return min(1.0, n / k) if k else 0.0


def role_fit(c):
    p = c.get("profile") or {}
    cls = R.title_class(p.get("current_title"))
    base = {"strong": 0.9, "med": 0.55, "other": 0.35, "nontech": 0.10}[cls]
    # a strong PAST title lifts a currently-ambiguous person (transitioning into ML)
    if cls in ("med", "other"):
        for j in (c.get("career_history") or []):
            if R.title_class(j.get("title")) == "strong":
                base = max(base, 0.68)
                break
    return base, cls


def evidence_fit(c):
    """Read evidence from the WORK (career descriptions), not the headline.

    Headline/summary claims count only at a small discount, so a stuffed one-liner
    cannot manufacture fit.
    """
    cw = career_text(c)
    hw = headline_text(c)
    core = R.count_hits(cw, R.CORE_EVIDENCE)
    ml = R.count_hits(cw, R.ML_EVIDENCE)
    infra = R.count_hits(cw, R.INFRA_EVIDENCE)
    ev = R.count_hits(cw, R.EVAL_EVIDENCE)
    score = (0.50 * _sat(core, 3) + 0.25 * _sat(ml, 3)
             + 0.15 * _sat(infra, 2) + 0.10 * _sat(ev, 1))
    # small credit for headline-only claims (max +0.06) - a hint, not proof
    hl = R.count_hits(hw, R.CORE_EVIDENCE) + R.count_hits(hw, R.ML_EVIDENCE)
    score += 0.06 * _sat(hl, 4)
    return min(1.0, score), dict(core=core, ml=ml, infra=infra, eval=ev)


def cv_primary_penalty(c, core_desc_hits):
    """JD disqualifier: CV/speech/robotics-primary without significant IR/NLP exposure."""
    t = ((c.get("profile") or {}).get("current_title") or "").lower()
    cw = career_text(c)
    cv_hits = R.count_hits(cw, R.CV_SPEECH_ROBOTICS)
    title_cv = any(k in t for k in R.CV_TITLE)
    if (title_cv or cv_hits >= 2) and core_desc_hits < 3:
        return 0.55
    return 1.0


def skill_trust(c, text):
    tot = 0.0
    for s in (c.get("skills") or []):
        nm = (s.get("name") or "").lower()
        if nm not in AI_VOCAB:
            continue
        pf = PROF_W.get(s.get("proficiency"), 0.5)
        endo = 0.5 + 0.5 * _sat(s.get("endorsements") or 0, 15)
        dur = s.get("duration_months") or 0
        dur_f = 0.4 + 0.6 * _sat(dur, 24) if dur > 0 else 0.25  # 0-month claims distrusted
        grounded = 1.15 if nm in text else 0.55  # claimed but unseen in work → discount
        tot += pf * endo * dur_f * grounded
    return min(1.0, tot / 3.0)


def experience_fit(c):
    y = (c.get("profile") or {}).get("years_of_experience") or 0
    if 6 <= y <= 8:      band = 1.0
    elif 5 <= y < 6 or 8 < y <= 9:   band = 0.82
    elif 4 <= y < 5 or 9 < y <= 11:  band = 0.60
    elif 3 <= y < 4 or 11 < y <= 13: band = 0.42
    else:                band = 0.25
    ten = avg_tenure_months(c)
    if ten < 12:   tf = 0.55        # serial job-hopper (JD: title-chaser)
    elif ten < 18: tf = 0.75
    elif ten >= 36: tf = 1.05
    else:          tf = 1.0
    return max(0.0, min(1.0, band * tf))


def trajectory_fit(c, text, ev):
    ch = c.get("career_history") or []
    names = " ".join((j.get("company") or "").lower() for j in ch)
    ind = ((c.get("profile") or {}).get("current_industry") or "").lower()
    svc = sum(1 for comp in R.SERVICES_COMPANIES if comp in names)
    base = 0.6
    if ev["core"] or ev["ml"]:
        base += 0.2                      # real ML/product-style work described
    if svc and len(ch):
        base -= 0.25                     # services-heavy career (JD disfavors)
    if "it services" in ind or "consulting" in ind:
        base -= 0.10
    return max(0.1, min(1.0, base))


def availability_mult(c):
    rs = c.get("redrob_signals") or {}
    resp = (rs.get("recruiter_response_rate") or 0) / 0.9
    rec = max(0.0, min(1.0, (276 - days_inactive(c)) / (276 - 36)))
    opn = 1.0 if rs.get("open_to_work_flag") else 0.4
    notice = max(0.0, min(1.0, 1 - (rs.get("notice_period_days") or 90) / 180))
    avail = 0.40 * min(1, resp) + 0.30 * rec + 0.15 * opn + 0.15 * notice
    return 0.65 + 0.45 * avail          # in [0.65, 1.10]


def location_mult(c):
    loc = ((c.get("profile") or {}).get("location") or "").lower()
    for hub, w in R.HUB_WEIGHTS.items():
        if hub in loc:
            return 1.0 + 0.06 * w
    if (c.get("redrob_signals") or {}).get("willing_to_relocate"):
        return 1.02
    return 1.0


def score_candidate(c, integrity_fn, sem_fit=None):
    cw = career_text(c)
    rf, rcls = role_fit(c)
    ef_kw, ev = evidence_fit(c)
    # Blend semantic relevance (precomputed) with keyword evidence. Semantic AUGMENTS
    # keyword evidence (rescues concise elite profiles) but never replaces it - pure
    # embedding similarity on short texts is too noisy to stand alone, and wrong-role /
    # impossible profiles stay gated below regardless.
    ef = ef_kw if sem_fit is None else max(ef_kw, 0.55 * ef_kw + 0.45 * sem_fit)
    st = skill_trust(c, cw)                        # grounded in the work, not the headline
    xf = experience_fit(c)
    tf = trajectory_fit(c, cw, ev)

    gate = (rf * ef) ** 0.5                        # consensus of the two pillars
    core = gate * (0.55 + 0.20 * xf + 0.15 * st + 0.10 * tf)

    # CV/speech/robotics-primary without IR exposure (JD disqualifier)
    cvp = cv_primary_penalty(c, ev["core"])
    core *= cvp

    # research-only / framework-only cues - a red flag ONLY on otherwise-weak profiles
    # (avoids nuking a strong engineer who merely mentions "academic"/"research").
    if ef < 0.4 and (R.count_hits(cw, R.RESEARCH_ONLY) or R.count_hits(cw, R.FRAMEWORK_ONLY)):
        core *= 0.8

    hard, soft, ireasons = integrity_fn(c)
    integ = 0.02 if hard else soft
    final = core * availability_mult(c) * location_mult(c) * integ
    final = max(0.0, min(0.999, final))

    facets = dict(role_fit=rf, role_class=rcls, evidence_fit=ef, ev=ev, skill_trust=st,
                  experience_fit=xf, trajectory_fit=tf, gate=gate, core=core,
                  availability=availability_mult(c), location=location_mult(c),
                  honeypot=hard, integ_soft=soft, cv_pen=cvp, integ_reasons=ireasons)
    return final, facets
