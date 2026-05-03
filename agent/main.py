import argparse
import time
import sys
from agent.tools.read_log import read_log, get_log_size, tail_log
from agent.workflows.fix_from_traceback import run_fix_workflow
from agent.workflows.fix_from_issue import run_fix_from_issue
from agent.config import LOG_PATH


def run_once(log_path: str | None = None) -> dict:
    print("[Agent] Running in single-shot mode...")
    result = run_fix_workflow(log_path)
    _print_result(result)
    return result


def run_watch(log_path: str | None = None, poll_interval: int = 10) -> None:
    print(f"[Agent] Running in watch mode (polling every {poll_interval}s)...")

    existing_log = read_log(log_path)
    if existing_log["success"] and existing_log["content"].strip():
        if "Traceback" in existing_log["content"] and ("Error" in existing_log["content"] or "Exception" in existing_log["content"]):
            print("[Agent] Found existing traceback in log, processing...")
            result = run_fix_workflow(log_path)
            _print_result(result)

    last_position = get_log_size(log_path)

    while True:
        try:
            new_data = tail_log(log_path, since_position=last_position)
            if new_data["success"] and new_data["content"].strip():
                last_position = new_data["position"]
                content = new_data["content"]

                if "Traceback" in content and ("Error" in content or "Exception" in content):
                    print("[Agent] New traceback detected in log!")
                    result = run_fix_workflow(log_path)
                    _print_result(result)

            time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\n[Agent] Watch mode stopped by user.")
            break
        except Exception as e:
            print(f"[Agent] Error in watch loop: {e}")
            time.sleep(poll_interval)


def run_from_issue(issue_text: str) -> dict:
    print("[Agent] Running in issue mode...")
    result = run_fix_from_issue(issue_text)
    _print_result(result)
    return result


def _print_result(result: dict) -> None:
    print("\n" + "=" * 60)
    print(f"  Fix ID: {result.get('id', 'N/A')}")
    print(f"  Status: {result.get('status', 'N/A')}")
    print(f"  Error Type: {result.get('error_type', 'N/A')}")
    print(f"  Root Cause: {result.get('root_cause', 'N/A')}")
    if result.get("changed_files"):
        print(f"  Changed Files: {', '.join(result['changed_files'])}")
    if result.get("branch"):
        print(f"  Branch: {result['branch']}")
    if result.get("pr_url"):
        print(f"  PR URL: {result['pr_url']}")
    print(f"  Feishu Notified: {result.get('feishu_notified', False)}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Agent Auto-Debug System")
    parser.add_argument("--once", action="store_true", help="Run agent once and exit")
    parser.add_argument("--watch", action="store_true", help="Watch log file for new errors")
    parser.add_argument("--issue", type=str, help="Fix from issue description text")
    parser.add_argument("--log-path", type=str, default=None, help="Path to error log file")
    parser.add_argument("--poll-interval", type=int, default=10, help="Poll interval in seconds for watch mode")

    args = parser.parse_args()

    if args.issue:
        run_from_issue(args.issue)
    elif args.watch:
        run_watch(args.log_path, args.poll_interval)
    elif args.once:
        run_once(args.log_path)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
