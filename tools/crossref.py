import requests

from models.schemas import Source
from utils.config import contact_email
from utils.text import strip_tags


def search(query, n=6, timeout=20):
    params = {
        "query": query,
        "rows": n,
        "filter": "has-abstract:true",
        "select": "DOI,title,abstract,author,issued,container-title,URL,is-referenced-by-count,type",
    }
    if contact_email():
        params["mailto"] = contact_email()
    r = requests.get("https://api.crossref.org/works", params=params, timeout=timeout)
    r.raise_for_status()
    out = []
    for it in r.json().get("message", {}).get("items", []):
        authors = [a.get("family", "") for a in it.get("author", [])[:3] if a.get("family")]
        authors_s = ", ".join(authors) + (" et al." if len(it.get("author", [])) > 3 else "")
        try:
            year = it["issued"]["date-parts"][0][0]
        except Exception:
            year = None
        doi = it.get("DOI", "")
        out.append(
            Source(
                title=(it.get("title") or [""])[0],
                url=(f"https://doi.org/{doi}" if doi else it.get("URL", "")),
                snippet=strip_tags(it.get("abstract", "")),
                year=year,
                authors=authors_s,
                venue=(it.get("container-title") or [""])[0],
                doi=doi,
                cited_by=it.get("is-referenced-by-count") or 0,
                kind=it.get("type") or "journal-article",
            )
        )
    return out
