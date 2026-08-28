# KodeAgent

> **一个面向学习与项目级长任务的自构建 AI Agent 框架**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

KodeAgent 是一个用来本人**学习梳理**的 AI Agent 框架 —— 核心逻辑（agent 循环、工具抽象、思维范式、事件驱动）全部自己手写，只在必要的基础设施层（LLM SDK、TUI 库、Token counter）使用成熟库。

**当前状态**：v0.1 Phase 1 骨架完成，ruff / pyright / pytest 三套验证全绿，CLI 冒烟通过。

---

## ✨ 核心特性

- **事件驱动架构**：agent loop 产生事件 → EventBus 广播 → 订阅者（CLI/TUI/logger）消费
- **工具并发执行**：同一轮多 tool_call 用 `asyncio.gather` 并发（tool 间无依赖是 LLM 的隐含契约）
- **双类型消息**：AgentMessage（内部，含扩展类型）→ `convert_to_llm` → LLMMessage（协议）
- **Hook 扩展**：ReAct / Plan-Execute 通过实现 `AgentHooks` 改变行为，不改核心 loop
- **多 Provider**：OpenAI / Ollama（OpenAI 协议）/ Mock，Anthropic 待接入
- **结构化 JSON 日志**：自动脱敏敏感字段

---

## 🚀 快速开始

```bash
# 1. 克隆
git clone https://github.com/Shiningold/kodeagent.git
cd kodeagent

# 2. 创建虚拟环境（推荐 Conda）
conda create -n kode python=3.11
conda activate kode
uv pip install -e ".[dev]"

# 3. 配置 API key
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY，或用 Ollama（无需真实 key）

# 4. 跑起来（mock 模式，无需 API key）
python -m kodeagent "你好，介绍下你自己" --mock

# 5. 接真实 LLM
python -m kodeagent "帮我写个 Python 排序函数"
```

> **Windows 注意**：conda 回显非 ASCII 会触发 GBK 编码错误，加前缀：
> `PYTHONIOENCODING=utf-8 conda run -n kode <command>`

---

## 🧪 开发命令

```bash
ruff check kodeagent tests           # 代码检查
ruff check kodeagent tests --fix     # 自动修复
pyright                              # 类型检查
pytest tests/ -v                     # 运行测试（4 个冒烟测试）
```

---

## 📁 项目结构

```
kodeagent/
├── core/                  # 框架核心
│   ├── config.py          # pydantic-settings，3 层配置
│   ├── logger.py          # 结构化 JSON 日志 + 自动脱敏
│   ├── message.py         # AgentMessage / LLMMessage / convert_to_llm
│   ├── events.py          # 9 种事件 dataclass
│   ├── agent_hooks.py     # 3 必传 + 4 可选 hook 容器
│   ├── event_bus.py       # asyncio.Queue 广播 + N 订阅者
│   ├── llm.py             # LLMProvider Protocol + OpenAI/Mock 实现
│   ├── paradigm.py        # 通用 loop 骨架（工具并发执行）
│   ├── agent.py           # Agent 基类（hook 组装 + 事件流入口）
│   └── exceptions.py      # 异常体系
├── tools/
│   ├── base.py            # Tool Protocol + ToolResult
│   ├── registry.py        # 工具注册 + OpenAI/Anthropic 格式转换
│   └── builtin/
│       ├── file.py        # file_read / file_write / file_edit
│       └── shell.py       # shell_exec（带安全策略）
├── agents/
│   └── react.py           # ReAct 范式 hooks 工厂
├── __main__.py            # CLI 入口
└── __init__.py            # __version__
tests/
├── conftest.py            # 共享 fixtures
└── test_smoke.py          # Phase 1 冒烟测试（4 个）
```

---

## 📄 License

MIT — 见 [LICENSE](LICENSE)
