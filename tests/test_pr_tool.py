import pytest
from unittest.mock import patch, MagicMock
from agent.pr_tool import (
    has_remote,
    get_remote_url,
    is_gh_available,
    is_gh_authenticated,
    push_branch,
    run_pr_workflow
)


def test_has_remote_true(monkeypatch):
    """测试有remote时返回True"""
    def mock_run_command(cmd, *args, **kwargs):
        if cmd == "git remote get-url origin":
            return (True, "git@github.com:user/repo.git")
        return (False, "")
    
    monkeypatch.setattr("agent.pr_tool._run_command", mock_run_command)
    assert has_remote() is True


def test_has_remote_false(monkeypatch):
    """测试没有remote时返回False"""
    def mock_run_command(cmd, *args, **kwargs):
        return (False, "")
    
    monkeypatch.setattr("agent.pr_tool._run_command", mock_run_command)
    assert has_remote() is False


def test_get_remote_url(monkeypatch):
    """测试获取remote URL"""
    def mock_run_command(cmd, *args, **kwargs):
        if cmd == "git remote get-url origin":
            return (True, "git@github.com:user/repo.git")
        return (False, "")
    
    monkeypatch.setattr("agent.pr_tool._run_command", mock_run_command)
    assert get_remote_url() == "git@github.com:user/repo.git"


def test_is_gh_available_true(monkeypatch):
    """测试gh CLI可用"""
    def mock_run_command(cmd, *args, **kwargs):
        if cmd == "gh --version":
            return (True, "gh version 2.40.1")
        return (False, "")
    
    monkeypatch.setattr("agent.pr_tool._run_command", mock_run_command)
    assert is_gh_available() is True


def test_is_gh_available_false(monkeypatch):
    """测试gh CLI不可用"""
    def mock_run_command(cmd, *args, **kwargs):
        return (False, "command not found: gh")
    
    monkeypatch.setattr("agent.pr_tool._run_command", mock_run_command)
    assert is_gh_available() is False


def test_is_gh_authenticated_true(monkeypatch):
    """测试gh已登录"""
    def mock_run_command(cmd, *args, **kwargs):
        if cmd == "gh auth status":
            return (True, "Logged in to github.com")
        return (False, "")
    
    monkeypatch.setattr("agent.pr_tool._run_command", mock_run_command)
    assert is_gh_authenticated() is True


def test_is_gh_authenticated_false(monkeypatch):
    """测试gh未登录"""
    def mock_run_command(cmd, *args, **kwargs):
        return (False, "You are not logged into any GitHub hosts")
    
    monkeypatch.setattr("agent.pr_tool._run_command", mock_run_command)
    assert is_gh_authenticated() is False


def test_push_branch_allow_autofix(monkeypatch):
    """测试允许推送autofix/开头的分支"""
    def mock_run_command(cmd, *args, **kwargs):
        if cmd.startswith("git push -u origin autofix/"):
            return (True, "Pushed branch autofix/keyerror-get_user to remote successfully")
        return (False, "")
    
    monkeypatch.setattr("agent.pr_tool._run_command", mock_run_command)
    success, msg = push_branch("autofix/keyerror-get_user")
    assert success is True
    assert "Pushed branch" in msg
    assert "autofix/keyerror-get_user" in msg
    assert "successfully" in msg


def test_push_branch_reject_non_autofix(monkeypatch):
    """测试拒绝推送非autofix/开头的分支"""
    success, msg = push_branch("main")
    assert success is False
    assert "Security check" in msg
    assert "Only 'autofix/*' branches can be pushed" in msg
    
    success, msg = push_branch("feature/test")
    assert success is False
    assert "Security check" in msg


def test_run_pr_workflow_no_git_commit():
    """测试没有git commit时跳过PR"""
    record = {
        "git_result": {"success": False, "skipped": True, "reason": "No changes to commit"}
    }
    result = run_pr_workflow(record)
    assert result["skipped"] is True
    assert result["success"] is False
    assert result["reason"] == "Git commit not available"


def test_run_pr_workflow_no_remote(monkeypatch):
    """测试没有remote时跳过PR"""
    record = {
        "git_result": {"success": True, "branch": "autofix/keyerror-get_user"}
    }
    
    def mock_run_command(cmd, *args, **kwargs):
        if cmd == "git remote get-url origin":
            return (False, "")
        return (False, "")
    
    monkeypatch.setattr("agent.pr_tool._run_command", mock_run_command)
    result = run_pr_workflow(record)
    assert result["skipped"] is True
    assert result["reason"] == "No git remote configured"


def test_run_pr_workflow_gh_not_available(monkeypatch):
    """测试gh不可用时跳过PR"""
    record = {
        "git_result": {"success": True, "branch": "autofix/keyerror-get_user"}
    }
    
    def mock_run_command(cmd, *args, **kwargs):
        if cmd == "git remote get-url origin":
            return (True, "git@github.com:user/repo.git")
        elif cmd == "gh --version":
            return (False, "command not found")
        return (False, "")
    
    monkeypatch.setattr("agent.pr_tool._run_command", mock_run_command)
    result = run_pr_workflow(record)
    assert result["skipped"] is True
    assert result["reason"] == "GitHub CLI not installed"


def test_run_pr_workflow_gh_not_authenticated(monkeypatch):
    """测试gh未登录时跳过PR"""
    record = {
        "git_result": {"success": True, "branch": "autofix/keyerror-get_user"}
    }
    
    def mock_run_command(cmd, *args, **kwargs):
        if cmd == "git remote get-url origin":
            return (True, "git@github.com:user/repo.git")
        elif cmd == "gh --version":
            return (True, "gh version 2.40.1")
        elif cmd == "gh auth status":
            return (False, "Not logged in")
        return (False, "")
    
    monkeypatch.setattr("agent.pr_tool._run_command", mock_run_command)
    result = run_pr_workflow(record)
    assert result["skipped"] is True
    assert result["reason"] == "GitHub CLI not authenticated"


def test_run_pr_workflow_invalid_branch(monkeypatch):
    """测试分支名不合法时跳过PR"""
    record = {
        "git_result": {"success": True, "branch": "main"}
    }
    
    def mock_run_command(cmd, *args, **kwargs):
        if cmd == "git remote get-url origin":
            return (True, "git@github.com:user/repo.git")
        elif cmd == "gh --version":
            return (True, "gh version 2.40.1")
        elif cmd == "gh auth status":
            return (True, "Logged in")
        return (False, "")
    
    monkeypatch.setattr("agent.pr_tool._run_command", mock_run_command)
    result = run_pr_workflow(record)
    assert result["skipped"] is True
    assert "must start with 'autofix/'" in result["reason"]


def test_create_pull_request_default_base(monkeypatch):
    """测试创建PR默认使用develop作为base分支"""
    from agent.pr_tool import create_pull_request
    
    def mock_run_command(cmd, *args, **kwargs):
        if "gh pr create" in cmd:
            # 检查命令是否包含--base参数
            assert "--base develop" in cmd
            assert "--head autofix/keyerror-get_user" in cmd
            return (True, "https://github.com/user/repo/pull/1")
        return (False, "")
    
    monkeypatch.setattr("agent.pr_tool._run_command", mock_run_command)
    success, msg = create_pull_request("autofix/keyerror-get_user", "Test PR", "Test body")
    assert success is True
    assert "https://github.com/user/repo/pull/1" in msg


def test_create_pull_request_env_base(monkeypatch):
    """测试通过环境变量GITHUB_PR_BASE_BRANCH覆盖base分支"""
    import os
    from agent.pr_tool import create_pull_request
    
    # 设置环境变量
    monkeypatch.setenv("GITHUB_PR_BASE_BRANCH", "main")
    
    def mock_run_command(cmd, *args, **kwargs):
        if "gh pr create" in cmd:
            # 检查命令是否使用环境变量设置的base
            assert "--base main" in cmd
            assert "--head autofix/keyerror-get_user" in cmd
            return (True, "https://github.com/user/repo/pull/2")
        return (False, "")
    
    monkeypatch.setattr("agent.pr_tool._run_command", mock_run_command)
    success, msg = create_pull_request("autofix/keyerror-get_user", "Test PR", "Test body")
    assert success is True
    assert "https://github.com/user/repo/pull/2" in msg
    
    # 清除环境变量
    monkeypatch.delenv("GITHUB_PR_BASE_BRANCH", raising=False)


def test_run_pr_workflow_includes_base_branch(monkeypatch):
    """测试run_pr_workflow返回结果包含base_branch"""
    record = {
        "git_result": {"success": True, "branch": "autofix/keyerror-get_user"},
        "error_type": "KeyError",
        "function_name": "get_user",
        "traceback_summary": "KeyError: 'age'",
        "fix_mode": "LLM",
        "root_cause": "Missing age field",
        "fix_strategy": "Use get() method",
        "record_path": "fix_records/bug_001.md"
    }
    
    def mock_run_command(cmd, *args, **kwargs):
        if cmd == "git remote get-url origin":
            return (True, "git@github.com:user/repo.git")
        elif cmd == "gh --version":
            return (True, "gh version 2.40.1")
        elif cmd == "gh auth status":
            return (True, "Logged in")
        elif cmd.startswith("git push -u origin autofix/"):
            return (True, "Pushed successfully")
        elif "gh pr create" in cmd:
            assert "--base develop" in cmd
            return (True, "https://github.com/user/repo/pull/3")
        return (False, "")
    
    monkeypatch.setattr("agent.pr_tool._run_command", mock_run_command)
    result = run_pr_workflow(record)
    
    assert result["success"] is True
    assert result["skipped"] is False
    assert result["base_branch"] == "develop"
    assert result["branch"] == "autofix/keyerror-get_user"
    assert result["pr_url"] == "https://github.com/user/repo/pull/3"
