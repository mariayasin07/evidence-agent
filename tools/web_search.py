from models.schemas import Source


def search(query, n=6, timeout=20):
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS
    results = DDGS(timeout=timeout).text(query, max_results=n) or []
    out = []
    for r in results:
        url = r.get("href") or r.get("url") or ""
        if not url:
            continue
        out.append(Source(title=r.get("title", ""), url=url, snippet=(r.get("body") or "").strip(), kind="web"))
    return out
