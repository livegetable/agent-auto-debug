from agent.tools import parse_traceback, parse_llm_json


def test_parse_traceback_skip_third_party():
    """测试parse_traceback能跳过第三方库路径，优先定位项目代码"""
    mock_log = """
Traceback (most recent call last):
  File "/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, send)
  File "/usr/local/lib/python3.11/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/Users/chancie/Documents/trae_projects/agent-auto-debug/app/main.py", line 49, in get_user
    "age": user["age"]
KeyError: 'age'
"""
    result = parse_traceback(mock_log)
    assert result["error_type"] == "KeyError"
    assert "app/main.py" in result["target_file"]
    assert result["target_line"] == 49
    assert result["function_name"] == "get_user"
    assert "site-packages" not in result["target_file"]
    assert "starlette" not in result["target_file"]
    assert "fastapi" not in result["target_file"]


def test_parse_traceback_direct():
    """测试parse_traceback在没有第三方库路径时正常解析"""
    mock_log = """
Traceback (most recent call last):
  File "app/main.py", line 49, in get_user
    "age": user["age"]
KeyError: 'age'
"""
    result = parse_traceback(mock_log)
    assert result["error_type"] == "KeyError"
    assert result["target_file"] == "app/main.py"
    assert result["target_line"] == 49
    assert result["function_name"] == "get_user"


def test_parse_llm_json_valid():
    """测试parse_llm_json能解析标准JSON字符串"""
    # 使用简单内容避免转义问题
    valid_json = '''
{
  "root_cause": "Missing age field",
  "fix_strategy": "Use get() method",
  "file_path": "app/main.py",
  "old_code": "user.age",
  "new_code": "user.get_age()",
  "test_update_needed": true,
  "test_strategy": "Check age is 0"
}
'''
    result = parse_llm_json(valid_json)
    assert result is not None
    assert result["root_cause"] == "Missing age field"
    assert result["fix_strategy"] == "Use get() method"
    assert result["file_path"] == "app/main.py"


def test_parse_llm_json_invalid():
    """测试parse_llm_json遇到非法JSON时返回None"""
    invalid_json = """
{
  "root_cause": "Missing age field",
  "fix_strategy": "Use get() method"
  # 缺少闭合括号
"""
    result = parse_llm_json(invalid_json)
    assert result is None


def test_parse_llm_json_with_markdown():
    """测试parse_llm_json能处理被```json包裹的JSON"""
    markdown_json = """```json
{
  "root_cause": "Missing age field",
  "fix_strategy": "Use get() method",
  "file_path": "app/main.py",
  "old_code": "user.age",
  "new_code": "user.get_age()",
  "test_update_needed": true,
  "test_strategy": "Check age is 0"
}
```
"""
    result = parse_llm_json(markdown_json)
    assert result is not None
    assert result["root_cause"] == "Missing age field"
    assert result["file_path"] == "app/main.py"


def test_parse_llm_json_missing_fields():
    """测试parse_llm_json遇到字段不完整的JSON返回None"""
    incomplete_json = """
{
  "root_cause": "Missing age field",
  "fix_strategy": "Use get() method"
}
"""
    result = parse_llm_json(incomplete_json)
    assert result is None
