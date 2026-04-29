import json
import requests
from agent.config import FEISHU_WEBHOOK_URL, FEISHU_NOTIFY_MODE


def send_success_card(
    fix_id: str,
    error_type: str,
    root_cause: str,
    branch: str,
    pr_url: str,
    changed_files: list[str],
) -> dict:
    card = _build_card(
        title="🤖 Agent 自动修复成功",
        status="success",
        fix_id=fix_id,
        error_type=error_type,
        root_cause=root_cause,
        branch=branch,
        pr_url=pr_url,
        changed_files=changed_files,
    )
    return _send(card)


def send_failure_card(
    fix_id: str,
    error_type: str,
    root_cause: str,
    reason: str,
) -> dict:
    card = _build_card(
        title="⚠️ Agent 自动修复失败",
        status="failed",
        fix_id=fix_id,
        error_type=error_type,
        root_cause=root_cause,
        reason=reason,
    )
    return _send(card)


def _build_card(
    title: str,
    status: str,
    fix_id: str = "",
    error_type: str = "",
    root_cause: str = "",
    branch: str = "",
    pr_url: str = "",
    changed_files: list[str] | None = None,
    reason: str = "",
) -> dict:
    elements = []

    if fix_id:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**修复ID**: {fix_id}"}})
    if error_type:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**错误类型**: {error_type}"}})
    if root_cause:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**根因分析**: {root_cause}"}})
    if branch:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**修复分支**: {branch}"}})
    if pr_url:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**PR链接**: [查看PR]({pr_url})"}})
    if changed_files:
        files_str = "\n".join(f"  - `{f}`" for f in changed_files)
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**变更文件**:\n{files_str}"}})
    if reason:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**失败原因**: {reason}"}})

    color = "green" if status == "success" else "red"
    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color,
            },
            "elements": elements,
        },
    }


def _send(card: dict) -> dict:
    mode = FEISHU_NOTIFY_MODE
    if mode == "webhook":
        return _send_via_webhook(card)
    elif mode == "cli":
        return _send_via_cli(card)
    else:
        return {"success": False, "error": f"Unknown FEISHU_NOTIFY_MODE: {mode}"}


def _send_via_webhook(card: dict) -> dict:
    url = FEISHU_WEBHOOK_URL
    if not url:
        return {"success": False, "error": "FEISHU_WEBHOOK_URL not configured"}

    try:
        resp = requests.post(url, json=card, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code", -1) == 0:
            return {"success": True, "response": data}
        return {"success": False, "error": data.get("msg", "Unknown error"), "response": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _send_via_cli(card: dict) -> dict:
    return {"success": False, "error": "CLI mode not yet implemented"}
