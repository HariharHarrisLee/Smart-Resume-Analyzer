# job_matcher.py
import re
import spacy
from collections import Counter

# load once
try:
    _nlp = spacy.load("en_core_web_sm")
except Exception as e:
    # will error if model not downloaded
    raise RuntimeError("spaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm") from e

def extract_keywords(text: str, top_n: int = 40) -> list:
    """
    Extract candidate keywords / phrases from the job description.
    Returns a list of phrase strings (lowercased).
    """
    if not text:
        return []
    doc = _nlp(text.lower())
    candidates = []
    for nc in doc.noun_chunks:
        phrase = nc.text.strip()
        if len(phrase) > 2:
            candidates.append(phrase)
    for ent in doc.ents:
        candidates.append(ent.text.strip())
    for token in doc:
        if token.is_alpha and not token.is_stop and token.pos_ in ("NOUN", "PROPN", "ADJ"):
            if len(token.text) > 2:
                candidates.append(token.lemma_.strip())
    cleaned = [re.sub(r"[^a-z0-9\-\s\+]", "", c).strip() for c in candidates]
    cleaned = [c for c in cleaned if c and not c.isnumeric()]
    counts = Counter(cleaned)
    top = [p for p,_ in counts.most_common(top_n)]
    seen = set(); result = []
    for p in top:
        if p not in seen:
            seen.add(p); result.append(p)
    return result

def match_score(resume_text: str, job_keywords: list) -> dict:
    """
    Calculate a simple match score based on substring presence of keywords.
    Returns {'score': int, 'matched': [...], 'missing': [...]}
    """
    resume_low = (resume_text or "").lower()
    job_keywords = [k.lower().strip() for k in job_keywords if k and len(k.strip())>0]
    if not job_keywords:
        return {"score": 0, "matched": [], "missing": []}
    matched = []
    missing = []
    for k in job_keywords:
        # check whole words - crude but better than substring alone
        pattern = r"\b" + re.escape(k) + r"\b"
        if re.search(pattern, resume_low):
            matched.append(k)
        else:
            missing.append(k)
    score = int(100 * len(matched) / max(1, len(job_keywords)))
    return {"score": score, "matched": matched, "missing": missing}
