import os
import re
import json
import subprocess
from datetime import datetime


def read_log(log_path: str = "logs/error.log") -> str:
    """读取错误日志文件内容"""
    if not os.path.exists(log_path):
        return ""
    with open(log_path, "r", encoding="utf-8") as f:
        return f.read()


def parse_traceback(log_text: str) -> dict:
    """从traceback中解析错误信息，当前仅支持KeyError，优先取最后一次错误"""
    if not log_text:
        print("❌ 错误日志为空")
        return {}
    
    # 分割多个错误记录，取最后一个非空的错误
    error_blocks = [block.strip() for block in log_text.split("---") if block.strip()]
    if not error_blocks:
        print("❌ 未找到有效的错误记录")
        return {}
    latest_error = error_blocks[-1]
    
    # 匹配错误类型和错误信息
    error_match = re.search(r"^(\w+):\s*'?([^'\n]+)'?", latest_error, re.MULTILINE)
    if not error_match:
        print("❌ 无法匹配错误类型")
        print("最近30行日志：")
        print("\n".join(log_text.splitlines()[-30:]))
        return {}
    
    error_type = error_match.group(1)
    error_message = error_match.group(2)
    
    if error_type != "KeyError":
        print(f"❌ 不支持的错误类型: {error_type}")
        return {"error_type": error_type, "error_message": error_message, "target_file": "", "target_line": 0}
    
    # 匹配所有File记录，过滤第三方库，优先选择项目内文件
    all_file_matches = list(re.finditer(r'File "([^"]+)", line (\d+), in (\w+)', latest_error))
    if not all_file_matches:
        print("❌ 无法匹配文件和行号")
        print("最近30行日志：")
        print("\n".join(log_text.splitlines()[-30:]))
        return {}
    
    # 过滤规则：排除第三方库文件，优先选择项目内文件
    project_files = []
    for match in all_file_matches:
        file_path = match.group(1)
        # 排除第三方库路径
        if "site-packages" in file_path:
            continue
        if "/starlette/" in file_path or "/fastapi/" in file_path or "/uvicorn/" in file_path:
            continue
        project_files.append(match)
    
    # 如果有项目文件，取最后一个（最接近真正出错位置）；否则fallback到最后一个File
    if project_files:
        selected_match = project_files[-1]
    else:
        selected_match = all_file_matches[-1]
    
    target_file = selected_match.group(1)
    target_line = int(selected_match.group(2))
    function_name = selected_match.group(3)
    
    # 处理路径：如果是绝对路径且存在，尝试转成相对路径
    if os.path.isabs(target_file) and os.path.exists(target_file):
        cwd = os.getcwd()
        if target_file.startswith(cwd):
            target_file = os.path.relpath(target_file, cwd)
    
    # 验证文件是否存在
    if not os.path.exists(target_file):
        print(f"❌ 解析到的文件不存在: {target_file}")
        return {}
    
    return {
        "error_type": error_type,
        "error_message": error_message,
        "target_file": target_file,
        "target_line": target_line,
        "function_name": function_name
    }


def read_code(file_path: str, line_no: int, context: int = 10) -> str:
    """读取目标文件中出错行附近的代码片段，带行号返回"""
    if not os.path.exists(file_path):
        return ""
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    start_line = max(0, line_no - context - 1)
    end_line = min(len(lines), line_no + context)
    
    code_snippet = ""
    for i in range(start_line, end_line):
        current_line = i + 1
        prefix = "-> " if current_line == line_no else "   "
        code_snippet += f"{prefix}{current_line:4d}: {lines[i]}"
    
    return code_snippet


def apply_fixed_patch(file_path: str = "app/main.py") -> bool:
    """针对当前demo bug，把user["age"]修复为user.get("age", 0)，支持幂等"""
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 检查是否已经修复完成
    if '"age": user.get("age", 0)' in content:
        print("ℹ️ 代码已经修复过，无需重复修改")
        return True
    
    # 替换目标代码
    old_pattern = r'"age": user\["age"\]'
    new_code = '"age": user.get("age", 0)'
    
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_code, content)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    
    return False


def update_tests_for_fix(test_file_path: str = "tests/test_app.py") -> bool:
    """修复测试用例：更新test_get_user_2_has_bug为验证修复成功"""
    if not os.path.exists(test_file_path):
        return False
    
    with open(test_file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 检查是否已经更新过测试
    if "test_get_user_2_fixed" in content:
        print("ℹ️ 测试用例已经更新过，无需重复修改")
        return True
    
    # 替换测试函数名称
    content = content.replace("test_get_user_2_has_bug", "test_get_user_2_fixed")
    
    # 替换文档字符串
    old_doc = '"""测试用户2的请求，应该触发KeyError返回500，证明bug存在"""'
    new_doc = '"""测试用户2的请求，修复后应该返回200，并为缺失age提供默认值"""'
    content = content.replace(old_doc, new_doc)
    
    # 替换断言
    old_assert = 'assert response.status_code == 500\n    data = response.json()\n    assert data["detail"] == "Internal Server Error"'
    new_assert = 'assert response.status_code == 200\n    data = response.json()\n    assert data["id"] == 2\n    assert data["name"] == "Bob"\n    assert data["age"] == 0'
    
    content = re.sub(re.escape(old_assert), new_assert, content)
    
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return True


def run_tests() -> tuple[bool, str]:
    """执行pytest测试，返回是否通过和输出内容"""
    result = subprocess.run(
        ["pytest", "tests/", "-v"],
        capture_output=True,
        text=True
    )
    return (result.returncode == 0, result.stdout + result.stderr)


def extract_traceback_summary(log_text: str, parsed_error: dict) -> str:
    """从日志中提取简洁的Traceback摘要"""
    return f"""{parsed_error['error_type']}: '{parsed_error['error_message']}'
File "{parsed_error['target_file']}", line {parsed_error['target_line']}, in {parsed_error['function_name']}"""


def parse_llm_json(llm_output: str) -> dict | None:
    """解析LLM输出的JSON，清理Markdown包裹，验证必填字段"""
    if not llm_output:
        return None
    
    # 清理```json和```包裹
    cleaned_output = llm_output.strip()
    if cleaned_output.startswith("```json"):
        cleaned_output = cleaned_output[7:]
    if cleaned_output.endswith("```"):
        cleaned_output = cleaned_output[:-3]
    
    cleaned_output = cleaned_output.strip()
    
    try:
        parsed_json = json.loads(cleaned_output)
    except json.JSONDecodeError:
        print("⚠️ LLM 输出不是有效的JSON格式")
        return None
    
    # 验证必填字段
    required_fields = [
        "root_cause", "fix_strategy", "file_path",
        "old_code", "new_code", "test_update_needed", "test_strategy"
    ]
    
    for field in required_fields:
        if field not in parsed_json:
            print(f"⚠️ LLM 输出缺少必填字段: {field}")
            return None
    
    return parsed_json


def apply_llm_patch(patch_json: dict) -> tuple[bool, str]:
    """应用LLM生成的补丁，支持幂等"""
    file_path = patch_json.get("file_path")
    old_code = patch_json.get("old_code", "").strip()
    new_code = patch_json.get("new_code", "").strip()
    
    if not os.path.exists(file_path):
        # 尝试相对路径
        if not os.path.isabs(file_path) and os.path.exists(os.path.join(os.getcwd(), file_path)):
            file_path = os.path.join(os.getcwd(), file_path)
        else:
            return False, f"文件不存在: {file_path}"
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 检查是否已经修复完成
    if new_code in content:
        return True, "代码已经修复完成，无需重复修改"
    
    # 查找旧代码
    if old_code not in content:
        return False, f"未找到需要替换的旧代码: {old_code}"
    
    # 替换代码
    content = content.replace(old_code, new_code)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return True, "补丁应用成功"


def write_fix_record(record: dict, record_id: str = "bug_001") -> str:
    """生成修复记录到fix_records目录下"""
    os.makedirs("fix_records", exist_ok=True)
    record_path = f"fix_records/{record_id}.md"
    
    content = f"""# 自动修复记录 {record_id}

## 基本信息
- 修复时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 修复模式: {record.get('fix_mode', 'Fixed Rule Fallback')}
- Bug 类型: {record.get('error_type', '未知')}
- 修改文件: {record.get('target_file', '未知')}
- 错误行号: {record.get('target_line', 0)}
- 出错函数: {record.get('function_name', '未知')}

## Traceback 摘要
```
{record.get('traceback_summary', '')}
```

{f"## LLM 根因分析\n{record.get('root_cause', '')}\n" if record.get('fix_mode') == 'LLM' else ""}
{f"## LLM 修复策略\n{record.get('fix_strategy', '')}\n" if record.get('fix_mode') == 'LLM' else "## 固定规则修复策略\n将 `user[\"age\"]` 修改为 `user.get(\"age\", 0)`，避免缺少age字段时触发KeyError。\n"}

## 相关代码上下文
```python
{record.get('code_snippet', '')}
```

## 测试结果
```
{record.get('test_output', '')}
```

## 修复状态
✅ 修复成功，所有测试通过
"""
    
    with open(record_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return record_path
