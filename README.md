# fun-agent-service

Node + Python 组合的智能体应用服务。

## 快速开始

```powershell
cd D:\dev\AI\AIPro\fun-ai-station\fun-agent-service
npm install
npm run dev
```

默认服务端口：`4010`  
Python 解释器可通过 `PYTHON_BIN` 指定。
LLM 相关：`LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`、`LLM_CONFIG_PATH`。
默认读取 `agents/configs/llm.json`（可通过 API 可视化修改）。

## Skills

通用能力封装在 `agents/skills/`：

- `llm.py`：OpenAI 兼容 Chat Completions 客户端
- `registry.py`：技能注册与复用（当前提供 `registry.llm()`）

## 接口

### GET /agents
返回已注册的智能体列表。

### POST /agents/:agent/execute
请求体：
```json
{
  "input": "你好，帮我总结一下",
  "context": {}
}
```

返回：
```json
{ "output": "..." }
```

### Trace Id
支持请求头 `x-trace-id`；未提供则自动生成，并回传在响应头。

## Python 智能体目录

`agents/` 目录内每个智能体都是一个模块（文件里导出 `AGENT`），同时支持在
`agents/configs/*.json` 中用配置方式自动加载。

## 新增智能体

两种方式任选其一：

### 方式 A：写 Python 智能体（可编程逻辑）

1) 在 `agents/` 新增文件，例如 `template_agent.py`  
2) 继承 `BaseAgent` 并导出 `AGENT` 实例  
3) 重启服务后，通过 `GET /agents` 查看是否出现

示例（已内置）：`agents/attendance_agent.py`