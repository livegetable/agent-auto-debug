FIX_PROMPT = """你是专业的代码修复助手，请根据以下错误信息和代码上下文，生成精准的修复方案。

## 错误信息
- 错误类型: {error_type}
- 错误信息: {error_message}
- 目标文件: {target_file}
- 出错行号: {target_line}
- 出错函数: {function_name}

## Traceback 摘要
```
{traceback_summary}
```

## 代码上下文（包含出错行前后）
```python
{code_context}
```

## 要求
1. 分析bug根因，给出修复方案
2. 输出必须是严格的JSON格式，不要输出任何Markdown、解释性文字或其他内容
3. JSON必须包含以下所有字段，不要遗漏：
   - root_cause: 字符串，说明bug的根本原因
   - fix_strategy: 字符串，说明具体的修复策略
   - file_path: 字符串，需要修改的文件路径（和目标文件一致）
   - old_code: 字符串，需要被替换的旧代码片段，必须和代码上下文中的完全一致
   - new_code: 字符串，替换后的新代码片段
   - test_update_needed: 布尔值，是否需要更新测试用例
   - test_strategy: 字符串，说明如何通过测试验证修复成功

## 输出示例
```json
{{
  "root_cause": "The code directly accesses user[\"age\"], but user 2 does not contain the age field, causing KeyError.",
  "fix_strategy": "Use user.get(\"age\", 0) to provide a default value when age is missing.",
  "file_path": "app/main.py",
  "old_code": "\"age\": user[\"age\"]",
  "new_code": "\"age\": user.get(\"age\", 0)",
  "test_update_needed": true,
  "test_strategy": "The /users/2 endpoint should return 200 and age should be 0."
}}
```

现在请输出修复方案JSON:
"""
