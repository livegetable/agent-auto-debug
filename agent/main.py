import argparse
import sys
import time

from agent.preflight import run_preflight_checks
from agent.tools.read_log import get_log_size, read_log, tail_log
from agent.workflows.fix_from_issue import run_fix_from_issue
from agent.workflows.fix_from_traceback import run_fix_workflow


def run_once(log_path: str | None = None) -> dict:
    print("[Agent] 单次执行模式启动...")
    result = run_fix_workflow(log_path)
    _print_result(result)
    return result


def run_watch(log_path: str | None = None, poll_interval: int = 10) -> None:
    print(f"[Agent] 监控模式启动（每 {poll_interval} 秒轮询）...")

    existing_log = read_log(log_path)
    if existing_log["success"] and existing_log["content"].strip():
        if "Traceback" in existing_log["content"] and (
            "Error" in existing_log["content"] or "Exception" in existing_log["content"]
        ):
            print("[Agent] 检测到历史 traceback，开始处理...")
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
                    print("[Agent] 检测到新的 traceback！")
                    result = run_fix_workflow(log_path)
                    _print_result(result)

            time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\n[Agent] 已停止监控模式。")
            break
        except Exception as error:
            print(f"[Agent] 监控循环异常: {error}")
            time.sleep(poll_interval)


def run_from_issue(issue_text: str) -> dict:
    print("[Agent] Issue 修复模式启动...")
    result = run_fix_from_issue(issue_text)
    _print_result(result)
    return result


def _print_result(result: dict) -> None:
    print("\n" + "=" * 60)
    print(f"  修复ID: {result.get('id', 'N/A')}")
    print(f"  状态: {result.get('status', 'N/A')}")
    print(f"  错误类型: {result.get('error_type', 'N/A')}")
    print(f"  根因: {result.get('root_cause', 'N/A')}")
    if result.get("changed_files"):
        print(f"  变更文件: {', '.join(result['changed_files'])}")
    if result.get("branch"):
        print(f"  分支: {result['branch']}")
    if result.get("pr_url"):
        print(f"  PR链接: {result['pr_url']}")
    print(f"  飞书通知: {result.get('feishu_notified', False)}")
    print("=" * 60 + "\n")


def _print_preflight_report(report: dict) -> None:
    print("\n[Agent] 启动前自检结果：")
    warning_count = 0
    for item in report["checks"]:
        status = "通过" if item["ok"] else "失败"
        if not item["ok"]:
            warning_count += 1
        print(f"  - {item['name']}: {status}（{item['message']}）")
    if report["ok"]:
        if warning_count:
            print("[Agent] 关键项通过，存在非阻断告警，继续执行。\n")
        else:
            print("[Agent] 自检通过，继续执行。\n")
    else:
        print("[Agent] 自检未通过，已停止执行。请先修复配置后重试。\n")


def main():
    parser = argparse.ArgumentParser(description="Agent 自动修复系统")
    parser.add_argument("--once", action="store_true", help="执行一次后退出")
    parser.add_argument("--watch", action="store_true", help="监控日志中的新错误")
    parser.add_argument("--issue", type=str, help="根据 issue 文本执行修复")
    parser.add_argument("--log-path", type=str, default=None, help="错误日志路径")
    parser.add_argument("--poll-interval", type=int, default=10, help="监控模式轮询秒数")
    parser.add_argument("--skip-preflight", action="store_true", help="跳过启动前自检")

    args = parser.parse_args()

    if not args.skip_preflight:
        report = run_preflight_checks()
        _print_preflight_report(report)
        if not report["ok"]:
            sys.exit(2)

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
