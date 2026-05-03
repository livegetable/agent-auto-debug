import json
import re
from pathlib import Path

from openai import OpenAI

from agent.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "repair_prompt.md"


def load_system_prompt() -> str:
    if PROMPT_PATH.is_file():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return "你是一个缺陷修复助手，请分析错误并生成修复补丁。"


def analyze_and_fix(
    traceback_text: str,
    code_context: dict[str, str],
    test_command: str = "",
    constraints: str = "",
    max_retries: int = 2,
) -> dict:
    client_kwargs = {"api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        client_kwargs["base_url"] = OPENAI_BASE_URL
    client = OpenAI(**client_kwargs)
    system_prompt = load_system_prompt()

    code_sections = []
    for file_path, content in code_context.items():
        code_sections.append(f"### File: {file_path}\n```\n{content}\n```")
    code_block = "\n\n".join(code_sections)

    user_message = f"""## Traceback
```
{traceback_text}
```

## Code Context
{code_block}

## Test Command
`{test_command}`

## Constraints
{constraints if constraints else "No additional constraints."}

请分析根因并生成 unified diff 补丁。
注意：`root_cause` 与 `explanation` 必须使用中文，且只输出一个 JSON 对象。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    for attempt in range(max_retries + 1):
        try:
            content = _request_llm_content(client, messages)
            result = _parse_response(content)
            if result:
                return result

            if attempt < max_retries:
                messages.append({"role": "assistant", "content": (content or "")[:4000]})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "你上一次输出不是可解析 JSON。"
                            "请只输出一个 JSON 对象，并确保包含 root_cause、patch、changed_files。"
                        ),
                    }
                )
                continue

            return {
                "root_cause": "LLM 返回内容无法解析为期望 JSON",
                "error_type": "Unknown",
                "patch": "",
                "changed_files": [],
                "confidence": 0.0,
                "explanation": f"原始返回（截断）: {(content or '')[:300]}",
            }
        except Exception as error:
            if attempt < max_retries:
                messages.append({"role": "assistant", "content": str(error)})
                messages.append({"role": "user", "content": "上一轮调用失败，请重试并严格输出 JSON。"})
                continue
            return {
                "root_cause": f"LLM 调用失败: {error}",
                "error_type": "Unknown",
                "patch": "",
                "changed_files": [],
                "confidence": 0.0,
                "explanation": f"重试 {max_retries + 1} 次后失败",
            }

    return {
        "root_cause": "未获取到有效 LLM 响应",
        "error_type": "Unknown",
        "patch": "",
        "changed_files": [],
        "confidence": 0.0,
        "explanation": "无有效响应",
    }


def _request_llm_content(client: OpenAI, messages: list[dict]) -> str:
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.1,
    )
    return response.choices[0].message.content or ""


def _parse_response(content: str) -> dict | None:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return _try_extract_json(content)

    required = ["root_cause", "patch", "changed_files"]
    if not all(key in data for key in required):
        return None

    return {
        "root_cause": data.get("root_cause", ""),
        "error_type": data.get("error_type", "Unknown"),
        "patch": data.get("patch", ""),
        "changed_files": data.get("changed_files", []),
        "confidence": float(data.get("confidence", 0.5)),
        "explanation": data.get("explanation", ""),
    }


def _try_extract_json(content: str) -> dict | None:
    json_match = re.search(r"\{[\s\S]*\}", content)
    if not json_match:
        return None
    try:
        return _parse_response(json_match.group())
    except Exception:
        return None
