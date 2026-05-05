import subprocess
import sys
from pathlib import Path
from agent.config import TEST_COMMAND


def run_test(test_command: str | None = None, cwd: str | None = None) -> dict:
    cmd = test_command or TEST_COMMAND
    base_dir = Path(cwd) if cwd else Path(__file__).resolve().parents[2]
    venv_python = base_dir / ".venv" / "Scripts" / "python.exe"

    candidate_commands: list[str] = []
    if venv_python.is_file():
        candidate_commands.append(f"\"{venv_python}\" -m {cmd}")
    candidate_commands.append(f"{sys.executable} -m {cmd}")
    candidate_commands.append(cmd)

    try:
        last_result = None
        for candidate_cmd in candidate_commands:
            result = subprocess.run(
                candidate_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=cwd,
                encoding="utf-8",
                errors="replace",
            )
            last_result = result
            stderr_lower = (result.stderr or "").lower()
            not_found = ("not recognized as an internal or external command" in stderr_lower) or ("不是内部或外部命令" in (result.stderr or ""))
            if result.returncode == 0 or not not_found:
                return {
                    "success": result.returncode == 0,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "command": candidate_cmd,
                }

        if last_result is None:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "No test command candidates generated",
                "command": cmd,
            }
        return {
            "success": last_result.returncode == 0,
            "returncode": last_result.returncode,
            "stdout": last_result.stdout,
            "stderr": last_result.stderr,
            "command": candidate_commands[-1],
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "Test command timed out after 120 seconds",
            "command": cmd,
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "command": cmd,
        }
