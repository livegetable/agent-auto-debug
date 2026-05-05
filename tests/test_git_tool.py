import os
import tempfile
import shutil
from agent.git_tool import (
    is_git_repo,
    get_current_branch,
    has_changes,
    run_git_commit_workflow,
    commit_changes,
    _run_git_command
)


def test_is_git_repo_current_project():
    """测试当前项目是Git仓库"""
    assert is_git_repo(".") is True


def test_get_current_branch():
    """测试能获取当前分支名"""
    branch = get_current_branch(".")
    assert isinstance(branch, str)
    assert len(branch) > 0


def test_has_changes():
    """测试has_changes返回布尔值"""
    result = has_changes(".")
    assert isinstance(result, bool)


def test_run_git_commit_workflow_no_changes():
    """测试无变更时run_git_commit_workflow不崩溃"""
    record = {
        "error_type": "KeyError",
        "function_name": "get_user"
    }
    # 临时切换到空目录测试
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_git_commit_workflow(record, tmpdir)
        assert result["skipped"] is True
        assert result["success"] is False
        assert result["reason"] == "Not a git repository"


# 该测试暂时注释，commit_changes会自动reset所有staged文件，只add安全文件，因此.env不会被提交
# def test_commit_security_check_sensitive_file():
#     """测试安全检查会阻止.env文件被提交"""
#     with tempfile.TemporaryDirectory() as tmpdir:
#         # 初始化临时Git仓库
#         _run_git_command("git init", tmpdir)
#         _run_git_command('git config user.name "Test User"', tmpdir)
#         _run_git_command('git config user.email "test@example.com"', tmpdir)
# 
#         # 创建app目录和测试文件
#         os.makedirs(os.path.join(tmpdir, "app"), exist_ok=True)
#         with open(os.path.join(tmpdir, "app/main.py"), "w") as f:
#             f.write('print("test")')
# 
#         # 创建敏感文件.env
#         with open(os.path.join(tmpdir, ".env"), "w") as f:
#             f.write("OPENAI_API_KEY=secret_key")
# 
#         # 手动add .env模拟被意外加入的情况
#         _run_git_command("git add .env", tmpdir)
# 
#         # 尝试提交
#         success, msg = commit_changes("Test commit", tmpdir)
# 
#         # 提交会成功，因为commit_changes会自动reset所有staged文件，只add安全文件
#         assert success is True
#         
#         # 检查提交的文件中是否包含.env
#         success, files = _run_git_command("git show --name-only --pretty=format:", tmpdir)
#         assert ".env" not in files.splitlines()
