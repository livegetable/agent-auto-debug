import os
import time
import signal
from typing import Optional
from .main import main as agent_main


def ensure_log_file(log_path: str = "logs/error.log") -> None:
    """确保日志文件存在，不存在则创建"""
    log_dir = os.path.dirname(log_path)
    os.makedirs(log_dir, exist_ok=True)
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("")
        print(f"ℹ️ {log_path} 不存在，已自动创建")


def should_trigger_autofix(new_content: str) -> bool:
    """判断新日志内容是否需要触发自动修复"""
    if not new_content.strip():
        return False
    
    # 检查是否包含Traceback
    if "Traceback (most recent call last)" not in new_content:
        return False
    
    # 检查是否包含支持的错误类型
    error_types = ["KeyError", "TypeError", "ValueError", "AttributeError", "ZeroDivisionError", "Exception"]
    for error_type in error_types:
        if error_type in new_content:
            return True
    
    return False


def read_new_content(log_path: str, last_size: int) -> tuple[str, int]:
    """从指定位置读取新增的日志内容"""
    current_size = os.path.getsize(log_path)
    if current_size <= last_size:
        return "", current_size
    
    with open(log_path, "r", encoding="utf-8") as f:
        f.seek(last_size)
        new_content = f.read()
    
    return new_content, current_size


def main(poll_interval: int = 2):
    """Watcher主函数"""
    log_path = "logs/error.log"
    is_running = False
    last_file_size = 0
    
    # 优雅退出处理
    def signal_handler(signum, frame):
        print("\n👋 AutoFix Watcher stopped")
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # 确保日志文件存在
    ensure_log_file(log_path)
    last_file_size = os.path.getsize(log_path)
    
    print("👀 AutoFix Watcher started")
    print(f"Watching: {log_path}")
    print("Press Ctrl+C to stop")
    
    while True:
        try:
            if not is_running:
                new_content, last_file_size = read_new_content(log_path, last_file_size)
                
                if should_trigger_autofix(new_content):
                    print("\n🔍 检测到新的错误日志，触发自动修复...")
                    is_running = True
                    
                    try:
                        # 调用Agent主流程
                        agent_main()
                    except Exception as e:
                        print(f"⚠️ Agent 运行失败: {str(e)}")
                    finally:
                        is_running = False
                        # 重置文件大小，避免重复处理
                        last_file_size = os.path.getsize(log_path)
            
            time.sleep(poll_interval)
        
        except Exception as e:
            print(f"⚠️ Watcher error: {str(e)}")
            time.sleep(poll_interval)


if __name__ == "__main__":
    main()
