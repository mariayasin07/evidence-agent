import re

from utils.text import content_tokens

UP = {"increase", "increased", "increases", "increasing", "higher", "improve", "improved", "improves", "improvement", "greater",
      "gain", "gains", "raise", "raised", "boost", "boosted", "enhance", "enhanced", "benefit", "beneficial", "positive", "effective"}
DOWN = {"decrease", "decreased", "decreases", "reduce", "reduced", "reduces", "reduction", "lower", "declined", "decline", "fewer",
        "drop", "dropped", "worse", "negative", "harmful", "ineffective", "worsened"}
NULL = re.compile(r"\b(no (?:statistically |clinically )?(?:significant |clear |measurable )?(?:effect|difference|association|relationship|improvement|change|benefit)"
                  r"|not (?:significantly )?(?:associated|related|different|effective)|did not|failed to|no evidence)\b", re.I)
LABEL = {"up": "an increase/benefit", "down": "a decrease/harm", "null": "no clear effect"}


def _polarity(text):
    if NULL.search(text):
        return "null"
    toks = set(re.findall(r"[a-z]+", text.lower()))
    u, d = bool(toks & UP), bool(toks & DOWN)
    return "up" if u and not d else "down" if d and not u else None


def _subject(text):
    return {w for w in content_tokens(text) if w not in UP and w not in DOWN}


def detect(llm, topic, findings, emit):
    """Rule-based comparison (no model call): same subject + opposing direction from different sources."""
    if len(findings) < 2:
        emit(msg="Conflict check skipped: fewer than 2 findings")
        return [], False
    info = {f.n: (_polarity(f.claim + " " + f.evidence), _subject(f.claim + " " + f.evidence), f.source_id) for f in findings}
    out = []
    ns = sorted(info)
    for i, a in enumerate(ns):
        for b in ns[i + 1 :]:
            (pa, sa, src_a), (pb, sb, src_b) = info[a], info[b]
            if src_a == src_b or not pa or not pb or pa == pb:
                continue
            shared = sa & sb
            if len(shared) < 3 or len(shared) / len(sa | sb) < 0.25:
                continue
            out.append({"topic": "Different results on: " + ", ".join(sorted(shared, key=len, reverse=True)[:3]),
                        "explanation": (f"F{a} points to {LABEL[pa]} while F{b} points to {LABEL[pb]} on overlapping subject matter. "
                                        "Differences may come from study population, design, measurement or definitions; compare the cited sources before drawing a conclusion."),
                        "finding_ids": [a, b]})
    out = out[:3]
    emit(msg=f"Conflict check (rule-based, {len(findings)} findings compared): {len(out)} genuine disagreement(s) found", counts={"conflicts": len(out)})
    return out, True
