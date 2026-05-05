import subprocess
import os
import shutil
from agent.config import GITHUB_TOKEN, GITHUB_REPO, BRANCH_PREFIX, PROJECT_ROOT


def _run_command(cmd: list[str], check: bool = True, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=check,
        cwd=PROJECT_ROOT,
        env=env,
        encoding="utf-8",
        errors="replace",
    )


def create_branch(branch_name: str) -> dict:
    try:
        _run_command(["git", "checkout", "-b", branch_name], check=True)
        return {"success": True, "branch": branch_name}
    except FileNotFoundError:
        return {"success": False, "error": "git command not found"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}


def commit_changes(message: str) -> dict:
    try:
        _run_command(["git", "add", "-A"], check=True)
        _run_command(["git", "commit", "-m", message], check=True)
        return {"success": True, "message": message}
    except FileNotFoundError:
        return {"success": False, "error": "git command not found"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}


def push_branch(branch_name: str) -> dict:
    try:
        _run_command(["git", "push", "-u", "origin", branch_name], check=True)
        return {"success": True, "branch": branch_name}
    except FileNotFoundError:
        return {"success": False, "error": "git command not found"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}


def create_pr(title: str, body: str, head: str, base: str = "main") -> dict:
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return {"success": False, "error": "GITHUB_TOKEN or GITHUB_REPO not configured"}
    if shutil.which("gh") is None:
        return {"success": False, "error": "gh CLI not found in PATH"}

    try:
        cmd = [
            "gh", "pr", "create",
            "--title", title,
            "--body", body,
            "--head", head,
            "--base", base,
            "--repo", GITHUB_REPO,
        ]
        env = os.environ.copy()
        env["GH_TOKEN"] = GITHUB_TOKEN
        result = _run_command(cmd, check=True, env=env)
        pr_url = result.stdout.strip()
        return {"success": True, "pr_url": pr_url}
    except FileNotFoundError:
        return {"success": False, "error": "gh CLI not found in PATH"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}


def get_current_branch() -> str:
    try:
        result = _run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], check=True)
        return result.stdout.strip()
    except FileNotFoundError:
        return "unknown"
    except subprocess.CalledProcessError:
        return "unknown"


def checkout_branch(branch_name: str) -> dict:
    try:
        _run_command(["git", "checkout", branch_name], check=True)
        return {"success": True, "branch": branch_name}
    except FileNotFoundError:
        return {"success": False, "error": "git command not found"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}


def delete_branch(branch_name: str) -> dict:
    try:
        _run_command(["git", "branch", "-D", branch_name], check=True)
        return {"success": True, "branch": branch_name}
    except FileNotFoundError:
        return {"success": False, "error": "git command not found"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}
