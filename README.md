# KodeAgent

> **一个面向学习与项目级长任务的自构建 AI Agent 框架**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

KodeAgent 是一个用来本人**学习梳理**的 AI Agent 框架 —— 核心逻辑（agent 循环、记忆管理、工具抽象、思维范式、Harness）全部自己手写，只在必要的基础设施层（LLM SDK、TUI 库、Token counter）使用成熟库。

**当前状态**：v0.x 早期阶段。代码还在从 step 1 开始写。

---

## ✨ 核心特性

- （等第一个版本）

---

## 🚀 快速开始

> ⚠️ **项目还在早期**以下命令预计将在第一个版本编码后可用。

```bash
# 1. 克隆
git clone https://github.com/Shiningold/kodeagent.git
cd kodeagent

# 2. 创建虚拟环境（本人用的 Conda，自行创建Python环境）
conda create -n kode python=3.11
conda activate kode
pip install -e ".[dev]"    # 没想好用那些，到时候再说

# 3. 配置 API key
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY / ANTHROPIC_API_KEY

# 4. 跑起来
kodeagent "你好，介绍下你自己"
```

---

## 📄 License

MIT — 见 [LICENSE](LICENSE)
