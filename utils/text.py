import html
import json
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse

STOP = set(
    "the a an and or of to in on for with is are was were be been by as at from that this it its their than then "
    "into over under between among can may might will would could should not no more most less other such these "
    "those which who whom whose while also has have had do does did about after before during".split()
)


def extract_json(text):
    if not text:
        raise ValueError("empty model response")
    t = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(t)
    except Exception:
        pass
    s, e = t.find("{"), t.rfind("}")
    if s != -1 and e > s:
        return json.loads(t[s : e + 1])
    raise ValueError("no JSON object found in model response")


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9%.]", " ", (s or "").lower())).strip()


def tokens(s):
    return [w.strip(".") for w in norm(s).split() if w.strip(".")]


def content_tokens(s):
    return [w for w in tokens(s) if len(w) > 3 and w not in STOP]


def quote_match(quote, text, thr=0.75):
    qt, tt = tokens(quote), tokens(text)
    if len(qt) < 4 or not tt:
        return False
    m = SequenceMatcher(None, qt, tt, autojunk=False).find_longest_match(0, len(qt), 0, len(tt))
    return m.size / len(qt) >= thr


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a and b else 0.0


def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def domain_of(url):
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def esc_md(s):
    return (s or "").replace("$", "\\$").replace("|", "\\|").replace("\n", " ")
