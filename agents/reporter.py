from utils.text import extract_json

SYSTEM = ("You write concise, neutral research prose. Use ONLY the findings provided. Do not add facts, numbers or sources. "
          "Be explicit about uncertainty and never imply causation unless a finding is marked causal.")


def build_report(llm, topic, depth, findings, conflicts, sources, plan, stats, emit):
    by_id = {s.id: s for s in sources}
    order = []
    for f in findings:
        for sid in [f.source_id] + f.corroborating:
            if sid not in order:
                order.append(sid)
    newn = {sid: i + 1 for i, sid in enumerate(order)}
    refs = [{"n": newn[sid], "title": by_id[sid].title or "(untitled)", "url": by_id[sid].link(), "authors": by_id[sid].authors,
             "year": by_id[sid].year, "venue": by_id[sid].venue, "doi": by_id[sid].doi, "tier": by_id[sid].tier,
             "score": by_id[sid].score, "collection": by_id[sid].collection} for sid in order]

    rep_f = []
    for f in findings:
        rep_f.append({"n": f.n, "claim": f.claim, "evidence": f.evidence, "source_n": newn[f.source_id],
                      "support_ns": [newn[i] for i in f.corroborating], "status": f.status, "detail": f.detail,
                      "evidence_type": f.evidence_type, "certainty": f.certainty, "confidence": f.confidence,
                      "caveat": f.caveat, "statistic": f.statistic})
    fmap = {f["n"]: f for f in rep_f}
    persp = [{"topic": c["topic"], "explanation": c["explanation"],
              "positions": [{"n": i, "claim": fmap[i]["claim"], "cites": [fmap[i]["source_n"]] + fmap[i]["support_ns"]} for i in c["finding_ids"]]}
             for c in conflicts]
    stat = [{"n": f["n"], "value": f["statistic"], "context": f["claim"], "cites": [f["source_n"]], "status": f["status"]}
            for f in rep_f if f["statistic"]]

    intro = conclusion = ""
    if rep_f:
        block = "\n".join(f"F{f['n']} ({f['status']}, {f['evidence_type']}, confidence {f['confidence']}): {f['claim']}" for f in rep_f)
        cblock = "\n".join(f"- {c['topic']}: {c['explanation']}" for c in conflicts) or "none"
        prompt = (f"Topic: {topic}\n\nVERIFIED FINDINGS:\n{block}\n\nDISAGREEMENTS:\n{cblock}\n\n"
                  'Return JSON: {"introduction":"2-4 sentences framing the topic and scope (no new facts)",'
                  '"conclusion":"3-5 sentences summarising what the evidence supports, where it is uncertain or only correlational, and what is unknown"}')
        try:
            d = extract_json(llm.chat(SYSTEM, prompt, json_mode=True, max_tokens=400, timeout=30))
            intro, conclusion = str(d.get("introduction", "")).strip(), str(d.get("conclusion", "")).strip()
        except Exception as e:
            emit(msg=f"Writer model failed ({str(e)[:80]}); using standard framing text")
    if not intro:
        intro = f"This report examines the evidence available for: {topic}. It draws only on sources retrieved from the open web and scholarly databases during this session."
    if not conclusion:
        conclusion = ("The findings above are limited to claims whose supporting quotes were found in retrieved source text. "
                      "Review the verification status and caveats of each finding before relying on it." if rep_f
                      else "No claims passed verification, so no conclusions can be drawn from this search. Try a more specific topic or a Deep Dive.")

    how = {
        "queries": {"web": plan["web_queries"], "scholarly": plan["scholarly_queries"], "subquestions": plan["subquestions"]},
        "search": stats["search"], "evaluation": stats["eval"], "verification": stats["verify"],
        "conflicts_checked": stats["conflicts_checked"], "conflicts_found": len(conflicts),
        "limitations": [
            "Quotes are verified against the text each database or search engine returned (usually an abstract or snippet), not the full paper.",
            "Results reflect what DuckDuckGo, OpenAlex and Crossref returned at the time of the search and may omit relevant work.",
            "Credibility scores are heuristic (source type, domain, citations, recency) and are not a substitute for expert review.",
            "Correlational findings do not establish causation.",
        ],
    }
    emit(msg=f"Report assembled: {len(rep_f)} findings, {len(refs)} references")
    return {"introduction": intro, "findings": rep_f, "perspectives": persp, "statistics": stat, "how": how,
            "conclusion": conclusion, "references": refs}
