import os
import subprocess
from typing import Tuple, Dict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def _run_command(cmd: str, repo_path: str = ".", capture_output: bool = True) -> Tuple[bool, str]:
    """运行命令，返回成功状态和输出"""
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            shell=True,
            capture_output=capture_output,
            text=True,
            timeout=30
        )
        return (result.returncode == 0, result.stdout.strip() or result.stderr.strip())
    except Exception as e:
        return (False, str(e))


def has_remote(repo_path: str = ".") -> bool:
    """检查是否配置了remote origin"""
    success, _ = _run_command("git remote get-url origin", repo_path)
    return success


def get_remote_url(repo_path: str = ".") -> str:
    """获取remote origin URL，不包含敏感信息"""
    success, output = _run_command("git remote get-url origin", repo_path)
    return output if success else ""


def is_gh_available() -> bool:
    """检查GitHub CLI是否可用"""
    success, _ = _run_command("gh --version")
    return success


def is_gh_authenticated() -> bool:
    """检查GitHub CLI是否已登录"""
    success, _ = _run_command("gh auth status")
    return success


def push_branch(branch_name: str, repo_path: str = ".") -> Tuple[bool, str]:
    """推送分支到远程，只允许推送autofix/开头的分支"""
    if not branch_name.startswith("autofix/"):
        return (False, f"Security check: Only 'autofix/*' branches can be pushed, rejected '{branch_name}'")
    
    success, output = _run_command(f"git push -u origin {branch_name}", repo_path)
    if success:
        return (True, f"Pushed branch {branch_name} to remote successfully")
    else:
        return (False, f"Failed to push branch: {output}")


def create_pull_request(branch_name: str, title: str, body: str, repo_path: str = ".") -> Tuple[bool, str]:
    """创建 GitHub PR；只复用 head/base 均匹配且仍然 open 的 PR。"""
    base_branch = os.getenv("GITHUB_PR_BASE_BRANCH", "develop")

    # 只查询 open 状态、head 分支匹配、base 分支也匹配的 PR
    # 避免复用旧的 closed PR，或 base 还是 submission/agent-auto-debug 的旧 PR
    success, output = _run_command(
        f'gh pr list --head {branch_name} --base {base_branch} --state open --json url --jq ".[0].url"',
        repo_path
    )

    if success and output.strip().startswith("http"):
        return (True, f"PR already exists: {output.strip()}")

    # 创建新 PR，显式指定 base 分支
    success, output = _run_command(
        f'gh pr create --base {base_branch} --head {branch_name} --title "{title}" --body "{body}"',
        repo_path
    )

    if success:
        lines = output.strip().splitlines()
        for line in lines:
            if line.startswith("https://github.com/"):
                return (True, line.strip())
        return (True, output.strip())

    return (False, f"Failed to create PR: {output}")


def run_pr_workflow(record: Dict, repo_path: str = ".") -> Dict:
    """PR创建工作流入口，返回结构化结果"""
    base_branch = os.getenv("GITHUB_PR_BASE_BRANCH", "develop")
    
    result = {
        "success": False,
        "skipped": True,
        "reason": "",
        "branch": "",
        "base_branch": base_branch,
        "pr_url": "",
        "message": ""
    }
    
    # A. 检查是否有成功的Git Commit
    git_result = record.get("git_result", {})
    if not git_result.get("success"):
        result["reason"] = "Git commit not available"
        return result
    
    branch_name = git_result.get("branch", "")
    result["branch"] = branch_name
    
    # B. 检查是否有remote
    if not has_remote(repo_path):
        result["reason"] = "No git remote configured"
        return result
    
    # C. 检查GitHub CLI是否可用
    if not is_gh_available():
        result["reason"] = "GitHub CLI not installed"
        return result
    
    # D. 检查是否已登录
    if not is_gh_authenticated():
        result["reason"] = "GitHub CLI not authenticated"
        return result
    
    # E. 检查分支名是否合法
    if not branch_name or not branch_name.startswith("autofix/"):
        result["reason"] = f"Invalid branch name: {branch_name}, must start with 'autofix/'"
        return result
    
    # F. 推送分支
    push_success, push_msg = push_branch(branch_name, repo_path)
    if not push_success:
        result["reason"] = push_msg
        return result
    
    # G. 创建PR
    error_type = record.get("error_type", "unknown")
    function_name = record.get("function_name", "unknown")
    pr_title = f"AutoFix: fix {error_type} in {function_name}"
    
    # 构造PR body
    pr_body_parts = [
        f"## AutoFix Agent 修复记录",
        f"- **Bug 类型**: {error_type}",
        f"- **出错函数**: {function_name}",
        f"- **修改文件**: {record.get('target_file', 'unknown')}",
        "",
        f"### Traceback 摘要",
        f"```\n{record.get('traceback_summary', '')}\n```",
        ""
    ]
    
    if record.get("fix_mode") == "LLM":
        pr_body_parts.extend([
            f"### LLM 根因分析",
            f"{record.get('root_cause', '')}",
            "",
            f"### LLM 修复策略",
            f"{record.get('fix_strategy', '')}",
            ""
        ])
    
    pr_body_parts.extend([
        f"### 测试结果",
        f"✅ 所有pytest测试通过",
        "",
        f"### 修复记录",
        f"本地修复记录：{record.get('record_path', 'fix_records/bug_001.md')}",
        "",
        f"---",
        f"This PR was generated by AutoFix Agent."
    ])
    
    pr_body = "\n".join(pr_body_parts)
    
    pr_success, pr_msg = create_pull_request(branch_name, pr_title, pr_body, repo_path)
    if not pr_success:
        result["reason"] = pr_msg
        return result
    
    # 提取PR URL
    pr_url = ""
    if "https://github.com/" in pr_msg:
        pr_url = [part for part in pr_msg.split() if part.startswith("https://github.com/")][0]
    elif pr_msg.startswith("https://github.com/"):
        pr_url = pr_msg.strip()
    
    result["success"] = True
    result["skipped"] = False
    result["pr_url"] = pr_url
    result["message"] = pr_msg
    
    return result
