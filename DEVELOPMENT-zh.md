# Agent 自动化修复系统开发文档（中文版）

## 1. 项目概述

### 1.1 背景
线上服务出现问题时，常见流程是人工查看日志、定位原因、修改代码、运行测试、提交 PR、再通知相关开发者。这个流程重复度高、耗时长、且容易受个人经验影响。

本项目目标是构建一个基于 Agent 的自动化修复系统。当 Web 服务出现报错（或出现新的 Bug 提交）时，Agent 能自动完成以下动作：

1. 读取 Traceback 日志及上下文。
2. 调用大模型分析根因。
3. 生成并应用修复补丁。
4. 运行测试验证修复。
5. 自动创建分支、提交 Commit、发起 PR。
6. 通过飞书卡片通知开发者：
   “我发现了一个 Bug 并已为您修复，请 Review。”

### 1.2 项目目标
- 交付一个可运行的 MVP，能自动修复常见后端错误。
- 让每次修复过程可追溯、可审计、可复现。
- 演示从“报错触发”到“飞书通知”的完整闭环。

### 1.3 MVP 非目标
- 不追求一次性实现生产级多服务治理平台。
- 不实现“自动合并到主干”。
- 不追求覆盖所有错误类型（优先处理 traceback 明确的常见问题）。

## 2. Agent 在最终展示中的形态

本项目中的 Agent 主体是一个后台自动化服务（CLI + 定时/常驻运行），不是必须做成网页，也不是必须做成 IDE 插件。

演示时的可视化载体：
- 终端：展示 Agent 执行过程。
- GitHub PR 页面：展示自动修复结果。
- 飞书消息卡片：展示修复完成通知。

可选增强（非 MVP 必需）：
- 轻量 Web Dashboard（修复记录看板）。
- 平台插件化封装（后续扩展）。

## 3. 范围与验收标准

### 3.1 范围（In Scope）
- 监控 Bug 信号来源：
  - 服务 traceback 日志文件。
  - 新增 Bug Issue 事件（可作为 MVP+）。
- 具备 Tool Use 能力：
  - `Read Log`
  - `Read Code`
  - `Run Test`
  - `Git Commit / Create PR`
- 自动生成并应用修复补丁。
- 落库修复记录。
- 飞书通知。

### 3.2 验收标准（MVP）
满足以下条件即视为通过：
- 至少 3 种预置 Bug 场景可端到端自动修复。
- 修复补丁可通过测试命令校验。
- Agent 自动完成分支、Commit、PR。
- 飞书收到结构化通知卡片（包含 PR 链接）。
- 每次执行均产生结构化修复记录。

## 4. 建议目录结构

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
      feishu_cli.py
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
  DEVELOPMENT-zh.md
```

## 5. 系统架构与流程

### 5.1 主流程
1. 触发事件到达（日志报错或 issue 事件）。
2. Agent 读取 traceback 并提取关键字段。
3. Agent 读取相关源码和测试上下文。
4. 调用大模型输出：根因分析 + 修复补丁（unified diff）。
5. 在工作区应用补丁。
6. 运行测试验证。
7. 若测试通过：
   - 创建修复分支
   - 提交 Commit
   - 推送并创建 PR
   - 发送飞书通知
8. 记录执行结果到 `agent/records/fixes.jsonl`。

### 5.2 失败处理策略
- 补丁应用失败：标记失败并保留中间产物，等待人工介入。
- 测试失败：禁止创建 PR，通知“需人工处理”。
- GitHub/飞书调用失败：记录重试状态，不丢失修复上下文。

## 6. 核心模块设计

### 6.1 `agent/main.py`
- Agent 启动入口。
- 支持模式：
  - 单次执行（`--once`）
  - 持续监听（`--watch`）

### 6.2 `agent/workflows/fix_from_traceback.py`
- traceback 解析。
- 候选文件定位。
- 工具调度与修复循环编排。

### 6.3 `agent/llm.py`
- 封装大模型调用与工具调用闭环。
- 输入：
  - traceback 摘要
  - 相关代码片段
  - 测试命令
  - 修复约束
- 输出：
  - 根因分析
  - 补丁 diff
  - 置信度（可选）

### 6.4 工具层（`agent/tools/`）
- `read_log.py`：读取/追踪日志。
- `read_code.py`：按路径、范围、关键字获取代码上下文。
- `run_test.py`：执行测试并解析结果。
- `git_ops.py`：分支、提交、推送、创建 PR。
- `notify_feishu.py`：飞书通知入口（统一封装）。
- `feishu_cli.py`：飞书 CLI 适配层（可选增强）。

### 6.5 修复记录（`agent/records/fixes.jsonl`）
每次修复写入一条结构化记录，例如：

```json
{
  "id": "fix-20260430-001",
  "time": "2026-04-30T10:00:00+08:00",
  "source": "traceback_log",
  "error_type": "KeyError",
  "root_cause": "request payload 缺失关键字段校验",
  "changed_files": ["demo_service/app.py", "demo_service/tests/test_app.py"],
  "test_result": "passed",
  "branch": "agent/fix-20260430-001",
  "pr_url": "https://github.com/org/repo/pull/123",
  "feishu_notified": true,
  "notify_mode": "webhook",
  "status": "success"
}
```

## 7. 外部集成设计

### 7.1 大模型（LLM）
- 使用 OpenAI API 的工具调用模式。
- 通过环境变量配置模型名和密钥。

### 7.2 GitHub
- 使用 Token + REST API（或 `gh` CLI）创建 PR。
- 分支命名规范：
  - `agent/fix-<timestamp-or-id>`

### 7.3 飞书（Webhook 与 CLI 双模式）

#### 7.3.1 推荐策略
- MVP 默认：`Webhook` 作为主通知通道。
- 增强能力：`lark-cli` 作为可选扩展通道。

原因：
- Webhook 依赖少，适合服务端自动化与 CI。
- CLI 能力更丰富，适合后续扩展（文档、多维表、复杂组织内流程）。

#### 7.3.2 发送模式
- `webhook`：直接向机器人地址发送卡片 JSON。
- `cli`：通过飞书官方 CLI 调用消息能力发送通知。

#### 7.3.3 通知类型
- `success`：自动修复成功并已创建 PR。
- `failed`：自动修复失败，需人工介入。

## 8. 配置项设计

从 `.env.example` 复制生成 `.env`，至少包含：

```env
OPENAI_API_KEY=
OPENAI_MODEL=
GITHUB_TOKEN=
GITHUB_REPO=owner/repo

FEISHU_NOTIFY_MODE=webhook
FEISHU_WEBHOOK_URL=
FEISHU_CHAT_ID=
FEISHU_CLI_BIN=lark-cli
FEISHU_IDENTITY=bot

TEST_COMMAND=pytest demo_service/tests -q
LOG_PATH=demo_service/logs/error.log
```

说明：
- `FEISHU_NOTIFY_MODE` 取值：`webhook` 或 `cli`。
- `webhook` 模式必须配置 `FEISHU_WEBHOOK_URL`。
- `cli` 模式必须保证本机可执行 `lark-cli` 且完成认证。

## 9. 双人开发分工

### 9.1 开发者 A：Demo 服务与验证体系
- 实现 `demo_service`，构造 3-4 类可控 Bug。
- 完成测试套件与统一测试命令。
- 实现触发脚本 `scripts/trigger_bug.py`。
- 负责演示素材、场景稳定性和复现实验。

### 9.2 开发者 B：Agent 核心与外部集成
- 实现 Agent 工作流与工具层。
- 实现 LLM 驱动的修复补丁闭环。
- 集成 GitHub PR 自动化。
- 集成飞书 Webhook/CLI 通知。
- 落地修复记录机制。

### 9.3 联合里程碑（建议）
1. Day 1：服务 + 单一 Bug + Agent 骨架。
2. Day 2：补丁闭环 + 测试校验。
3. Day 3：PR 自动化 + 飞书通知。
4. Day 4：联调演练 + 录制演示视频。

## 10. 测试与验收计划

### 10.1 功能测试
每个预置 Bug 场景均验证：
- traceback 被正确采集。
- 补丁可成功生成并应用。
- 测试通过。
- PR 成功创建。
- 飞书通知成功发送。

### 10.2 异常测试
- 日志损坏或格式异常。
- 补丁冲突导致无法应用。
- 补丁后测试仍失败。
- GitHub API 失败。
- 飞书请求超时或鉴权失败。

### 10.3 验收清单
- 端到端链路在演示环境可稳定复现。
- 修复记录完整且可追溯。
- PR 描述包含根因与测试证据。
- 视频完整展示“触发-修复-通知”全过程。

## 11. 演示视频脚本建议

1. 启动 Demo Web 服务。
2. 触发一个已知 Bug。
3. 展示日志中 traceback 生成。
4. 启动 Agent（或展示 watch 模式自动触发）。
5. 展示 Agent 执行路径：
   `read log -> analyze -> patch -> test -> commit -> PR -> notify`
6. 打开 GitHub PR，展示改动文件和说明。
7. 展示飞书卡片通知（含 PR 链接）。
8. 展示 `fixes.jsonl` 对应记录作为最终证据。

## 12. 实施约束与安全规则

- Agent 仅允许修改仓库根目录内文件。
- 单次修复最大改动文件数需设上限（MVP 建议 <= 5）。
- 测试未通过禁止创建 PR。
- 每次运行必须生成结构化记录。
- 默认保留人工 Review 作为最终合入关口。

## 13. 下一步实施顺序

1. 初始化项目骨架与 `.env.example`。
2. 实现 `demo_service`（先做 1 个 Bug + 测试）。
3. 实现最小 Agent 闭环：`read_log -> llm -> patch -> test`。
4. 接入 Git 分支/Commit/PR 自动化。
5. 接入飞书通知（先 webhook，后 cli 增强）。
6. 扩展到多 Bug 模板并加强容错能力。
