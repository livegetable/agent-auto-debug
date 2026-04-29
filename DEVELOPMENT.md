# Agent Auto-Debug System Development Document

## 1. Project Overview

### 1.1 Background
In online services, bug handling usually requires manual steps: reading logs, locating root cause, modifying code, running tests, creating a PR, and notifying developers. This process is repetitive and costly.

This project builds an Agent-based auto-repair system for a simple web service. When a runtime error occurs or a new bug issue is submitted, the Agent should:

1. Read traceback logs and context.
2. Analyze root cause with an LLM.
3. Generate and apply a code patch.
4. Run tests to verify the fix.
5. Create a Git branch, commit, and open a PR.
6. Send a Feishu card notification:
   "I found a bug and fixed it for you. Please review."

### 1.2 Goals
- Deliver a runnable MVP that can automatically repair common backend bugs.
- Ensure repair actions are traceable and reviewable.
- Produce a full demo workflow from bug trigger to Feishu notification.

### 1.3 Non-Goals (MVP)
- Full production-grade multi-service orchestration.
- Fully autonomous merge-to-main without human review.
- Handling all bug classes (focus on common traceback-driven issues).

## 2. Final Form of the Agent

The Agent is primarily a backend automation service (CLI + scheduler/daemon style), not necessarily a web page or IDE plugin.

Presentation layer in demo:
- Terminal output for Agent workflow.
- GitHub PR page for repair result.
- Feishu card for final notification.

Optional (not required for MVP):
- Lightweight web dashboard for repair history.
- Plugin packaging for future integration.

## 3. Scope and Success Criteria

### 3.1 In Scope
- Monitor bug signals from:
  - Service traceback log file.
  - New bug issue event (optional second trigger in MVP+).
- Tool-use capable Agent:
  - `Read Log`
  - `Read Code`
  - `Run Test`
  - `Git Commit` / `Create PR`
- Automatic patch generation and application.
- Repair record persistence.
- Feishu card notification.

### 3.2 Success Criteria
MVP is accepted when all conditions are met:
- At least 3 predefined bug scenarios can be auto-repaired end-to-end.
- Generated patch passes project tests.
- Agent creates branch + commit + PR automatically.
- Feishu receives a structured notification card with PR link.
- Repair record is persisted for each run.

## 4. Suggested Repository Structure

```text
agent-auto-debug/
  agent/
    main.py
    config.py
    llm.py
    prompts/
      repair_prompt.md
    tools/
      read_log.py
      read_code.py
      run_test.py
      git_ops.py
      notify_feishu.py
    workflows/
      fix_from_traceback.py
      fix_from_issue.py
    records/
      fixes.jsonl
  demo_service/
    app.py
    tests/
      test_app.py
    logs/
      error.log
  scripts/
    run_agent_once.py
    trigger_bug.py
  docs/
    demo-script.md
  .env.example
  README.md
  DEVELOPMENT.md
```

## 5. Architecture and Data Flow

### 5.1 High-Level Flow
1. Trigger detected (log error or issue event).
2. Agent loads traceback and extracts key fields.
3. Agent reads related code and tests.
4. Agent asks LLM for root-cause analysis + unified diff patch.
5. Agent applies patch in workspace.
6. Agent runs tests.
7. If tests pass:
   - create branch
   - commit changes
   - open PR
   - notify Feishu
8. Write repair record to `agent/records/fixes.jsonl`.

### 5.2 Failure Handling
- If patch apply fails: mark run as failed, keep artifacts for manual review.
- If tests fail: do not create PR, notify as "needs manual intervention".
- If GitHub/Feishu API fails: keep local commit and record retryable status.

## 6. Core Module Design

### 6.1 `agent/main.py`
- Agent entrypoint.
- Supports modes:
  - single run (`--once`)
  - watch mode (`--watch`)

### 6.2 `agent/workflows/fix_from_traceback.py`
- Parse traceback.
- Resolve candidate files and contexts.
- Orchestrate tool calls and repair loop.

### 6.3 `agent/llm.py`
- Encapsulate model invocation and tool-calling loop.
- Input:
  - traceback summary
  - selected code snippets
  - test command
  - constraints
- Output:
  - root cause analysis
  - patch (unified diff)
  - confidence score (optional)

### 6.4 Tool Layer (`agent/tools/`)
- `read_log.py`: read and tail error logs.
- `read_code.py`: fetch code snippets by path/range/search.
- `run_test.py`: execute configured test command and parse result.
- `git_ops.py`: create branch, commit, push, create PR via GitHub API.
- `notify_feishu.py`: send Feishu interactive card via webhook.

### 6.5 Records (`agent/records/fixes.jsonl`)
Each line stores one repair run, example:

```json
{
  "id": "fix-20260430-001",
  "time": "2026-04-30T10:00:00+08:00",
  "source": "traceback_log",
  "error_type": "KeyError",
  "root_cause": "missing key validation in request payload handling",
  "changed_files": ["demo_service/app.py", "demo_service/tests/test_app.py"],
  "test_result": "passed",
  "branch": "agent/fix-20260430-001",
  "pr_url": "https://github.com/org/repo/pull/123",
  "feishu_notified": true,
  "status": "success"
}
```

## 7. External Integrations

### 7.1 LLM
- Use OpenAI API with tool-calling pattern.
- Model and API key configured via environment variables.

### 7.2 GitHub
- Use GitHub token and REST API for PR creation.
- Branch naming convention:
  - `agent/fix-<timestamp-or-id>`

### 7.3 Feishu
- Use bot webhook to send card message.
- Notification types:
  - `success`: auto-fixed and PR opened.
  - `failed`: auto-fix failed, manual review required.

## 8. Configuration

Create `.env` from `.env.example` with at least:

```env
OPENAI_API_KEY=
OPENAI_MODEL=
GITHUB_TOKEN=
GITHUB_REPO=owner/repo
FEISHU_WEBHOOK_URL=
TEST_COMMAND=pytest demo_service/tests -q
LOG_PATH=demo_service/logs/error.log
```

## 9. Development Plan (Two Developers)

### 9.1 Developer A: Demo Service and Validation
- Build `demo_service` and inject 3-4 controllable bug scenarios.
- Implement test suite and a stable test command.
- Implement bug trigger script (`scripts/trigger_bug.py`).
- Prepare demo narrative and reproducible scenarios.

### 9.2 Developer B: Agent and Integrations
- Build Agent workflow and tool layer.
- Implement LLM-driven patch generation and apply loop.
- Integrate GitHub PR automation.
- Integrate Feishu card notifications.
- Persist structured repair records.

### 9.3 Joint Milestones
1. Day 1: service + single bug + skeleton Agent.
2. Day 2: LLM patch loop + test verification.
3. Day 3: GitHub PR + Feishu notification.
4. Day 4: end-to-end rehearsal + demo video recording.

## 10. Test and Acceptance Plan

### 10.1 Functional Tests
- Trigger each predefined bug and verify:
  - traceback captured
  - patch generated
  - tests pass
  - PR created
  - Feishu notified

### 10.2 Negative Tests
- Corrupted traceback log.
- Patch cannot be applied.
- Tests remain failing after patch.
- GitHub API failure.
- Feishu webhook timeout.

### 10.3 Acceptance Checklist
- End-to-end run succeeds in demo environment.
- Repair records are complete and readable.
- PR description includes root cause and test evidence.
- Video clearly demonstrates full workflow.

## 11. Demo Video Script (Recommended)

1. Start the demo web service.
2. Trigger a known bug with script/request.
3. Show traceback generated in log.
4. Run Agent (or show watch mode auto-trigger).
5. Show Agent steps in terminal:
   read log -> analyze -> patch -> test -> commit -> PR -> notify.
6. Open GitHub PR and show changed files.
7. Show Feishu card notification with PR link.
8. Show `fixes.jsonl` entry as final evidence.

## 12. Implementation Constraints and Safety Rules

- Agent must only modify files inside repository root.
- Max changed files per run should be limited (e.g., <= 5 in MVP).
- No PR if tests fail.
- Every run must produce a structured record.
- Human review remains mandatory before merge.

## 13. Next Step (Execution Order)

1. Initialize project skeleton and `.env.example`.
2. Implement `demo_service` with one bug + tests.
3. Implement minimal Agent loop (`read_log -> llm -> patch -> test`).
4. Add git/PR automation.
5. Add Feishu card notification.
6. Expand to multiple bug templates and improve robustness.
