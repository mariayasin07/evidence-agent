import time

import streamlit as st

from agents.orchestrator import STAGES, run_research
from services.export import to_docx, to_pdf
from services.llm import LLMProvider
from utils import history
from utils.config import PRESETS, env_api_key, load_settings, save_settings
from utils.text import esc_md
from utils.theme import css

st.set_page_config(page_title="Evidence Research Agent", page_icon="🔎", layout="wide")

ss = st.session_state
if "cfg" not in ss:
    ss.cfg = load_settings()
cfg = ss.cfg
ss.setdefault("page", "New Research")
ss.setdefault("api_key", env_api_key())
ss.setdefault("models", {})
ss.setdefault("current_id", None)
ss.setdefault("view_id", None)
ss.setdefault("export_id", None)
ss.setdefault("export_blob", None)
ss.setdefault("topic", "")
st.markdown(css(cfg["theme"]), unsafe_allow_html=True)

PAGES = ["New Research", "Research History", "Settings", "Export"]
EXAMPLES = [
    "Does intermittent fasting improve long-term health outcomes?",
    "How effective are four-day work weeks for productivity and wellbeing?",
    "What does research say about microplastics and human health?",
]


def S(fn, label, key, wkey=None, **kw):
    """Settings widget bound to cfg[key]; persists on change."""
    wk = wkey or "w_" + key
    if wk not in ss:
        ss[wk] = cfg[key]

    def cb():
        cfg[key] = ss[wk]
        save_settings(cfg)

    return fn(label, key=wk, on_change=cb, **kw)


def go(page, **kw):
    ss.page = page
    for k, v in kw.items():
        ss[k] = v


def make_llm():
    return LLMProvider(cfg, ss.api_key)


def cites(ns, refs):
    return " ".join(f"[\\[{n}\\]]({refs[n]['url']})" if refs.get(n, {}).get("url") else f"[{n}]" for n in ns)


# ------------------------------------------------------------------ report
def render_report(task):
    r = task["report"]
    refs = {x["n"]: x for x in r["references"]}
    st.markdown(f"## {esc_md(task['topic'])}")
    st.caption(f"{task['depth']} · {task['created']} · {task['model']} · {task.get('duration', '?')}s")
    st.markdown("### Introduction")
    st.markdown(esc_md(r["introduction"]))

    st.markdown("### Key Findings")
    if not r["findings"]:
        st.warning("No claims passed verification for this topic. See “How We Checked”.")
    for f in r["findings"]:
        with st.container(border=True):
            st.markdown(f"**{f['n']}. Claim —** {esc_md(f['claim'])} {cites([f['source_n']] + f['support_ns'], refs)}")
            st.markdown(f"**Evidence —** “{esc_md(f['evidence'])}”")
            src = refs.get(f["source_n"], {})
            title = esc_md(src.get("title", "")) or "source"
            link = f"[{title}]({src['url']})" if src.get("url") else title
            st.markdown(f"**Source —** {link} · {src.get('tier', '')} · credibility {src.get('score', '?')}/100")
            icon = "✅" if f["status"] == "Verified" else "🟡"
            st.markdown(f"**Verification —** {icon} {f['status']} · confidence {f['confidence']}. {esc_md(f['detail'])}")
            if f["evidence_type"] == "correlational":
                st.caption("⚠️ Correlational evidence — this does not establish causation.")
            elif f["evidence_type"] == "causal":
                st.caption("Source reports a causal/experimental result; check study design and sample in the source.")
            if f["caveat"]:
                st.caption("Caveat: " + esc_md(f["caveat"]))

    if r["perspectives"]:
        st.markdown("### Different Perspectives")
        for p in r["perspectives"]:
            with st.container(border=True):
                st.markdown(f"**{esc_md(p['topic'])}** — {esc_md(p['explanation'])}")
                for x in p["positions"]:
                    st.markdown(f"- F{x['n']}: {esc_md(x['claim'])} {cites(x['cites'], refs)}")

    if r["statistics"]:
        st.markdown("### Important Statistics")
        rows = "\n".join(f"| **{esc_md(x['value'])}** | {esc_md(x['context'])} | {cites(x['cites'], refs)} | {x['status']} |" for x in r["statistics"])
        st.markdown("| Value | Context | Source | Verification |\n|---|---|---|---|\n" + rows)

    if r["findings"]:
        st.markdown("### Evidence Map")
        rows = "\n".join(
            f"| {f['n']} | {esc_md(f['claim'])} | {cites([f['source_n']] + f['support_ns'], refs)} | "
            f"{'✅' if f['status'] == 'Verified' else '🟡'} {f['status']} | {f['confidence']} | {f['evidence_type']} |"
            for f in r["findings"])
        st.markdown("| # | Claim | Sources | Verification | Confidence | Evidence type |\n|---|---|---|---|---|---|\n" + rows)

    h = r["how"]
    s, e, v = h["search"], h["evaluation"], h["verification"]
    st.markdown("### How We Checked")
    st.markdown(
        f"- **Searches:** {s['completed']}/{s['searches']} completed ({s['failed']} failed) · {s['raw']} raw results → {s.get('unique', 0)} unique sources\n"
        f"- **Source evaluation:** {e['kept']} kept; {e['no_text']} dropped (no readable text), {e['low_score']} below credibility threshold\n"
        f"- **Claim verification:** {v['candidates']} candidates → {v['verified']} verified, {v['partial']} partially verified; "
        f"{v['removed_unverified']} removed (quote not found in source), {v['removed_lowcred']} removed (single low-credibility source)\n"
        f"- **Conflict check:** {'run — ' + str(h['conflicts_found']) + ' genuine disagreement(s)' if h['conflicts_checked'] else 'not run'}")
    with st.expander("Queries used and limitations"):
        st.markdown("**Web:** " + "; ".join(esc_md(q) for q in h["queries"]["web"]))
        st.markdown("**Scholarly:** " + "; ".join(esc_md(q) for q in h["queries"]["scholarly"]))
        for x in h["limitations"]:
            st.markdown("- " + x)
    if task.get("log"):
        with st.expander("Process log"):
            st.code("\n".join(task["log"]), language=None)

    st.markdown("### Conclusion")
    st.markdown(esc_md(r["conclusion"]))
    st.markdown("### References")
    for x in r["references"]:
        meta = ". ".join(p for p in [x.get("authors"), f"({x['year']})" if x.get("year") else "", x.get("venue")] if p)
        t = esc_md(x["title"])
        st.markdown(f"**[{x['n']}]** {meta + '. ' if meta else ''}{'[' + t + '](' + x['url'] + ')' if x['url'] else t} · _{x['tier']}_")
    st.button("Export this report", key=f"exp_{task['id']}", on_click=go, args=("Export",), kwargs={"export_id": task["id"]})


# ------------------------------------------------------------------ new research
def run_ui(topic, depth):
    state = {"stages": {s: "pending" for s in STAGES}, "msg": "Starting…", "active": [], "counts": {}, "log": []}
    box = st.container(border=True)
    with box:
        st.markdown("#### Research in progress")
        stage_ph, act_ph, cnt_ph = st.empty(), st.empty(), st.empty()
        with st.expander("Live activity log", expanded=True):
            log_ph = st.empty()

    def draw():
        chips = ""
        for s in STAGES:
            k = state["stages"][s]
            icon = {"done": "✅", "running": "⏳", "pending": "○"}[k]
            chips += f"<span class='chip {'run' if k == 'running' else 'done' if k == 'done' else ''}'>{icon} {s}</span>"
        running = [s for s in STAGES if state["stages"][s] == "running"]
        nxt = [s for s in STAGES if state["stages"][s] == "pending"]
        stage_ph.markdown(chips + f"<br><small>Current: <b>{running[0] if running else 'finishing'}</b> · Next: <b>{nxt[0] if nxt else 'none'}</b></small>",
                          unsafe_allow_html=True)
        lines = [f"**Now:** {esc_md(state['msg'])}"] + [f"- 🔎 {esc_md(a)}" for a in state["active"][:8]]
        act_ph.markdown("\n".join(lines))
        c = state["counts"]
        with cnt_ph.container():
            cols = st.columns(6)
            vals = [("Searches", f"{c.get('searches_done', 0)}/{c.get('searches_total', 0)}"), ("Raw results", c.get("raw", 0)),
                    ("Unique sources", c.get("unique", 0)), ("Sources kept", c.get("kept", 0)),
                    ("Claims checked", c.get("candidates", 0)), ("Findings", c.get("verified", 0))]
            for col, (k, v) in zip(cols, vals):
                col.metric(k, v)
        log_ph.markdown("\n".join(f"- {esc_md(x)}" for x in state["log"][-10:]))

    t0 = time.time()

    def on_event(ev):
        if "stage" in ev:
            state["stages"][ev["stage"]] = ev.get("stage_state", "running")
        if ev.get("msg"):
            state["msg"] = ev["msg"]
            state["log"].append(f"{time.time() - t0:4.1f}s — {ev['msg']}")
        if "active" in ev:
            state["active"] = ev["active"]
        if "counts" in ev:
            state["counts"].update(ev["counts"])
        draw()

    draw()
    return box, on_event


def page_new():
    st.markdown("<div class='hero'><h1>Evidence Research</h1><p>Ask about any topic. The agent plans, searches, evaluates, verifies and reports — with every claim tied to a checked source.</p></div>",
                unsafe_allow_html=True)
    st.text_area("Research topic or question", key="topic", height=100, placeholder="Enter any topic or question you want researched…")
    c1, c2 = st.columns([3, 1])
    with c1:
        S(st.radio, "Research depth", "depth", options=["Standard", "Deep Dive"], horizontal=True)
    with c2:
        st.write("")
        start = st.button("Start research", type="primary", use_container_width=True)
    st.caption("Try an example (it only fills the box — you can research anything):")
    cols = st.columns(3)
    for i, ex in enumerate(EXAMPLES):
        cols[i].button(ex, key=f"ex{i}", on_click=lambda e=ex: ss.__setitem__("topic", e), use_container_width=True)
    st.caption(f"Model: {make_llm().label}")

    ran = None
    if start:
        topic = (ss.topic or "").strip()
        llm = make_llm()
        ok, msg = llm.ready()
        if not topic:
            st.warning("Enter a topic first.")
        elif not ok:
            st.error(msg)
        else:
            box, on_event = run_ui(topic, cfg["depth"])
            try:
                ran = run_research(topic, cfg["depth"], cfg, llm, on_event)
                ss.current_id = ran["id"]
                box.empty()
            except Exception as e:
                st.error(f"Research stopped: {e}")
    if ran:
        render_report(ran)
    elif ss.current_id:
        t = history.load(ss.current_id)
        if t:
            st.divider()
            st.caption("Latest research")
            render_report(t)


# ------------------------------------------------------------------ history
def page_history():
    st.markdown("## Research History")
    if ss.view_id:
        t = history.load(ss.view_id)
        st.button("← Back to history", on_click=lambda: ss.__setitem__("view_id", None))
        if t:
            render_report(t)
        return
    items = history.list_tasks()
    if not items:
        st.info("No research yet. Start one from New Research.")
    for it in items:
        with st.container(border=True):
            a, b, c = st.columns([7, 1.3, 1.3])
            a.markdown(f"**{esc_md(it['topic'])}**")
            a.caption(f"{it['created']} · {it['depth']} · {it['findings']} findings · {it['sources']} references · {it['model']}")
            b.button("Open", key=f"o{it['id']}", on_click=lambda i=it["id"]: ss.__setitem__("view_id", i), use_container_width=True)
            c.button("Delete", key=f"d{it['id']}", on_click=lambda i=it["id"]: history.delete(i), use_container_width=True)


# ------------------------------------------------------------------ settings
def model_picker(key, cfg_key):
    models = ss.models.get(key, [])
    cur = cfg[cfg_key]
    if models:
        if cur not in models:
            cfg[cfg_key] = cur = models[0]
            ss.pop("w_" + cfg_key, None)
            save_settings(cfg)
        S(st.selectbox, "Model", cfg_key, options=models)
    else:
        S(st.text_input, "Model name", cfg_key, wkey="w_" + cfg_key + "_txt", help="Click “Check connection / refresh models” to discover models.")


def page_settings():
    st.markdown("## Settings")
    t1, t2, t3, t4, t5 = st.tabs(["Appearance", "AI / Model", "Research", "Trust & verification", "Export"])
    with t1:
        S(st.radio, "Theme", "theme", options=["Light", "Dark"], horizontal=True)
        st.caption("Dark mode uses a near-black theme.")
    with t2:
        S(st.radio, "Provider", "provider", options=["Ollama", "Cloud API"], horizontal=True)
        if cfg["provider"] == "Ollama":
            S(st.text_input, "Ollama host URL", "ollama_host")
            key = f"ollama|{cfg['ollama_host']}"
            if st.button("Check connection / refresh models"):
                ok, msg, models = make_llm().check()
                (st.success if ok else st.error)(msg)
                ss.models[key] = models
                st.rerun() if ok and models else None
            model_picker(key, "ollama_model")
        else:
            S(st.selectbox, "Cloud provider", "cloud_provider", options=list(PRESETS))
            if cfg["cloud_provider"].startswith("Custom"):
                S(st.text_input, "Base URL (OpenAI-compatible)", "cloud_base_url", placeholder="https://host/v1")
            else:
                st.caption(f"Base URL: {PRESETS[cfg['cloud_provider']]}")
            st.text_input("API key", type="password", key="api_key_w", value=ss.api_key,
                          on_change=lambda: ss.__setitem__("api_key", ss.api_key_w),
                          help="Kept in this browser session only (or set LLM_API_KEY in .env). Never written to settings.")
            key = f"cloud|{cfg['cloud_provider']}|{cfg['cloud_base_url']}"
            if st.button("Check connection / refresh models"):
                ok, msg, models = make_llm().check()
                (st.success if ok else st.error)(msg)
                ss.models[key] = models
                st.rerun() if ok and models else None
            model_picker(key, "cloud_model")
        ok, msg = make_llm().ready()
        st.caption("✅ Ready" if ok else f"⚠️ {msg}")
    with t3:
        S(st.radio, "Default research depth", "depth", wkey="w_depth_settings", options=["Standard", "Deep Dive"], horizontal=True)
        S(st.slider, "Max sources analysed — Standard", "max_sources_standard", min_value=6, max_value=14)
        S(st.slider, "Max sources analysed — Deep Dive", "max_sources_deep", min_value=12, max_value=30)
        S(st.slider, "Model call timeout (seconds)", "llm_timeout", min_value=30, max_value=300, step=10)
        S(st.slider, "Search timeout (seconds)", "search_timeout", min_value=5, max_value=60, step=5)
    with t4:
        S(st.slider, "Minimum source credibility score", "min_score", min_value=0, max_value=80)
        S(st.toggle, "Prefer scholarly sources", "prefer_scholarly")
        S(st.toggle, "Drop single-source findings from low-credibility sources", "require_corroboration")
        S(st.toggle, "Strict quote matching (≥90% of the quote must appear in the source)", "strict_quote_check")
    with t5:
        S(st.radio, "Default format", "export_format", wkey="w_export_format_settings", options=["PDF", "DOCX"], horizontal=True)
        S(st.toggle, "Include Evidence Map", "export_map", wkey="w_export_map_s")
        S(st.toggle, "Include evidence quotes", "export_evidence", wkey="w_export_evidence_s")
        S(st.toggle, "Include process log", "export_log", wkey="w_export_log_s")


# ------------------------------------------------------------------ export
def page_export():
    st.markdown("## Export")
    items = history.list_tasks()
    if not items:
        st.info("Nothing to export yet.")
        return
    ids = [i["id"] for i in items]
    labels = {i["id"]: f"{i['created']} — {i['topic'][:80]}" for i in items}
    pref = ss.export_id or ss.current_id
    sel = st.selectbox("Research task", ids, index=ids.index(pref) if pref in ids else 0, format_func=lambda i: labels[i])
    S(st.radio, "Format", "export_format", options=["PDF", "DOCX"], horizontal=True)
    c = st.columns(3)
    with c[0]:
        S(st.toggle, "Evidence Map", "export_map")
    with c[1]:
        S(st.toggle, "Evidence quotes", "export_evidence")
    with c[2]:
        S(st.toggle, "Process log", "export_log")
    if st.button("Generate file", type="primary"):
        task = history.load(sel)
        try:
            fmt = cfg["export_format"]
            data = to_pdf(task, cfg) if fmt == "PDF" else to_docx(task, cfg)
            mime = "application/pdf" if fmt == "PDF" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ss.export_blob = (f"research-{sel}.{fmt.lower()}", data, mime)
        except Exception as e:
            st.error(f"Export failed: {e}")
    if ss.export_blob:
        name, data, mime = ss.export_blob
        st.download_button(f"Download {name}", data, file_name=name, mime=mime)
        st.caption("A copy is also saved in the exports/ folder.")


# ------------------------------------------------------------------ shell
with st.sidebar:
    st.markdown("### 🔎 Evidence Research")
    st.radio("Navigate", PAGES, key="page", label_visibility="collapsed")
    st.caption(make_llm().label)

{"New Research": page_new, "Research History": page_history, "Settings": page_settings, "Export": page_export}[ss.page]()
