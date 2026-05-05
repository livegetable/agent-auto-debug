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

### 后续Agent开发方向
你可以继续扩展Agent功能：
1. 接入大模型实现通用错误修复能力
2. 添加多种错误类型的支持
3. 实现Git Commit/PR自动提交
4. 添加飞书/企业微信通知
5. 引入LangGraph实现更复杂的修复流程
