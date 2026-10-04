import datetime
import time

from agents.conflicts import detect
from agents.evaluator import evaluate
from agents.planner import plan_research
from agents.reporter import build_report
from agents.researcher import research
from agents.verifier import extract_candidates, verify
from utils import history

STAGES = ["Planning", "Searching", "Evaluating", "Verifying", "Conflict checking", "Writing"]


def run_research(topic, depth, cfg, llm, on_event):
    t0 = time.time()
    log = []

    def emit(**kw):
        if kw.get("msg"):
            log.append(f"[{time.time() - t0:5.1f}s] {kw['msg']}")
        on_event(kw)

    def stage(name, msg):
        emit(stage=name, stage_state="running", msg=msg, active=[])

    def done(name):
        emit(stage=name, stage_state="done")

    stage("Planning", "Planning: breaking the topic into searchable questions")
    plan = plan_research(llm, topic, depth, emit)
    done("Planning")

    stage("Searching", "Searching DuckDuckGo, OpenAlex and Crossref")
    sources, sstats = research(plan, depth, cfg, emit)
    done("Searching")

    stage("Evaluating", "Evaluating source credibility and readable text")
    kept, estats = evaluate(sources, depth, cfg, emit)
    done("Evaluating")

    stage("Verifying", "Verifying: extracting claims and checking each quote against its source")
    cands = extract_candidates(llm, topic, kept, depth, cfg, emit)
    findings, vstats = verify(cands, kept, depth, cfg, emit)
    done("Verifying")

    stage("Conflict checking", "Checking findings for genuine disagreement")
    conflicts, checked = detect(llm, topic, findings, emit)
    done("Conflict checking")

    stage("Writing", "Writing the report")
    report = build_report(llm, topic, depth, findings, conflicts, kept, plan,
                          {"search": sstats, "eval": estats, "verify": vstats, "conflicts_checked": checked}, emit)
    done("Writing")

    task = {"id": history.new_id(), "topic": topic, "depth": depth,
            "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "duration": round(time.time() - t0, 1),
            "model": llm.label, "plan": plan, "report": report, "log": log}
    history.save(task)
    emit(msg=f"Done in {task['duration']}s and saved to Research History")
    return task
