import os
from agent.config import LOG_PATH


def read_log(log_path: str | None = None, tail: int = 100) -> dict:
    path = log_path or LOG_PATH
    if not os.path.isfile(path):
        return {"success": False, "error": f"Log file not found: {path}", "content": ""}

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    content = "".join(lines[-tail:])
    return {"success": True, "content": content, "path": path}


def tail_log(log_path: str | None = None, since_position: int = 0) -> dict:
    path = log_path or LOG_PATH
    if not os.path.isfile(path):
        return {"success": False, "error": f"Log file not found: {path}", "content": ""}

    with open(path, "r", encoding="utf-8") as f:
        f.seek(since_position)
        content = f.read()
        new_position = f.tell()

    return {"success": True, "content": content, "path": path, "position": new_position}


def get_log_size(log_path: str | None = None) -> int:
    path = log_path or LOG_PATH
    if not os.path.isfile(path):
        return 0
    return os.path.getsize(path)
