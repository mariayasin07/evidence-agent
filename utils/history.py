import json
import time
import uuid

from utils.config import DATA

HIST = DATA / "history"
HIST.mkdir(parents=True, exist_ok=True)


def new_id():
    return time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4]


def save(task):
    (HIST / f"{task['id']}.json").write_text(json.dumps(task, ensure_ascii=False, indent=1), encoding="utf-8")


def load(task_id):
    try:
        return json.loads((HIST / f"{task_id}.json").read_text(encoding="utf-8"))
    except Exception:
        return None


def delete(task_id):
    try:
        (HIST / f"{task_id}.json").unlink()
    except Exception:
        pass


def list_tasks():
    out = []
    for p in sorted(HIST.glob("*.json"), reverse=True):
        try:
            t = json.loads(p.read_text(encoding="utf-8"))
            r = t.get("report", {})
            out.append(
                {
                    "id": t["id"],
                    "topic": t["topic"],
                    "depth": t.get("depth", ""),
                    "created": t.get("created", ""),
                    "findings": len(r.get("findings", [])),
                    "sources": len(r.get("references", [])),
                    "model": t.get("model", ""),
                }
            )
        except Exception:
            continue
    return out
