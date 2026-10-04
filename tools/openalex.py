import requests

from models.schemas import Source
from utils.config import contact_email


def _abstract(inv):
    if not inv:
        return ""
    pos = {}
    for w, idxs in inv.items():
        for i in idxs:
            pos[i] = w
    return " ".join(pos[i] for i in sorted(pos))


def search(query, n=6, timeout=20):
    params = {
        "search": query,
        "per-page": n,
        "filter": "has_abstract:true",
        "select": "id,doi,title,publication_year,cited_by_count,abstract_inverted_index,primary_location,authorships,type",
    }
    if contact_email():
        params["mailto"] = contact_email()
    r = requests.get("https://api.openalex.org/works", params=params, timeout=timeout)
    r.raise_for_status()
    out = []
    for it in r.json().get("results", []):
        doi = (it.get("doi") or "").replace("https://doi.org/", "")
        names = [a.get("author", {}).get("display_name", "") for a in it.get("authorships", [])[:3]]
        authors = ", ".join(x for x in names if x) + (" et al." if len(it.get("authorships", [])) > 3 else "")
        venue = ((it.get("primary_location") or {}).get("source") or {}).get("display_name", "") or ""
        out.append(
            Source(
                title=it.get("title") or "",
                url=(f"https://doi.org/{doi}" if doi else it.get("id", "")),
                snippet=_abstract(it.get("abstract_inverted_index")),
                year=it.get("publication_year"),
                authors=authors,
                venue=venue,
                doi=doi,
                cited_by=it.get("cited_by_count") or 0,
                kind=it.get("type") or "article",
            )
        )
    return out
