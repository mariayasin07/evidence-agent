from utils.text import extract_json

SYSTEM = "You are a research planner for an evidence-based research tool. You plan searches; you do not answer the topic."


def _clean(lst, n):
    out = []
    for x in lst if isinstance(lst, list) else []:
        x = str(x).strip()
        if x and x.lower() not in [o.lower() for o in out]:
            out.append(x)
    return out[:n]


def plan_research(llm, topic, depth, emit):
    n = 5 if depth == "Deep Dive" else 3
    prompt = (
        f"Topic: {topic}\n\nPlan searches for an evidence-based report on exactly this topic. Return JSON:\n"
        f'{{"subquestions": [up to {n + 1} specific questions the report should answer],'
        f' "web_queries": [{n} concise web search queries],'
        f' "scholarly_queries": [{n} concise keyword queries for academic databases]}}\n'
        "Stay strictly on the user's topic. Do not state any facts."
    )
    source = "model"
    try:
        data = extract_json(llm.chat(SYSTEM, prompt, json_mode=True, max_tokens=400, timeout=45))
        sub = _clean(data.get("subquestions"), n + 1)
        web = _clean(data.get("web_queries"), n)
        sch = _clean(data.get("scholarly_queries"), n)
        if not web or not sch:
            raise ValueError("incomplete plan")
    except Exception as e:
        emit(msg=f"Planner model output unusable ({str(e)[:80]}); using topic-based queries.")
        source, sub = "fallback", []
        web = [topic, f"{topic} evidence", f"{topic} research findings", f"{topic} criticism limitations", f"{topic} statistics"][:n]
        sch = [topic, f"{topic} systematic review", f"{topic} meta-analysis", f"{topic} randomized OR longitudinal study", f"{topic} effects"][:n]
    emit(msg=f"Plan ready: {len(web)} web queries, {len(sch)} scholarly queries" + (f", {len(sub)} sub-questions" if sub else ""))
    return {"topic": topic, "subquestions": sub, "web_queries": web, "scholarly_queries": sch, "source": source}
