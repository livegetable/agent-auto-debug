import os
import subprocess
from typing import Tuple, Dict


def _run_git_command(cmd: str, repo_path: str = ".") -> Tuple[bool, str]:
    """运行git命令，返回成功状态和输出"""
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return (result.returncode == 0, result.stdout.strip() or result.stderr.strip())
    except Exception as e:
        return (False, str(e))


def is_git_repo(repo_path: str = ".") -> bool:
    """检查当前目录是否是Git仓库"""
    success, _ = _run_git_command("git rev-parse --is-inside-work-tree", repo_path)
    return success


def get_current_branch(repo_path: str = ".") -> str:
    """获取当前分支名，失败返回空字符串"""
    success, output = _run_git_command("git branch --show-current", repo_path)
    return output if success else ""


def has_changes(repo_path: str = ".") -> bool:
    """检查是否有未提交的变更"""
    success, output = _run_git_command("git status --porcelain", repo_path)
    return success and len(output.strip()) > 0


def create_autofix_branch(branch_name: str, repo_path: str = ".") -> Tuple[bool, str]:
    """创建并切换到修复分支；如果分支已存在，则切换到该分支。"""
    current_branch = get_current_branch(repo_path)

    if current_branch == branch_name:
        return (True, f"Already on branch {branch_name}")

    # 先明确检查本地分支是否已经存在
    success, output = _run_git_command(f"git branch --list {branch_name}", repo_path)

    if success and output.strip():
        # 分支已经存在，只允许 checkout，不再尝试 checkout -b
        success, checkout_output = _run_git_command(f"git checkout {branch_name}", repo_path)
        if success:
            return (True, f"Switched to existing branch {branch_name}")
        return (False, f"Branch {branch_name} exists but checkout failed: {checkout_output}")

    # 分支不存在，才创建新分支
    success, create_output = _run_git_command(f"git checkout -b {branch_name}", repo_path)

    if success:
        return (True, f"Created and switched to new branch {branch_name}")

    return (False, f"Failed to create branch {branch_name}: {create_output}")


def commit_changes(message: str, repo_path: str = ".") -> Tuple[bool, str]:
    """提交变更，只允许提交指定文件，安全检查敏感文件"""
    # 允许提交的文件/目录列表
    allowed_paths = [
        "app/main.py",
        "tests/test_app.py",
        "fix_records/bug_001.md",
        "fix_records/archive/",
        "README.md",
        "agent/",
        "tests/",
        "demo_reset.py",
        "requirements.txt",
        ".env.example",
        ".gitignore"
    ]
    
    # 先清理所有staged文件
    _run_git_command("git reset", repo_path)
    
    # 逐个add允许的文件/目录
    for path in allowed_paths:
        if os.path.exists(os.path.join(repo_path, path)):
            _run_git_command(f"git add {path}", repo_path)
    
    # 检查staged文件中是否有敏感文件
    success, staged_output = _run_git_command("git diff --cached --name-only", repo_path)
    if not success:
        return (False, "Failed to check staged files")
    
    sensitive_files = [".env", ".venv", "logs/error.log", "__pycache__", ".pytest_cache"]
    staged_files = staged_output.splitlines()
    
    for file in staged_files:
        for sensitive in sensitive_files:
            if sensitive in file:
                # 发现敏感文件，全部unstage
                _run_git_command("git reset", repo_path)
                return (False, f"Security check failed: Sensitive file {file} found in staged changes, commit aborted")
    
    # 检查是否有变更需要提交
    if not staged_files:
        return (False, "No changes to commit")
    
    # 执行commit
    success, output = _run_git_command(f'git commit -m "{message}"', repo_path)
    if not success:
        return (False, f"Commit failed: {output}")
    
    # 获取commit hash
    success, commit_hash = _run_git_command("git rev-parse --short HEAD", repo_path)
    if success:
        return (True, f"Commit successful: {commit_hash}")
    
    return (True, "Commit successful")


def run_git_commit_workflow(record: Dict, repo_path: str = ".") -> Dict:
    """Git Commit工作流入口，返回结构化结果"""
    result = {
        "success": False,
        "skipped": True,
        "reason": "",
        "branch": "",
        "commit_hash": "",
        "message": ""
    }
    
    # 检查是否是Git仓库
    if not is_git_repo(repo_path):
        result["reason"] = "Not a git repository"
        return result
    
    # 生成分支名
    error_type = record.get("error_type", "unknown").lower()
    function_name = record.get("function_name", "unknown").lower()
    branch_name = f"autofix/{error_type}-{function_name}"
    
    # 创建/切换分支
    branch_success, branch_msg = create_autofix_branch(branch_name, repo_path)
    if not branch_success:
        result["reason"] = branch_msg
        return result
    
    result["branch"] = branch_name
    
    # 检查是否有变更
    if not has_changes(repo_path):
        result["reason"] = "No changes to commit"
        return result
    
    # 生成commit消息
    commit_msg = f"AutoFix: fix {record.get('error_type')} in {record.get('function_name')}"
    
    # 提交变更
    commit_success, commit_msg_output = commit_changes(commit_msg, repo_path)
    if not commit_success:
        result["reason"] = commit_msg_output
        return result
    
    # 解析commit hash
    if "Commit successful: " in commit_msg_output:
        result["commit_hash"] = commit_msg_output.split(": ")[1]
    
    result["success"] = True
    result["skipped"] = False
    result["message"] = commit_msg_output
    
    return result
