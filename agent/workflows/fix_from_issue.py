import re
import os
import json
import subprocess
from agent.tools.read_code import read_file, search_code
from agent.tools.run_test import run_test
from agent.tools.git_ops import (
    create_branch, commit_changes, push_branch, create_pr,
    get_current_branch,
)
from agent.tools.notify_feishu import send_success_card, send_failure_card
from agent.llm import analyze_and_fix
from agent.records.store import save_record, generate_fix_id
from agent.config import PROJECT_ROOT, TEST_COMMAND, MAX_CHANGED_FILES, BRANCH_PREFIX


def parse_issue(issue_text: str) -> dict:
    error_type = "Unknown"
    error_type_match = re.search(r"(\w+Error|\w+Exception)", issue_text)
    if error_type_match:
        error_type = error_type_match.group(1)

    file_matches = re.findall(r'`([^`]+\.py)`', issue_text)
    files = []
    for f in file_matches:
        if os.path.isfile(os.path.join(PROJECT_ROOT, f)):
            files.append(f)

    return {
        "error_type": error_type,
        "description": issue_text,
        "files": files,
    }


def gather_code_context_from_issue(issue_info: dict) -> dict[str, str]:
    code_context = {}
    seen = set()

    for fpath in issue_info.get("files", []):
        if fpath in seen:
            continue
        seen.add(fpath)
        result = read_file(fpath)
        if result["success"]:
            code_context[fpath] = result["content"]

    if not code_context:
        search_terms = issue_info["description"].split()[:5]
        for term in search_terms:
            if len(term) < 3:
                continue
            search_result = search_code(term)
            if search_result["success"]:
                for r in search_result["results"][:3]:
                    fpath = r["file"]
                    if fpath not in seen:
                        seen.add(fpath)
                        result = read_file(fpath)
                        if result["success"]:
                            code_context[fpath] = result["content"]

    return code_context


def run_fix_from_issue(issue_text: str, max_attempts: int = 3) -> dict:
    fix_id = generate_fix_id()
    print(f"[Agent] Starting issue-based fix workflow: {fix_id}")

    print("[Agent] Step 1: Parsing issue...")
    issue_info = parse_issue(issue_text)
    print(f"[Agent] Detected error type: {issue_info['error_type']}")

    print("[Agent] Step 2: Gathering code context...")
    code_context = gather_code_context_from_issue(issue_info)
    print(f"[Agent] Loaded {len(code_context)} files for context")

    for attempt in range(1, max_attempts + 1):
        print(f"[Agent] Step 3: Analyzing and generating patch (attempt {attempt}/{max_attempts})...")
        llm_result = analyze_and_fix(
            traceback_text=issue_text,
            code_context=code_context,
            test_command=TEST_COMMAND,
        )

        if not llm_result.get("patch"):
            print("[Agent] LLM did not generate a patch")
            continue

        if len(llm_result.get("changed_files", [])) > MAX_CHANGED_FILES:
            print(f"[Agent] Patch changes too many files, skipping")
            continue

        print(f"[Agent] Root cause: {llm_result['root_cause']}")

        print("[Agent] Step 4: Applying patch...")
        from agent.workflows.fix_from_traceback import apply_patch, revert_changes
        apply_result = apply_patch(llm_result["patch"])
        if not apply_result["success"]:
            print(f"[Agent] Patch apply failed: {apply_result['error']}")
            revert_changes()
            continue

        print("[Agent] Step 5: Running tests...")
        test_result = run_test()
        if not test_result["success"]:
            print(f"[Agent] Tests failed after patch (attempt {attempt})")
            revert_changes()
            continue

        print("[Agent] Tests passed!")

        print("[Agent] Step 6: Creating branch and committing...")
        branch_name = f"{BRANCH_PREFIX}-{fix_id}"
        branch_result = create_branch(branch_name)
        if not branch_result["success"]:
            revert_changes()
            record = _build_issue_record(fix_id, issue_info, llm_result, "failed",
                                         error=f"Branch creation failed")
            save_record(record)
            return record

        commit_msg = f"fix({fix_id}): {llm_result['root_cause'][:80]}"
        commit_result = commit_changes(commit_msg)

        print("[Agent] Step 7: Pushing and creating PR...")
        pr_url = ""
        push_result = push_branch(branch_name)
        if push_result["success"]:
            pr_body = f"## Agent Auto-Fix (from Issue): {fix_id}\n\n{llm_result.get('root_cause', '')}\n\n{llm_result.get('explanation', '')}"
            pr_result = create_pr(
                title=f"[Agent Fix] {fix_id}: {issue_info['error_type']}",
                body=pr_body,
                head=branch_name,
            )
            if pr_result["success"]:
                pr_url = pr_result["pr_url"]

        print("[Agent] Step 8: Sending Feishu notification...")
        feishu_result = send_success_card(
            fix_id=fix_id,
            error_type=issue_info["error_type"],
            root_cause=llm_result["root_cause"],
            branch=branch_name,
            pr_url=pr_url,
            changed_files=llm_result.get("changed_files", []),
        )

        record = _build_issue_record(
            fix_id, issue_info, llm_result, "success",
            branch=branch_name, pr_url=pr_url,
            feishu_notified=feishu_result.get("success", False),
        )
        save_record(record)
        print(f"[Agent] Issue fix workflow completed: {fix_id}")
        return record

    feishu_result = send_failure_card(
        fix_id=fix_id,
        error_type=issue_info["error_type"],
        root_cause="Auto-fix failed after multiple attempts",
        reason="Could not generate a passing patch from issue description",
    )

    record = _build_issue_record(
        fix_id, issue_info, None, "failed",
        feishu_notified=feishu_result.get("success", False),
    )
    save_record(record)
    return record


def _build_issue_record(
    fix_id: str,
    issue_info: dict,
    llm_result: dict | None,
    status: str,
    branch: str = "",
    pr_url: str = "",
    feishu_notified: bool = False,
    error: str = "",
) -> dict:
    record = {
        "id": fix_id,
        "source": "issue",
        "error_type": issue_info.get("error_type", "Unknown"),
        "root_cause": llm_result.get("root_cause", "") if llm_result else "",
        "changed_files": llm_result.get("changed_files", []) if llm_result else [],
        "test_result": "passed" if status == "success" else "failed",
        "branch": branch,
        "pr_url": pr_url,
        "feishu_notified": feishu_notified,
        "status": status,
    }
    if error:
        record["error"] = error
    return record
