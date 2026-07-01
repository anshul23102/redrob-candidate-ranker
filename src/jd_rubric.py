"""Structured rubric distilled from the released JD (Senior AI Engineer, Redrob).

Everything the JD explicitly rewards / penalizes, as machine-readable evidence sets.
Kept interpretable on purpose: this is the "reconstruct the recruiter's decision
function" backbone. The offline embedding/ML lift augments — it does not replace — this.
"""

# --- Title signal (the decisive gate against keyword-stuffers) --------------
STRONG_TITLE = ("machine learning", "ml engineer", "ai engineer", "applied scientist",
                "data scientist", "research engineer", "nlp", "search engineer",
                "ranking", "relevance", "recommendation", "research scientist")
MED_TITLE = ("data engineer", "backend", "software engineer", "analytics engineer",
             "full stack", "platform engineer", "cloud engineer", "senior software",
             "devops", "sde", "developer")
NONTECH_TITLE = ("hr ", "human resource", "marketing", "sales", "account", "operations",
                 "mechanical", "civil", "content", "graphic", "customer support",
                 "business analyst", "project manager", "recruiter", "designer",
                 "administrator", "coordinator", "consultant (non-tech)")

# --- Career-history EVIDENCE (read the work, not the skill list) -------------
# Tier-1 evidence: the exact intelligence-layer work the JD owns.
CORE_EVIDENCE = ("retrieval", "ranking", "re-rank", "rerank", "recommend", "recsys",
                 "embedding", "semantic search", "vector search", "vector database",
                 "information retrieval", "relevance", "personalization", "personalisation",
                 "learning to rank", "nearest neighbor", "nearest neighbour", "ann index",
                 "search relevance", "matching system")
# Tier-2 evidence: core modern ML.
ML_EVIDENCE = ("machine learning", "deep learning", "natural language", "nlp",
               "transformer", "bert", "llm", "large language model", "fine-tun",
               "pytorch", "tensorflow", "model training", "feature engineering",
               "hugging face", "sentence-transformer")
# Infra the JD names (vector DBs / hybrid search / scale).
INFRA_EVIDENCE = ("elasticsearch", "opensearch", "solr", "faiss", "pinecone", "weaviate",
                  "qdrant", "milvus", "vector db", "hybrid search", "bm25",
                  "spark", "kafka", "airflow", "feature store")
# Rigor the JD explicitly demands.
EVAL_EVIDENCE = ("ndcg", "mrr", "mean average precision", "map@", "a/b test", "ab test",
                 "offline eval", "evaluation framework", "precision@", "recall@",
                 "online metrics", "recruiter engagement")

# --- Negative / disqualifier cues (JD "explicitly do NOT want") --------------
RESEARCH_ONLY = ("phd student", "postdoc", "research assistant", "academic", "publications only",
                 "purely research", "research lab")
FRAMEWORK_ONLY = ("langchain tutorial", "wrapper around openai", "prompt engineering only")
SERVICES_COMPANIES = ("tcs", "tata consultancy", "infosys", "wipro", "accenture", "cognizant",
                      "capgemini", "tech mahindra", "hcl", "mindtree", "ltimindtree",
                      "mphasis", "l&t infotech")

# --- Location (JD: Pune/Noida offices; Hyd/Mumbai/Delhi NCR/Blr welcome) -----
HUB_WEIGHTS = {"pune": 1.0, "noida": 1.0, "delhi": 0.8, "gurgaon": 0.8, "gurugram": 0.8,
               "hyderabad": 0.7, "mumbai": 0.7, "bangalore": 0.6, "bengaluru": 0.6,
               "chennai": 0.5}

# --- Facet weights (consensus backbone) -------------------------------------
# NOTE: role_fit and evidence_fit are CONSENSUS-GATED in scoring (a min-style gate),
# not simply summed — a big skill_trust cannot rescue a wrong title.
WEIGHTS = {
    "role_fit":       0.30,
    "evidence_fit":   0.34,
    "skill_trust":    0.12,
    "experience_fit": 0.14,
    "trajectory_fit": 0.10,
}

# Ideal experience band from the JD ("5-9 years... ideal 6-8").
YOE_IDEAL = (6.0, 8.0)
YOE_OK = (5.0, 9.0)


def count_hits(text, phrases):
    """# of distinct phrases from `phrases` present in `text`."""
    return sum(1 for p in phrases if p in text)


def title_class(title):
    t = (title or "").lower()
    if any(k in t for k in STRONG_TITLE):
        return "strong"
    if any(k in t for k in NONTECH_TITLE):
        return "nontech"
    if any(k in t for k in MED_TITLE):
        return "med"
    return "other"
