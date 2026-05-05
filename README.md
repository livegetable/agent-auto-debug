# agent-auto-debug：基于Agent的Web服务自动化修复系统

## Environment Setup / 环境配置

⚠️ **重要说明**：不要直接使用系统Python全局安装依赖，不要使用`--break-system-packages`参数。请始终使用项目虚拟环境。

### 首次初始化虚拟环境
```bash
# 进入项目根目录
cd /Users/chancie/Documents/trae_projects/agent-auto-debug

# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 升级pip
python -m pip install --upgrade pip

# 安装项目依赖
python -m pip install -r requirements.txt
```

### 每次打开新Terminal后的操作
```bash
# 进入项目根目录
cd /Users/chancie/Documents/trae_projects/agent-auto-debug

# 激活虚拟环境
source .venv/bin/activate
```

## Run AutoFix Agent / 运行 Agent
```bash
# 确保已激活虚拟环境
source .venv/bin/activate

# 运行自动修复Agent
python -m agent.main
```

## Run Tests / 运行测试
```bash
# 确保已激活虚拟环境
source .venv/bin/activate

# 运行所有测试
pytest tests/ -v
```

---

## 第一阶段：FastAPI Buggy Demo服务

这是基于Agent的Web服务自动化修复系统的第一阶段Demo，用于模拟线上Web服务报bug的场景。

## 项目结构
```
agent-auto-debug/
├── app/
│   └── main.py          # FastAPI主服务代码（包含故意bug）
├── tests/
│   └── test_app.py      # pytest测试用例
├── logs/                # 错误日志存放目录
├── fix_records/         # 后续Agent修复记录存放目录
├── requirements.txt     # Python依赖
└── README.md
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动服务
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
服务启动后访问 http://localhost:8000/docs 可以查看Swagger文档。

### 3. 触发bug
访问 http://localhost:8000/users/2 会触发KeyError：
- 返回HTTP 500：`{"detail": "Internal Server Error"}`
- 完整的Traceback会被写入 `logs/error.log` 文件

正常访问 http://localhost:8000/users/1 会成功返回用户信息。

### 4. 运行测试
```bash
pytest tests/ -v
```
预期结果：
- `test_get_user_1_success`：通过 ✅
- `test_get_user_2_has_bug`：通过 ✅（说明bug确实存在）

## 第二阶段：AutoFix Agent 使用方法（固定规则模式）

现在已经实现了最小规则版自动修复Agent，可以完成完整的修复闭环。

### 1. 先触发bug生成错误日志
```bash
# 启动服务
uvicorn app.main:app --reload --port 8000

# 访问触发bug
curl http://localhost:8000/users/2

# 确认错误日志已生成
cat logs/error.log
```

### 2. 运行自动修复Agent
```bash
python3 -m agent.main
```

Agent会自动完成以下流程：
1. 读取logs/error.log中的错误
2. 解析Traceback定位到出错文件和行号（自动过滤第三方库，只定位项目代码）
3. 读取相关代码上下文
4. 自动修复user["age"]为user.get("age", 0)
5. 自动更新测试用例test_get_user_2_has_bug为test_get_user_2_fixed
6. 运行pytest验证修复是否成功
7. 在fix_records/目录下生成完整修复记录bug_001.md

修复完成后：
- 访问/users/2会返回200，age字段为默认值0
- pytest运行后两个测试都会通过
- 修复记录会包含完整的bug信息、修改内容和测试结果

## 第三阶段：AutoFix Agent LLM 修复模式

现在已经支持LLM智能修复能力，优先使用大模型分析和修复bug，失败会自动fallback到固定规则。

### 1. 配置LLM环境
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入你的OpenAI API Key
OPENAI_API_KEY=your_actual_api_key
OPENAI_MODEL=gpt-4o-mini  # 可选，默认使用gpt-4o-mini
```

### 2. 安装新增依赖
```bash
pip install -r requirements.txt
```

### 3. 运行LLM修复模式
```bash
python3 -m agent.main
```

### 修复逻辑说明：
- 如果配置了OPENAI_API_KEY，会优先调用LLM分析bug并生成修复方案
- LLM会输出结构化JSON，包含根因分析、修复策略和代码补丁
- 如果LLM调用失败、JSON解析失败或补丁应用失败，会自动切换到固定规则修复
- 终端会明确显示当前使用的是"LLM修复模式"还是"Fixed Rule Fallback模式"
- 修复记录会根据修复模式展示不同的内容：
  - LLM模式：包含LLM的根因分析和修复策略
  - Fallback模式：显示固定规则的修复说明

### 兼容性说明：
- 所有原有功能完全保留，没有破坏性修改
- 如果没有配置OPENAI_API_KEY，系统会自动使用固定规则修复，完全不影响使用
- 修复过程完全幂等，已经修复过的代码不会重复修改
- pytest仍然会全部通过

## 使用火山引擎方舟在线模型

本项目通过 OpenAI-compatible API 接入火山引擎方舟在线大模型，无需修改代码即可直接使用。

### 配置方法
1. 在项目根目录下的 `.env` 文件中填写你的火山引擎方舟配置：
```
OPENAI_API_KEY=your_volcengine_ark_api_key_here
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
OPENAI_MODEL=your_volcengine_model_or_endpoint_id_here
```

### 火山方舟常用配置
- **Base URL**：`https://ark.cn-beijing.volces.com/api/v3`
- **API Key**：在火山引擎方舟控制台创建的API Key
- **Model/Endpoint ID**：模型部署后的Endpoint ID

### 测试连通性
```bash
# 确保已激活虚拟环境
source .venv/bin/activate

# 运行连通性测试
python test_volcengine.py
```

### 运行Agent
```bash
# 确保已激活虚拟环境
source .venv/bin/activate

# 运行自动修复Agent
python -m agent.main
```

### 预期行为
- 如果在线模型连接成功，Agent会优先尝试LLM智能修复
- 如果LLM调用失败、输出不是合法JSON、或者补丁无法应用，系统会自动使用固定规则 fallback
- Fallback是正常的安全机制，不是程序崩溃，可以保证修复流程始终正常完成

## 飞书通知配置

AutoFix Agent支持修复完成后自动发送飞书卡片通知给开发者。

### 配置方法
1. 在飞书群中添加自定义机器人，复制Webhook URL，格式类似：`https://open.feishu.cn/open-apis/bot/v2/hook/xxx`
2. 在项目根目录下的 `.env` 文件中添加飞书配置：
```
FEISHU_WEBHOOK_URL=your_feishu_webhook_url_here
```

### 测试连通性
```bash
# 确保已激活虚拟环境
source .venv/bin/activate

# 运行飞书连通性测试
python test_feishu.py
```

### 使用说明
- 运行Agent后，当修复成功并通过pytest测试时，会自动发送飞书卡片通知
- 卡片内容包含：Bug类型、修改文件、出错函数、修复模式、测试结果、修复记录等信息
- 如果是LLM修复模式，还会包含LLM根因分析和修复策略
- 如果没有配置`FEISHU_WEBHOOK_URL`，系统会自动跳过通知，完全不影响修复主流程

## Demo 演示流程
你可以按照以下步骤重复演示完整的自动修复流程：

### 1. 重置到bug初始状态
```bash
# 确保已激活虚拟环境
source .venv/bin/activate

# 执行重置脚本
python demo_reset.py
```
脚本会自动：
- 将app/main.py恢复到有bug的状态
- 将测试用例恢复到bug复现状态
- 清空错误日志
- 归档旧的修复记录

### 2. 启动FastAPI服务
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. 新开一个terminal，进入项目并激活虚拟环境
```bash
cd /Users/chancie/Documents/trae_projects/agent-auto-debug
source .venv/bin/activate
```

### 4. 触发bug
```bash
curl http://127.0.0.1:8000/users/2
```
此时会返回500错误，完整Traceback会写入logs/error.log

### 5. 查看日志
```bash
cat logs/error.log
```

### 6. 运行Agent自动修复
```bash
python -m agent.main
```
Agent会自动完成：读取日志→解析错误→LLM分析→修复代码→更新测试→运行验证→生成记录→发送飞书通知

### 7. 验证修复结果
```bash
# 运行测试，应该全部通过
pytest tests/ -v

# 查看修复记录
cat fix_records/bug_001.md

# 查看飞书群通知
```

现在你可以重复执行步骤1-7，多次演示完整的自动修复流程！

## Agent Watcher 自动监控模式
AutoFix Agent支持自动监控日志模式，一旦Web服务报错，会自动触发完整的修复流程，无需手动执行`python -m agent.main`。

### 使用步骤
1. **启动FastAPI Web服务**
```bash
uvicorn app.main:app --reload --port 8000
```

2. **新开Terminal，启动Watcher监控**
```bash
# 确保已激活虚拟环境
source .venv/bin/activate

# 启动监控器
python -m agent.watch
```
启动成功会显示：
```
👀 AutoFix Watcher started
Watching: logs/error.log
Press Ctrl+C to stop
```

3. **再新开Terminal，触发bug**
```bash
curl http://127.0.0.1:8000/users/2
```

### 自动修复流程
- Web服务报错后会自动将完整Traceback写入`logs/error.log`
- Watcher每2秒轮询一次日志文件，检测到新的Traceback会自动触发AutoFix Agent
- Agent自动完成全部流程：LLM分析→代码修复→更新测试→pytest验证→生成修复记录→Git本地提交→飞书通知
- 修复完成后Watcher继续监控，等待下一次错误

### 完整三终端演示流程
```bash
# 1. 先重置到bug状态
python demo_reset.py

# Terminal 1: 启动Web服务
uvicorn app.main:app --reload --port 8000

# Terminal 2: 启动Watcher监控
source .venv/bin/activate
python -m agent.watch

# Terminal 3: 触发bug
curl http://127.0.0.1:8000/users/2
```

### 预期结果
- Terminal 2中的Watcher会自动检测到错误并触发修复
- `app/main.py`被自动修复
- pytest测试全部通过
- `fix_records/bug_001.md`生成
- 本地Git提交成功
- 飞书群收到修复通知卡片

## GitHub PR 自动创建
AutoFix Agent支持在本地Git Commit成功后自动创建GitHub Pull Request，所有操作均符合安全规范。

### 功能说明
修复成功后如果满足前置条件，Agent会自动：
1. 推送当前`autofix/*`修复分支到远程仓库
2. 创建GitHub PR，PR标题、描述自动生成，包含bug信息、根因分析、修复策略等
3. 飞书通知中会自动包含PR链接，方便直接点击Review

### 前置条件
- 当前Git仓库已配置`remote origin`
- 已安装GitHub CLI
- 已执行`gh auth login`完成登录
- 当前修复分支名格式为`autofix/*`

### 配置步骤
1. **安装GitHub CLI**
```bash
brew install gh
```

2. **登录GitHub账号**
```bash
gh auth login
```
按照提示完成认证即可，Agent会自动使用系统已有的登录状态，无需在代码中配置Token。

3. **配置远程仓库**
```bash
git remote add origin <your-github-repo-url>
```
只需要配置一次，后续自动生效。

### 安全设计
- ✅ **仅允许推送autofix/*分支**：绝对不会push main/master等生产分支
- ✅ **无Token硬编码**：完全使用GitHub CLI的系统登录状态，无需在代码或.env中配置任何Token
- ✅ **优雅降级**：如果没有配置remote、未安装gh或未登录，PR创建会自动跳过，完全不影响修复主流程
- ✅ **无敏感信息泄露**：不会打印、记录或提交任何Token、API Key等敏感信息

### 完整自动修复流程（包含PR）
```bash
# 1. 重置到bug状态
python demo_reset.py

# Terminal 1: 启动Web服务
uvicorn app.main:app --reload --port 8000

# Terminal 2: 启动Watcher监控
source .venv/bin/activate
python -m agent.watch

# Terminal 3: 触发bug
curl http://127.0.0.1:8000/users/2
```

### 流程结果
1. Watcher自动检测到错误触发修复
2. Agent完成代码修复、测试验证、本地Git Commit
3. 自动推送autofix分支到远程并创建PR
4. 飞书通知中包含PR链接，点击可直接Review

## Git Commit Tool
AutoFix Agent修复成功后支持自动创建本地Git分支并提交修复代码，所有操作均在本地完成，不会推送到远程仓库。

### 功能说明
1. **自动创建修复分支**：修复成功后会自动创建格式为 `autofix/<error-type>-<function-name>` 的修复分支，例如：`autofix/keyerror-get_user`
2. **安全提交检查**：仅允许提交安全文件，自动过滤敏感文件：
   - ✅ 允许提交：app/main.py、测试文件、修复记录、agent代码、配置文件等
   - ❌ 禁止提交：.env、.venv、logs/error.log、缓存文件、敏感信息
3. **本地提交**：自动生成本地Commit，Commit消息格式为 `AutoFix: fix <error-type> in <function-name>`
4. **无侵入设计**：
   - 本阶段不会执行任何`git push`操作
   - 不会创建GitHub PR或连接远程仓库
   - 所有Commit仅保存在本地Git仓库
   - 如果不是Git仓库会自动跳过，不影响主流程
5. **手动推送**：后续需要推送到远程仓库时，用户可以手动配置远程地址并执行`git push`

### 后续Agent开发方向
你可以继续扩展Agent功能：
1. 接入大模型实现通用错误修复能力
2. 添加多种错误类型的支持
3. 实现Git Commit/PR自动提交
4. 添加飞书/企业微信通知
5. 引入LangGraph实现更复杂的修复流程
