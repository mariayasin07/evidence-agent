from concurrent.futures import ThreadPoolExecutor, TimeoutError as FTimeout, as_completed

from tools import COLLECTIONS


def _key(s):
    return (s.doi or s.url or s.title).lower().strip().rstrip("/")


def research(plan, depth, cfg, emit):
    deep = depth == "Deep Dive"
    nweb, nsch, ncr, per = (5, 5, 3, 8) if deep else (3, 3, 2, 6)
    jobs = [("web", q) for q in plan["web_queries"][:nweb]]
    jobs += [("openalex", q) for q in plan["scholarly_queries"][:nsch]]
    jobs += [("crossref", q) for q in plan["scholarly_queries"][:ncr]]
    timeout = int(cfg.get("search_timeout", 20))
    total = len(jobs)
    active = [f"{COLLECTIONS[c][0]}: {q}" for c, q in jobs]
    stats = {"searches": total, "completed": 0, "failed": 0, "raw": 0, "by_collection": {}, "errors": []}
    emit(msg=f"Running {total} searches in parallel across 3 source collections", active=list(active),
         counts={"searches_done": 0, "searches_total": total, "raw": 0})
    found, ex = [], ThreadPoolExecutor(max_workers=6)
    futs = {ex.submit(COLLECTIONS[c][1], q, per, timeout): (c, q) for c, q in jobs}
    pending = set(futs)
    try:
        for f in as_completed(futs, timeout=timeout * 2 + 10):
            pending.discard(f)
            c, q = futs[f]
            label = COLLECTIONS[c][0]
            active.remove(f"{label}: {q}")
            stats["completed"] += 1
            try:
                res = f.result()
                for s in res:
                    s.collection, s.query = label, q
                found.extend(res)
                stats["raw"] += len(res)
                stats["by_collection"][label] = stats["by_collection"].get(label, 0) + len(res)
                msg = f"{label} · “{q}” → {len(res)} results"
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(f"{label}: {str(e)[:100]}")
                msg = f"{label} · “{q}” failed ({str(e)[:70]}) — continuing"
            emit(msg=msg, active=list(active),
                 counts={"searches_done": stats["completed"], "searches_total": total, "raw": stats["raw"]})
    except FTimeout:
        for f in pending:
            stats["failed"] += 1
            stats["errors"].append("search timed out")
        emit(msg=f"{len(pending)} search(es) timed out — continuing with what was found", active=[])
    finally:
        ex.shutdown(wait=False, cancel_futures=True)
    if stats["raw"] == 0:
        raise RuntimeError("All searches failed or returned nothing. Check your internet connection and try again. " + "; ".join(stats["errors"][:3]))

    merged = {}
    for s in found:
        k = _key(s)
        if not k:
            continue
        if k not in merged or len(s.snippet) > len(merged[k].snippet):
            merged[k] = s
    sources = list(merged.values())
    emit(msg=f"{stats['raw']} raw results → {len(sources)} unique sources after de-duplication", counts={"unique": len(sources)})
    stats["unique"] = len(sources)
    return sources, stats
