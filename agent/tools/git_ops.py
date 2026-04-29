import subprocess
import os
from agent.config import GITHUB_TOKEN, GITHUB_REPO, BRANCH_PREFIX, PROJECT_ROOT


def create_branch(branch_name: str) -> dict:
    try:
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            capture_output=True, text=True, check=True, cwd=PROJECT_ROOT,
        )
        return {"success": True, "branch": branch_name}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}


def commit_changes(message: str) -> dict:
    try:
        subprocess.run(
            ["git", "add", "-A"],
            capture_output=True, text=True, check=True, cwd=PROJECT_ROOT,
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True, text=True, check=True, cwd=PROJECT_ROOT,
        )
        return {"success": True, "message": message}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}


def push_branch(branch_name: str) -> dict:
    try:
        subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            capture_output=True, text=True, check=True, cwd=PROJECT_ROOT,
        )
        return {"success": True, "branch": branch_name}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}


def create_pr(title: str, body: str, head: str, base: str = "main") -> dict:
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return {"success": False, "error": "GITHUB_TOKEN or GITHUB_REPO not configured"}

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
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True,
            cwd=PROJECT_ROOT, env=env,
        )
        pr_url = result.stdout.strip()
        return {"success": True, "pr_url": pr_url}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}


def get_current_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True, cwd=PROJECT_ROOT,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def checkout_branch(branch_name: str) -> dict:
    try:
        subprocess.run(
            ["git", "checkout", branch_name],
            capture_output=True, text=True, check=True, cwd=PROJECT_ROOT,
        )
        return {"success": True, "branch": branch_name}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}
