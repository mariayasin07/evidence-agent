import datetime
import math

from utils.text import domain_of

TOP = ("nih.gov", "who.int", "nature.com", "science.org", "thelancet.com", "bmj.com", "nejm.org", "jamanetwork.com",
       "cochrane.org", "plos.org", "oecd.org", "worldbank.org", "nber.org", "cdc.gov", "springer.com", "sciencedirect.com",
       "wiley.com", "tandfonline.com", "sagepub.com", "cell.com", "pnas.org", "arxiv.org", "nasa.gov", "un.org", "europa.eu")
NEWS = ("reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "nytimes.com", "economist.com", "ft.com", "theguardian.com")
LOW = ("pinterest.", "quora.", "reddit.", "facebook.", "twitter.", "tiktok.", "instagram.", "medium.com", "blogspot.",
       "wordpress.", "youtube.", "youtu.be", "linkedin.", "substack.")
INST = (".gov", ".edu", ".ac.uk", ".gov.uk", ".int", ".edu.au", ".gov.au")
SCHOLARLY = ("article", "review", "journal-article", "book-chapter", "proceedings-article", "book", "monograph")
PREPRINT = ("preprint", "posted-content")


def _match(d, hosts):
    return any(d == h or d.endswith("." + h) for h in hosts)


def score_source(s, prefer_scholarly=True):
    d = domain_of(s.url)
    score, tier = 30, "General web"
    if s.collection.startswith(("Scholarly", "Publication")):
        score += 25 if s.collection.startswith("Scholarly") else 20
        tier = "Scholarly publication"
        if s.kind in SCHOLARLY:
            score += 10
        elif s.kind in PREPRINT:
            score -= 8
            tier = "Preprint (not peer-reviewed)"
        if prefer_scholarly:
            score += 8
    else:
        if d.endswith(INST) or _match(d, TOP):
            score += 25
            tier = "Institution / major publisher"
        elif _match(d, NEWS):
            score += 12
            tier = "News outlet"
        elif d.endswith("wikipedia.org"):
            score += 5
            tier = "Encyclopedia (background only)"
        elif d == "x.com" or any(l in d for l in LOW):
            score -= 25
            tier = "Low-trust web"
    score += min(15, int(math.log10(1 + (s.cited_by or 0)) * 7))
    if s.year and s.year >= datetime.date.today().year - 5:
        score += 5
    if len(s.snippet) > 300:
        score += 5
    return max(0, min(100, score)), tier


def evaluate(sources, depth, cfg, emit):
    cap = int(cfg["max_sources_deep"] if depth == "Deep Dive" else cfg["max_sources_standard"])
    kept, no_text, low = [], 0, 0
    for s in sources:
        s.score, s.tier = score_source(s, cfg.get("prefer_scholarly", True))
        if len(s.snippet) < 60:
            no_text += 1
        elif s.score < cfg.get("min_score", 25):
            low += 1
        else:
            kept.append(s)
    kept.sort(key=lambda x: -x.score)
    over = max(0, len(kept) - cap)
    kept = kept[:cap]
    for i, s in enumerate(kept, 1):
        s.id = i
    st = {"unique": len(sources), "kept": len(kept), "no_text": no_text, "low_score": low, "over_cap": over}
    emit(msg=f"Scored {len(sources)} sources: kept {len(kept)} (dropped {no_text} without readable text, {low} below credibility threshold, {over} beyond the cap)",
         counts={"kept": len(kept)})
    if not kept:
        raise RuntimeError("No usable sources with readable text were found for this topic. Try rephrasing or lowering the minimum credibility score in Settings.")
    return kept, st
