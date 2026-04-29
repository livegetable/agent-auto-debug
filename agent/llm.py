import json
import re
from pathlib import Path
from openai import OpenAI
from agent.config import OPENAI_API_KEY, OPENAI_MODEL, PROJECT_ROOT

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "repair_prompt.md"


def load_system_prompt() -> str:
    if PROMPT_PATH.is_file():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return "You are a bug repair agent. Analyze the error and generate a fix."


def analyze_and_fix(
    traceback_text: str,
    code_context: dict[str, str],
    test_command: str = "",
    constraints: str = "",
    max_retries: int = 2,
) -> dict:
    client = OpenAI(api_key=OPENAI_API_KEY)
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
{constraints if constraints else 'No additional constraints.'}

Please analyze the root cause and generate a unified diff patch to fix the bug."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            result = _parse_response(content)
            if result:
                return result
        except Exception as e:
            if attempt < max_retries:
                messages.append({"role": "assistant", "content": str(e)})
                messages.append({
                    "role": "user",
                    "content": "The previous response was invalid. Please try again with valid JSON output.",
                })
                continue
            return {
                "root_cause": f"LLM call failed: {str(e)}",
                "error_type": "Unknown",
                "patch": "",
                "changed_files": [],
                "confidence": 0.0,
                "explanation": f"Failed after {max_retries + 1} attempts",
            }

    return {
        "root_cause": "Failed to get valid response from LLM",
        "error_type": "Unknown",
        "patch": "",
        "changed_files": [],
        "confidence": 0.0,
        "explanation": "No valid response",
    }


def _parse_response(content: str) -> dict | None:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return _try_extract_json(content)

    required = ["root_cause", "patch", "changed_files"]
    if not all(k in data for k in required):
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
    if json_match:
        try:
            return _parse_response(json_match.group())
        except Exception:
            pass
    return None
