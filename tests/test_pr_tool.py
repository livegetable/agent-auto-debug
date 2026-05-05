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
