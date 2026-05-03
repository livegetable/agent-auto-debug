import re
import os
import subprocess
from agent.tools.read_log import read_log
from agent.tools.read_code import read_file, search_code
from agent.tools.run_test import run_test
from agent.tools.git_ops import (
    create_branch, commit_changes, push_branch, create_pr,
    get_current_branch, checkout_branch,
)
from agent.tools.notify_feishu import send_success_card, send_failure_card
from agent.llm import analyze_and_fix
from agent.records.store import save_record, generate_fix_id
from agent.config import PROJECT_ROOT, TEST_COMMAND, MAX_CHANGED_FILES, BRANCH_PREFIX


def extract_traceback_info(log_content: str) -> dict:
    tb_match = re.search(
        r"Traceback \(most recent call last\):[\s\S]*?(\w+Error|\w+Exception): (.+?)(?:\n|$)",
        log_content,
    )
    if not tb_match:
        return {"error_type": "Unknown", "error_message": "", "traceback": log_content}

    full_traceback = tb_match.group(0)
    error_type = tb_match.group(1)
    error_message = tb_match.group(2)

    file_matches = re.findall(
        r'File "(.+?)", line (\d+)',
        full_traceback,
    )

    files = []
    for fpath, lineno in file_matches:
        rel = os.path.relpath(fpath, PROJECT_ROOT).replace("\\", "/")
        files.append({"file": rel, "line": int(lineno)})

    return {
        "error_type": error_type,
        "error_message": error_message,
        "traceback": full_traceback,
        "files": files,
    }


def gather_code_context(traceback_info: dict) -> dict[str, str]:
    code_context = {}
    seen = set()

    for file_info in traceback_info.get("files", []):
        fpath = file_info["file"]
        if fpath in seen:
            continue
        seen.add(fpath)

        result = read_file(fpath)
        if result["success"]:
            code_context[fpath] = result["content"]

        test_path = _find_test_file(fpath)
        if test_path and test_path not in seen:
            seen.add(test_path)
            result = read_file(test_path)
            if result["success"]:
                code_context[test_path] = result["content"]

    return code_context


def _find_test_file(source_path: str) -> str | None:
    parts = source_path.replace("\\", "/").split("/")
    filename = parts[-1]
    name_without_ext = os.path.splitext(filename)[0]
    test_filename = f"test_{name_without_ext}.py"

    search_result = search_code(test_filename.replace(".py", ""), file_glob="test_*.py")
    if search_result["success"] and search_result["results"]:
        for r in search_result["results"]:
            if r["file"].endswith(test_filename):
                return r["file"]

    return None


def apply_patch(patch_text: str) -> dict:
    normalized_patch = _normalize_patch_text(patch_text)
    if not normalized_patch.strip():
        return {"success": False, "error": "Empty patch"}

    patch_file = os.path.join(PROJECT_ROOT, "_agent_patch.diff")
    try:
        with open(patch_file, "w", encoding="utf-8") as f:
            f.write(normalized_patch)

        result = subprocess.run(
            ["git", "apply", "--check", patch_file],
            capture_output=True, text=True, cwd=PROJECT_ROOT,
        )
        if result.returncode != 0:
            return {
                "success": False,
                "error": (
                    f"Patch check failed: {result.stderr}\n\n"
                    f"Patch preview:\n{_preview_text(normalized_patch)}"
                ),
            }

        result = subprocess.run(
            ["git", "apply", patch_file],
            capture_output=True, text=True, cwd=PROJECT_ROOT,
        )
        if result.returncode != 0:
            return {"success": False, "error": f"Patch apply failed: {result.stderr}"}

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        if os.path.isfile(patch_file):
            os.remove(patch_file)


def _normalize_patch_text(patch_text: str) -> str:
    patch = (patch_text or "").replace("\r\n", "\n").strip()
    if not patch:
        return ""

    fenced_match = re.search(r"```(?:diff)?\n([\s\S]*?)```", patch, flags=re.IGNORECASE)
    if fenced_match:
        patch = fenced_match.group(1).strip()

    lines = patch.split("\n")
    start_index = 0
    for index, line in enumerate(lines):
        if line.startswith("--- ") or line.startswith("diff --git "):
            start_index = index
            break
    patch = "\n".join(lines[start_index:]).strip()
    return patch + "\n"


def _preview_text(text: str, max_lines: int = 30) -> str:
    lines = text.splitlines()
    preview_lines = lines[:max_lines]
    if len(lines) > max_lines:
        preview_lines.append("...<截断>")
    return "\n".join(preview_lines)


def revert_changes() -> dict:
    try:
        subprocess.run(
            ["git", "checkout", "--", "."],
            capture_output=True, text=True, cwd=PROJECT_ROOT,
        )
        subprocess.run(
            ["git", "clean", "-fd"],
            capture_output=True, text=True, cwd=PROJECT_ROOT,
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_fix_workflow(log_path: str | None = None, max_attempts: int = 3) -> dict:
    fix_id = generate_fix_id()
    original_branch = get_current_branch()
    print(f"[Agent] 开始修复流程: {fix_id}")

    log_result = read_log(log_path)
    if not log_result["success"]:
        record = _build_record(fix_id, "traceback_log", "Unknown", "", [], "failed",
                               error="Failed to read log file")
        save_record(record)
        return record

    print("[Agent] 步骤1：读取并解析 traceback...")
    traceback_info = extract_traceback_info(log_result["content"])
    if traceback_info["error_type"] == "Unknown":
        record = _build_record(fix_id, "traceback_log", "Unknown", "", [], "failed",
                               error="Could not parse traceback from log")
        save_record(record)
        return record

    print(f"[Agent] 识别到错误: {traceback_info['error_type']}: {traceback_info['error_message']}")

    print("[Agent] 步骤2：收集代码上下文...")
    code_context = gather_code_context(traceback_info)
    print(f"[Agent] 已加载上下文文件数: {len(code_context)}")

    for attempt in range(1, max_attempts + 1):
        print(f"[Agent] 步骤3：分析根因并生成补丁（第 {attempt}/{max_attempts} 次）...")
        llm_result = analyze_and_fix(
            traceback_text=traceback_info["traceback"],
            code_context=code_context,
            test_command=TEST_COMMAND,
        )

        if not llm_result.get("patch"):
            print("[Agent] LLM 未生成补丁")
            if llm_result.get("root_cause"):
                print(f"[Agent] 原因: {llm_result['root_cause']}")
            if llm_result.get("explanation"):
                print(f"[Agent] 说明: {llm_result['explanation']}")
            continue

        if len(llm_result.get("changed_files", [])) > MAX_CHANGED_FILES:
            print(f"[Agent] 补丁修改文件过多（{len(llm_result['changed_files'])}），跳过")
            continue

        print(f"[Agent] 根因分析: {llm_result['root_cause']}")
        print(f"[Agent] 置信度: {llm_result.get('confidence', 0)}")

        print("[Agent] 步骤4：应用补丁...")
        apply_result = apply_patch(llm_result["patch"])
        if not apply_result["success"]:
            print(f"[Agent] 补丁应用失败: {apply_result['error']}")
            revert_changes()
            continue

        print("[Agent] 步骤5：执行测试...")
        test_result = run_test()
        if not test_result["success"]:
            print(f"[Agent] 补丁后测试失败（第 {attempt} 次）")
            print(f"[Agent] 测试输出:\n{test_result['stdout']}\n{test_result['stderr']}")
            revert_changes()
            code_context_updated = {}
            for fpath in llm_result.get("changed_files", []):
                r = read_file(fpath)
                if r["success"]:
                    code_context_updated[fpath] = r["content"]
            code_context.update(code_context_updated)
            continue

        print("[Agent] 测试通过，继续执行 Git 流程...")

        print("[Agent] 步骤6：创建分支并提交...")
        branch_name = f"{BRANCH_PREFIX}-{fix_id}"
        branch_result = create_branch(branch_name)
        if not branch_result["success"]:
            print(f"[Agent] 创建分支失败: {branch_result['error']}")
            revert_changes()
            record = _build_record(
                fix_id, "traceback_log", traceback_info["error_type"],
                llm_result["root_cause"], llm_result.get("changed_files", []),
                "failed", error=f"Branch creation failed: {branch_result['error']}",
            )
            save_record(record)
            return record

        commit_msg = f"fix({fix_id}): {llm_result['root_cause'][:80]}"
        commit_result = commit_changes(commit_msg)
        if not commit_result["success"]:
            print(f"[Agent] 提交失败: {commit_result['error']}")
            record = _build_record(
                fix_id, "traceback_log", traceback_info["error_type"],
                llm_result["root_cause"], llm_result.get("changed_files", []),
                "failed", error=f"Commit failed: {commit_result['error']}",
                branch=branch_name,
            )
            save_record(record)
            return record

        print("[Agent] 步骤7：推送并创建 PR...")
        push_result = push_branch(branch_name)
        pr_url = ""
        if push_result["success"]:
            pr_body = _build_pr_body(fix_id, traceback_info, llm_result, test_result)
            pr_result = create_pr(
                title=f"[Agent Fix] {fix_id}: {traceback_info['error_type']}",
                body=pr_body,
                head=branch_name,
            )
            if pr_result["success"]:
                pr_url = pr_result["pr_url"]
                print(f"[Agent] PR 已创建: {pr_url}")
            else:
                print(f"[Agent] 创建 PR 失败: {pr_result['error']}")
        else:
            print(f"[Agent] 推送失败: {push_result['error']}")

        print("[Agent] 步骤8：发送飞书通知...")
        feishu_result = send_success_card(
            fix_id=fix_id,
            error_type=traceback_info["error_type"],
            root_cause=llm_result["root_cause"],
            branch=branch_name,
            pr_url=pr_url,
            changed_files=llm_result.get("changed_files", []),
        )
        feishu_notified = feishu_result.get("success", False)

        record = _build_record(
            fix_id, "traceback_log", traceback_info["error_type"],
            llm_result["root_cause"], llm_result.get("changed_files", []),
            "success", branch=branch_name, pr_url=pr_url,
            feishu_notified=feishu_notified,
        )
        save_record(record)
        print(f"[Agent] 修复流程已完成: {fix_id}")
        return record

    print(f"[Agent] 已重试 {max_attempts} 次，全部失败")

    feishu_result = send_failure_card(
        fix_id=fix_id,
        error_type=traceback_info["error_type"],
        root_cause="Auto-fix failed after multiple attempts",
        reason="Could not generate a patch that passes all tests",
    )

    record = _build_record(
        fix_id, "traceback_log", traceback_info["error_type"],
        "Auto-fix failed after multiple attempts", [], "failed",
        feishu_notified=feishu_result.get("success", False),
    )
    save_record(record)
    return record


def _build_record(
    fix_id: str,
    source: str,
    error_type: str,
    root_cause: str,
    changed_files: list[str],
    status: str,
    branch: str = "",
    pr_url: str = "",
    feishu_notified: bool = False,
    error: str = "",
) -> dict:
    record = {
        "id": fix_id,
        "source": source,
        "error_type": error_type,
        "root_cause": root_cause,
        "changed_files": changed_files,
        "test_result": "passed" if status == "success" else "failed",
        "branch": branch,
        "pr_url": pr_url,
        "feishu_notified": feishu_notified,
        "status": status,
    }
    if error:
        record["error"] = error
    return record


def _build_pr_body(
    fix_id: str,
    traceback_info: dict,
    llm_result: dict,
    test_result: dict,
) -> str:
    body_parts = [
        f"## Agent Auto-Fix: {fix_id}",
        "",
        f"**Error Type**: `{traceback_info['error_type']}`",
        f"**Error Message**: {traceback_info['error_message']}",
        "",
        "### Root Cause Analysis",
        llm_result.get("root_cause", "N/A"),
        "",
        "### Fix Explanation",
        llm_result.get("explanation", "N/A"),
        "",
        "### Changed Files",
    ]
    for f in llm_result.get("changed_files", []):
        body_parts.append(f"- `{f}`")

    body_parts.extend([
        "",
        "### Test Evidence",
        "```",
        test_result.get("stdout", "N/A"),
        "```",
        "",
        "---",
        "*This PR was automatically generated by the Agent Auto-Debug System.*",
        "*Please review before merging.*",
    ])
    return "\n".join(body_parts)
