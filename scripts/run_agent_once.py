import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.main import run_once


if __name__ == "__main__":
    log_path = sys.argv[1] if len(sys.argv) > 1 else None
    result = run_once(log_path)
    sys.exit(0 if result.get("status") == "success" else 1)
