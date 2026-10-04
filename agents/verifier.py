import math
import re
import time

from models.schemas import Finding
from utils.text import content_tokens, extract_json, jaccard, norm, quote_match

SYSTEM = "You rewrite a source sentence as a short neutral claim. Use only the sentence given. Never add facts or numbers."

_SPLIT = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9"\u201c(\[])')
_STAT = re.compile(r"\b\d+(?:\.\d+)?\s?(?:%|percent|per cent)|\b\d+(?:\.\d+)?\s?(?:-|\u2013)?\s?(?:fold|times|mg|kg|participants|patients|people|adults|children|employees|workers)\b|\b(?:p|OR|HR|RR|CI)\s?[<=>]\s?\d", re.I)
# actual results / effects / comparisons / associations / conclusions
_RESULT = re.compile(
    r"\b(found|finding|findings|showed|shown|shows|demonstrat\w*|revealed|observed|reported|"
    r"associat\w*|correlat\w*|linked to|increas\w*|decreas\w*|reduc\w*|improv\w*|declin\w*|rose|fell|"
    r"higher|lower|greater|fewer|more likely|less likely|compared (?:with|to)|than|odds|hazard|risk of|"
    r"significant\w*|no (?:significant )?(?:effect|difference|association)|effect(?:s)? (?:of|on)|"
    r"led to|resulted in|concluded|conclude|outcomes? (?:were|was|improved|worsened))\b", re.I)
# purpose / definition / background / structure sentences -> never findings
_NOT_FINDING = re.compile(
    r"(\b(?:this|the present|the current|our) (?:study|paper|article|review|work|research|analysis|chapter|report|essay|thesis)\b"
    r".{0,40}\b(?:aims?|seeks?|examines?|explores?|investigates?|discusses|describes?|presents?|proposes?|reviews?|focus(?:es)?|analy[sz]es|addresses|introduces|outlines|provides an overview)\b"
    r"|\b(?:we|i) (?:aim|seek|examine|explore|investigate|discuss|describe|propose|review|present|introduce|outline)\b"
    r"|\b(?:aims?|objectives?|purpose) (?:of|is|are|was|were)\b|\bin this (?:paper|study|article|review|chapter)\b"
    r"|\brefers? to\b|\bis defined as\b|\bare defined as\b|\bis (?:a|an|the) (?:term|concept|practice|type|form)\b|\bdefinition of\b"
    r"|\bhas (?:become|gained|attracted|emerged)\b|\bin recent years\b|\bincreasing(?:ly)? (?:attention|interest|popular)\b"
    r"|\bfuture (?:research|studies|work)\b|\bmore research is needed\b|\bremains? (?:unclear|unknown)\b|\bbackground\b|\bintroduction\b"
    r"|\bthe rest of (?:this|the) (?:paper|article)\b|\bis organi[sz]ed\b|\?\s*$)", re.I)
_CAUSAL = re.compile(r"\b(randomi[sz]ed|caus(?:e|ed|es|ing)|led to|resulted in|trial|experiment\w*)\b", re.I)
_CORREL = re.compile(r"\b(associat\w*|correlat\w*|linked|observational|cohort|cross-sectional|relationship)\b", re.I)
_JUNK = re.compile(r"(copyright|all rights reserved|click here|subscribe|cookie|sign up|read more|\bpublished by\b)", re.I)


def _stems(text):
    return {w[:6] for w in content_tokens(text)}


def _sentences(src):
    out = []
    for x in _SPLIT.split(src.snippet[:1500].strip()):
        x = x.strip()
        if 40 <= len(x) <= 400 and len(x.split()) >= 7 and not _JUNK.search(x) and not _NOT_FINDING.search(x):
            out.append(x)
    return out


def _score(sent, tstems):
    """Relevance to the question + strength of result signal. Returns 0 if not a real finding."""
    stat, res = bool(_STAT.search(sent)), bool(_RESULT.search(sent))
    if not (stat or res):
        return 0.0
    ov = len(_stems(sent) & tstems)
    need = 1 if len(tstems) <= 3 else 2
    if ov < need:
        return 0.0
    return ov / max(1, len(tstems)) + (0.4 if res else 0) + (0.4 if stat else 0) + (0.1 if len(sent) > 90 else 0)


def _deterministic(topic, sources, per_source):
    ts = _stems(topic)
    cands = []
    for src in sources:
        scored = sorted(((_score(x, ts), x) for x in _sentences(src)), key=lambda t: -t[0])
        for sc, sent in scored[:per_source]:
            if sc <= 0:
                continue
            m = _STAT.search(sent)
            cands.append(Finding(
                claim=sent, evidence=sent, source_id=src.id, rank=round(sc, 3),
                evidence_type="causal" if _CAUSAL.search(sent) and not _CORREL.search(sent) else "correlational" if _CORREL.search(sent) else "descriptive",
                certainty="medium", statistic=m.group(0).strip() if m else ""))
    return cands


def _refine(llm, topic, cands, cfg, emit, budget):
    """Optional: LLM rewrites a few top sentences into short claims. Failures keep the verbatim sentence."""
    if not cfg.get("llm_refine", True) or not cands:
        return cands
    call_to = int(cfg.get("claim_call_timeout", 20))
    start, fails, done, skip = time.time(), 0, 0, set()
    for i in range(0, len(cands), 4):
        if fails >= 1 or time.time() - start > budget:
            emit(msg=f"Claim wording: stopped after {done}/{len(cands)} (kept original sentences for the rest)")
            break
        batch = cands[i : i + 4]
        lines = "\n".join(f"{j}: {c.evidence[:300]}" for j, c in enumerate(batch, 1))
        prompt = (f"Question: {topic}\n\nSentences:\n{lines}\n\nFor each number write one short neutral claim (max 30 words) that states the result "
                  'using only that sentence, or "SKIP" if it does not report a result relevant to the question. JSON: {"c":{"1":"...","2":"..."}}')
        try:
            res = extract_json(llm.chat(SYSTEM, prompt, json_mode=True, max_tokens=240, timeout=call_to)).get("c", {})
            for j, c in enumerate(batch, 1):
                v = str(res.get(str(j), "")).strip()
                if v.upper() == "SKIP":
                    skip.add(id(c))
                elif 15 <= len(v) <= 300 and jaccard(content_tokens(v), content_tokens(c.evidence)) >= 0.25:
                    c.claim = v
        except Exception as e:
            fails += 1
            emit(msg=f"Claim wording skipped ({str(e)[:60]}) — keeping original sentences")
        done += len(batch)
    kept = [c for c in cands if id(c) not in skip]
    return kept if len(kept) >= max(1, len(cands) // 2) else cands


def extract_candidates(llm, topic, sources, depth, cfg, emit):
    deep = depth == "Deep Dive"
    emit(msg=f"Extracting result-bearing sentences from {len(sources)} sources (definitions, aims and background are skipped)")
    cands = _deterministic(topic, sources, 3 if deep else 2)
    cands.sort(key=lambda c: -c.rank)
    cands = cands[: 24 if deep else 14]
    emit(msg=f"{len(cands)} candidate findings from {len({c.source_id for c in cands})} sources", counts={"candidates": len(cands)})
    n = 14 if deep else 4
    cands = _refine(llm, topic, cands[:n], cfg, emit, budget=60 if deep else 20) + cands[n:]
    emit(msg=f"{len(cands)} candidate findings ready for verification", counts={"candidates": len(cands)})
    return cands


def verify(cands, sources, depth, cfg, emit):
    by_id = {s.id: s for s in sources}
    thr = 0.9 if cfg.get("strict_quote_check", True) else 0.75
    stats = {"candidates": len(cands), "verified": 0, "partial": 0, "removed_unverified": 0, "removed_lowcred": 0, "duplicates": 0}
    good, seen = [], []
    for f in cands:
        src = by_id[f.source_id]
        if not quote_match(f.evidence, f"{src.title}. {src.snippet}", thr):
            stats["removed_unverified"] += 1
            continue
        ct = content_tokens(f.claim)
        if any(jaccard(ct, c) > 0.7 for c in seen):
            stats["duplicates"] += 1
            continue
        seen.append(ct)
        if f.statistic and not (any(ch.isdigit() for ch in f.statistic) and norm(f.statistic) in norm(f.evidence)):
            f.statistic = ""
        cs = set(ct)
        if len(cs) >= 4:
            for o in sources:
                if o.id != src.id and len(f.corroborating) < 3 and len(cs & set(content_tokens(o.title + " " + o.snippet))) / len(cs) >= 0.6:
                    f.corroborating.append(o.id)
        if not f.corroborating and cfg.get("require_corroboration", True) and src.score < 50:
            stats["removed_lowcred"] += 1
            continue
        multi = bool(f.corroborating)
        f.status = "Verified" if multi else "Partially verified"
        f.detail = (f"Quote found in source text and the claim is also supported by {len(f.corroborating)} other source(s)."
                    if multi else "Quote found in source text; no second source corroborated it. Treat with caution.")
        if f.certainty == "low" or src.score < 40:
            f.confidence = "Low"
        elif multi and src.score >= 60 and f.certainty != "low":
            f.confidence = "High"
        else:
            f.confidence = "Moderate"
        good.append(f)
    good.sort(key=lambda f: (f.status != "Verified", -(f.rank + by_id[f.source_id].score / 100)))
    good = good[: 14 if depth == "Deep Dive" else 8]
    for i, f in enumerate(good, 1):
        f.n = i
    stats["verified"] = sum(f.status == "Verified" for f in good)
    stats["partial"] = len(good) - stats["verified"]
    emit(msg=f"Verification: {stats['verified']} verified, {stats['partial']} partially verified, "
             f"{stats['removed_unverified']} removed (quote not found in source), {stats['removed_lowcred']} removed (single low-credibility source)",
         counts={"verified": len(good)})
    return good, stats
