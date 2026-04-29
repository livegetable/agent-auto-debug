import json
import subprocess
import os
from agent.config import FEISHU_CLI_BIN, FEISHU_CHAT_ID, FEISHU_IDENTITY


def send_card_via_cli(card_json: dict, chat_id: str | None = None) -> dict:
    target_chat = chat_id or FEISHU_CHAT_ID
    if not target_chat:
        return {"success": False, "error": "FEISHU_CHAT_ID not configured"}

    try:
        card_str = json.dumps(card_json, ensure_ascii=False)
        cmd = [
            FEISHU_CLI_BIN,
            "message",
            "send",
            "--chat", target_chat,
            "--identity", FEISHU_IDENTITY,
            "--card", card_str,
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        return {"success": False, "error": result.stderr, "output": result.stdout}
    except FileNotFoundError:
        return {"success": False, "error": f"CLI binary not found: {FEISHU_CLI_BIN}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "CLI command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_cli_available() -> bool:
    try:
        result = subprocess.run(
            [FEISHU_CLI_BIN, "--version"],
            capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False
