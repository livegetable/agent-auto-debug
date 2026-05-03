from __future__ import annotations

from typing import Any

from openai import OpenAI

from agent.config import (
    FEISHU_NOTIFY_MODE,
    FEISHU_WEBHOOK_URL,
    GITHUB_REPO,
    GITHUB_TOKEN,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)


def run_preflight_checks() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    has_error = False

    checks.append({"name": "OPENAI_API_KEY", "ok": bool(OPENAI_API_KEY), "message": "已配置" if OPENAI_API_KEY else "未配置"})
    checks.append({"name": "OPENAI_MODEL", "ok": bool(OPENAI_MODEL), "message": f"当前模型: {OPENAI_MODEL}" if OPENAI_MODEL else "未配置"})
    checks.append({"name": "OPENAI_BASE_URL", "ok": True, "message": f"当前地址: {OPENAI_BASE_URL}" if OPENAI_BASE_URL else "使用官方默认地址"})
    if not OPENAI_API_KEY or not OPENAI_MODEL:
        has_error = True

    llm_ok, llm_msg = _check_llm_connectivity()
    checks.append({"name": "LLM 连通性", "ok": llm_ok, "message": llm_msg})
    if not llm_ok:
        has_error = True

    gh_ok = bool(GITHUB_TOKEN and GITHUB_REPO)
    checks.append({"name": "GitHub 自动化", "ok": gh_ok, "message": "已配置，支持 push/PR" if gh_ok else "未完整配置，将跳过 push/PR"})

    feishu_ok = True
    feishu_msg = "已配置"
    if FEISHU_NOTIFY_MODE == "webhook":
        if (not FEISHU_WEBHOOK_URL) or ("your-hook-id" in FEISHU_WEBHOOK_URL):
            feishu_ok = False
            feishu_msg = "webhook 模式但 FEISHU_WEBHOOK_URL 未配置为真实地址"
    checks.append({"name": "飞书通知", "ok": feishu_ok, "message": feishu_msg})

    return {"ok": not has_error, "checks": checks}


def _check_llm_connectivity() -> tuple[bool, str]:
    try:
        kwargs = {"api_key": OPENAI_API_KEY}
        if OPENAI_BASE_URL:
            kwargs["base_url"] = OPENAI_BASE_URL
        client = OpenAI(**kwargs)
        client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
            temperature=0,
        )
        return True, "连接成功"
    except Exception as error:
        return False, f"连接失败: {error}"
