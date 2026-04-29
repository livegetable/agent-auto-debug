import json
import os
from datetime import datetime, timezone, timedelta
from agent.config import RECORDS_PATH


def generate_fix_id() -> str:
    now = datetime.now(timezone(timedelta(hours=8)))
    date_str = now.strftime("%Y%m%d")
    existing = _load_all()
    count = len([r for r in existing if r.get("id", "").startswith(f"fix-{date_str}")])
    seq = str(count + 1).zfill(3)
    return f"fix-{date_str}-{seq}"


def save_record(record: dict) -> dict:
    os.makedirs(os.path.dirname(RECORDS_PATH), exist_ok=True)
    if "id" not in record:
        record["id"] = generate_fix_id()
    if "time" not in record:
        now = datetime.now(timezone(timedelta(hours=8)))
        record["time"] = now.isoformat()

    with open(RECORDS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def _load_all() -> list[dict]:
    if not os.path.isfile(RECORDS_PATH):
        return []
    records = []
    with open(RECORDS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def get_latest_records(limit: int = 10) -> list[dict]:
    records = _load_all()
    return records[-limit:]


def get_record_by_id(fix_id: str) -> dict | None:
    for record in _load_all():
        if record.get("id") == fix_id:
            return record
    return None
