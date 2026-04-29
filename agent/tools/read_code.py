import os
from agent.config import PROJECT_ROOT


def read_file(file_path: str, start_line: int = 1, end_line: int | None = None) -> dict:
    abs_path = _resolve_path(file_path)
    if not abs_path:
        return {"success": False, "error": f"File not found: {file_path}", "content": ""}

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        return {"success": False, "error": str(e), "content": ""}

    start_idx = max(0, start_line - 1)
    end_idx = len(lines) if end_line is None else min(end_line, len(lines))
    selected = lines[start_idx:end_idx]

    numbered = []
    for i, line in enumerate(selected, start=start_line):
        numbered.append(f"{i}: {line.rstrip()}")

    return {
        "success": True,
        "content": "\n".join(numbered),
        "file_path": str(abs_path),
        "total_lines": len(lines),
    }


def search_code(pattern: str, directory: str | None = None, file_glob: str = "*.py") -> dict:
    search_dir = _resolve_path(directory) if directory else PROJECT_ROOT
    if not search_dir or not os.path.isdir(search_dir):
        return {"success": False, "error": f"Directory not found: {directory}", "results": []}

    results = []
    for root, _dirs, files in os.walk(search_dir):
        for fname in files:
            if not fname.endswith(file_glob.lstrip("*")):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line_no, line in enumerate(f, start=1):
                        if pattern.lower() in line.lower():
                            rel = os.path.relpath(fpath, PROJECT_ROOT)
                            results.append({
                                "file": rel.replace("\\", "/"),
                                "line": line_no,
                                "content": line.rstrip(),
                            })
            except Exception:
                continue

    return {"success": True, "results": results}


def _resolve_path(path: str) -> str | None:
    if os.path.isabs(path) and (os.path.isfile(path) or os.path.isdir(path)):
        return path
    candidate = os.path.join(PROJECT_ROOT, path)
    if os.path.isfile(candidate) or os.path.isdir(candidate):
        return candidate
    return None
