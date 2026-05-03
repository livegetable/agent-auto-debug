import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")

FEISHU_NOTIFY_MODE = os.environ.get("FEISHU_NOTIFY_MODE", "webhook")
FEISHU_WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL", "")
FEISHU_CHAT_ID = os.environ.get("FEISHU_CHAT_ID", "")
FEISHU_CLI_BIN = os.environ.get("FEISHU_CLI_BIN", "lark-cli")
FEISHU_IDENTITY = os.environ.get("FEISHU_IDENTITY", "bot")

TEST_COMMAND = os.environ.get("TEST_COMMAND", "pytest demo_service/tests -q")
LOG_PATH = os.environ.get("LOG_PATH", str(PROJECT_ROOT / "demo_service" / "logs" / "error.log"))

RECORDS_PATH = PROJECT_ROOT / "agent" / "records" / "fixes.jsonl"

MAX_CHANGED_FILES = int(os.environ.get("MAX_CHANGED_FILES", "5"))

BRANCH_PREFIX = "agent/fix"
