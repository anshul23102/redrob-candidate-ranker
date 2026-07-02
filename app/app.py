"""Sandbox demo — run the ranker end-to-end on a small candidate sample (<=100).

Satisfies submission_spec §10.5: accepts an uploaded JSONL/JSON sample (or uses the
bundled 50-candidate sample), runs the EXACT same scoring pipeline as rank.py
(CPU-only, no network), and shows the ranked shortlist with reasoning + concerns.

Run:  streamlit run app/app.py
"""
import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.scoring.score import score_candidate           # noqa: E402
from src.integrity.checks import integrity              # noqa: E402
from src.reasoning.reason import make_reason            # noqa: E402
from src.retrieval.semantic import load_semantic, semantic_fit  # noqa: E402

st.set_page_config(page_title="The Last Commit — Candidate Ranker", layout="wide")

st.title("Intelligent Candidate Ranker")
st.caption("The Last Commit · India Runs Track 1 · consensus-gated, fraud-hardened, "
           "explainable — CPU-only, offline, ~0.1 ms per candidate")

sem_on = load_semantic(str(ROOT / "artifacts" / "semantic.json"))
with st.sidebar:
    st.header("How it works")
    st.markdown(
        "1. **Role consensus gate** — evidence can't rescue a wrong title\n"
        "2. **Evidence from the work** — career descriptions, not headlines\n"
        "3. **Integrity layer** — impossible profiles hard-gated (honeypots)\n"
        "4. **Availability signals** — response rate, recency, notice period\n"
        "5. **Grounded reasoning** — every claim from real fields + one honest concern"
    )
    st.markdown(f"Semantic layer: {'🟢 on (precomputed)' if sem_on else '⚪ off — keyword rubric only'}")
    topk = st.slider("Show top", 5, 100, 20, 5)

up = st.file_uploader("Upload candidate sample (.json list or .jsonl, ≤100 candidates)",
                      type=["json", "jsonl"])

def load_sample():
    if up is not None:
        raw = up.read().decode("utf-8")
        try:
            data = json.loads(raw)
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError:
            return [json.loads(l) for l in raw.splitlines() if l.strip()]
    return json.load(open(ROOT / "data" / "sample_candidates.json"))

cands = load_sample()[:100]
st.write(f"**{len(cands)} candidates loaded** "
         f"({'uploaded file' if up else 'bundled 50-candidate sample'})")

if st.button("Rank candidates", type="primary"):
    rows = []
    for c in cands:
        s, f = score_candidate(c, integrity, sem_fit=semantic_fit(c["candidate_id"]))
        rows.append((s, c, f))
    rows.sort(key=lambda r: (-r[0], r[1]["candidate_id"]))

    for rank, (s, c, f) in enumerate(rows[:topk], start=1):
        p = c["profile"]
        reason = make_reason(c, f)
        with st.container(border=True):
            left, right = st.columns([5, 1])
            with left:
                st.markdown(f"**#{rank} · {p['current_title']}** — "
                            f"{p.get('location','?')} · {p['years_of_experience']:.1f}y "
                            f"· `{c['candidate_id']}`")
                st.markdown(reason)
                st.progress(min(1.0, s),
                            text=f"score {s:.3f} · role {f['role_fit']:.2f} · "
                                 f"evidence {f['evidence_fit']:.2f} · "
                                 f"availability {f['availability']:.2f}"
                                 + (" · ⚠️ integrity-flagged" if f["honeypot"] else ""))
            with right:
                st.metric("score", f"{s:.3f}")
    flagged = sum(1 for _, _, f in rows if f["honeypot"])
    st.info(f"Integrity layer flagged {flagged} of {len(rows)} candidates in this sample "
            "(hard-gated out of top ranks).")
