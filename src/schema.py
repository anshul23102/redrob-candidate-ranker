"""Candidate loading + lightweight normalized views. Stdlib only (rank-time safe)."""
from __future__ import annotations
import json
from datetime import date

try:
    import orjson  # fast path if available
    def _loads(b): return orjson.loads(b)
except Exception:  # pragma: no cover
    def _loads(b): return json.loads(b)

TODAY = date(2026, 7, 2)


def load_candidates(path):
    """Yield candidate dicts, streaming (memory-safe for the 100K pool)."""
    with open(path, "rb") as f:
        for line in f:
            if line.strip():
                yield _loads(line)


def parse_date(s):
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except Exception:
        return None


def joined_text(c):
    """All free-text a recruiter would read: summary + headline + every role description."""
    p = c.get("profile", {}) or {}
    parts = [p.get("headline") or "", p.get("summary") or ""]
    for j in (c.get("career_history") or []):
        parts.append(j.get("title") or "")
        parts.append(j.get("description") or "")
    return "  ".join(parts).lower()


def career_text(c):
    """Only what the candidate actually DID: role titles + descriptions.

    Evidence is read from here (not the headline) so a buzzword-stuffed headline
    cannot manufacture fit — the work has to back the claim.
    """
    parts = []
    for j in (c.get("career_history") or []):
        parts.append(j.get("title") or "")
        parts.append(j.get("description") or "")
    return "  ".join(parts).lower()


def headline_text(c):
    p = c.get("profile", {}) or {}
    return ((p.get("headline") or "") + "  " + (p.get("summary") or "")).lower()


def skill_names(c):
    return [(s.get("name") or "").lower() for s in (c.get("skills") or [])]


def avg_tenure_months(c):
    ch = c.get("career_history") or []
    durs = [j.get("duration_months") or 0 for j in ch]
    return (sum(durs) / len(durs)) if durs else 0.0


def days_inactive(c):
    d = parse_date((c.get("redrob_signals") or {}).get("last_active_date"))
    return (TODAY - d).days if d else 999
