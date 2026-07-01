#!/usr/bin/env python3
"""One-shot profile of the 100K candidate pool. Streams the JSONL; stdlib only."""
import json, sys, statistics as st
from collections import Counter
from datetime import date

PATH = sys.argv[1] if len(sys.argv) > 1 else "./data/candidates.jsonl"
TODAY = date(2026, 7, 2)

AI_SKILLS = {"machine learning","deep learning","nlp","natural language processing","pytorch",
 "tensorflow","embeddings","transformers","llm","llms","rag","information retrieval","recommender",
 "recommendation systems","vector search","faiss","pinecone","retrieval","ranking","bert","semantic search",
 "learning to rank","xgboost","scikit-learn","hugging face","fine-tuning","mlops","elasticsearch"}
TECH_TITLE = ("engineer","developer","scientist","ml ","ai ","data","software","backend","architect","research","devops","full stack","sre")
SERVICES = {"tcs","infosys","wipro","accenture","cognizant","capgemini","tech mahindra","hcl","mindtree","ltimindtree"}

def parse_d(s):
    try: return date.fromisoformat(s)
    except Exception: return None

n=0
titles=Counter(); countries=Counter(); tiers=Counter(); workmode=Counter()
yoe=[]; ncareer=[]; nskills=[]; complete=[]; resp=[]; ghs=[]; last_active_days=[]
open_to_work=0; verified_e=0; willing_reloc=0
ai_skill_counts=[]; stuffer=0
# impossibility / honeypot signatures
imp_dur_gt_yoe=0; imp_expert0=0; imp_skilldur_gt_yoe=0; imp_date_order=0; imp_future=0; imp_sumdur=0
any_impossible=0
india_cities=Counter()
INDIA_HUBS={"bengaluru","bangalore","pune","noida","hyderabad","mumbai","delhi","gurgaon","gurugram","chennai","new delhi","delhi ncr"}
india_hub_hits=0

with open(PATH,"r",encoding="utf-8") as f:
    for line in f:
        if not line.strip(): continue
        c=json.loads(line); n+=1
        p=c.get("profile",{}); ch=c.get("career_history",[]) or []; sk=c.get("skills",[]) or []
        ed=c.get("education",[]) or []; rs=c.get("redrob_signals",{}) or {}
        t=p.get("current_title") or ""
        titles[t]+=1; countries[p.get("country") or "?"]+=1
        y=p.get("years_of_experience") or 0; yoe.append(y)
        ncareer.append(len(ch)); nskills.append(len(sk))
        for e in ed: tiers[e.get("tier","?")]+=1
        loc=(p.get("location") or "").lower()
        if any(h in loc for h in INDIA_HUBS): india_hub_hits+=1
        for h in INDIA_HUBS:
            if h in loc: india_cities[h]+=1; break
        # signals
        complete.append(rs.get("profile_completeness_score") or 0)
        resp.append(rs.get("recruiter_response_rate") or 0)
        ghs.append(rs.get("github_activity_score") if rs.get("github_activity_score") is not None else -1)
        workmode[rs.get("preferred_work_mode") or "?"]+=1
        if rs.get("open_to_work_flag"): open_to_work+=1
        if rs.get("verified_email"): verified_e+=1
        if rs.get("willing_to_relocate"): willing_reloc+=1
        la=parse_d(rs.get("last_active_date") or "")
        if la: last_active_days.append((TODAY-la).days)
        # AI skill / stuffer
        names=[(s.get("name") or "").lower() for s in sk]
        ai_ct=sum(1 for nm in names if nm in AI_SKILLS)
        ai_skill_counts.append(ai_ct)
        tl=t.lower()
        is_tech=any(k in tl for k in TECH_TITLE)
        if ai_ct>=5 and not is_tech: stuffer+=1
        # impossibility checks
        bad=False
        sumdur=sum((j.get("duration_months") or 0) for j in ch)
        if sumdur > (y*12)+18 and y>0: imp_sumdur+=1; bad=True
        for j in ch:
            sd=parse_d(j.get("start_date") or ""); edd=parse_d(j.get("end_date") or "") if j.get("end_date") else None
            dm=j.get("duration_months") or 0
            if sd and dm>0 and dm > ((TODAY-sd).days/30.4)+2: imp_dur_gt_yoe+=1; bad=True; break
            if sd and edd and edd<sd: imp_date_order+=1; bad=True; break
            if sd and sd>TODAY: imp_future+=1; bad=True; break
        for s in sk:
            if (s.get("proficiency")=="expert") and (s.get("duration_months",0)==0): imp_expert0+=1; bad=True; break
        for s in sk:
            if (s.get("duration_months") or 0) > (y*12)+12 and y>0: imp_skilldur_gt_yoe+=1; bad=True; break
        if bad: any_impossible+=1

def pct(a):
    a=sorted(a); q=lambda x:a[min(len(a)-1,int(x*len(a)))]
    if not a: return "no data"
    return f"min={a[0]:.1f} p25={q(.25):.1f} med={q(.5):.1f} p75={q(.75):.1f} p95={q(.95):.1f} max={a[-1]:.1f}"

print(f"N = {n}")
print(f"\n-- years_of_experience --\n{pct(yoe)}")
print(f"-- #career_history --\n{pct(ncareer)}")
print(f"-- #skills --\n{pct(nskills)}")
print(f"-- profile_completeness --\n{pct(complete)}")
print(f"-- recruiter_response_rate --\n{pct(resp)}")
print(f"-- github_activity_score --\n{pct(ghs)}")
print(f"-- last_active_days_ago --\n{pct(last_active_days)}")
print(f"\nopen_to_work: {open_to_work} ({100*open_to_work/n:.1f}%) | willing_relocate: {willing_reloc} ({100*willing_reloc/n:.1f}%) | verified_email: {100*verified_e/n:.1f}%")
print(f"India-hub located: {india_hub_hits} ({100*india_hub_hits/n:.1f}%)  {dict(india_cities.most_common())}")
print(f"\n-- AI-core-skill count per candidate --\n{pct(ai_skill_counts)}")
print(f"likely keyword-STUFFERS (>=5 AI skills but non-technical title): {stuffer} ({100*stuffer/n:.2f}%)")
print(f"\n== IMPOSSIBILITY / HONEYPOT SIGNATURES ==")
print(f"any_impossible: {any_impossible} ({100*any_impossible/n:.2f}%)")
print(f"  sum(job durations) >> YoE: {imp_sumdur}")
print(f"  job duration > time-since-start: {imp_dur_gt_yoe}")
print(f"  expert skill w/ 0 months used: {imp_expert0}")
print(f"  skill duration > YoE: {imp_skilldur_gt_yoe}")
print(f"  end_date < start_date: {imp_date_order} | future start_date: {imp_future}")
print(f"\n-- education tiers --\n{dict(tiers)}")
print(f"-- preferred_work_mode --\n{dict(workmode)}")
print(f"\n-- TOP 30 current_titles --")
for t,ct in titles.most_common(30): print(f"  {ct:5d}  {t}")
print(f"\n-- TOP 12 countries --\n{dict(countries.most_common(12))}")
