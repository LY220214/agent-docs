# 🧠 Minimal ReAct Agent

> 一个不到 200 行的 AI Agent 实现，用于理解 Agent 的核心工作原理。

---

## 🎯 这个项目是什么

这不是一个生产级的 Agent 框架，而是一个**学习工具**。

它的目标是让你在 10 分钟内：
1. 跑通一个真实的 AI Agent
2. 亲眼看到 ReAct（推理 + 行动）循环是怎么工作的
3. 理解 Agent 和普通聊天机器人之间的本质区别

**聊天机器人**: 你问 → 它答  
**AI Agent**: 你给任务 → 它思考 → 调用工具 → 观察结果 → 再思考 → ... → 完成任务

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 需要 Python 3.10+
pip install openai
```

只需要这一个依赖。Agent 代码本身零外部依赖（除了 OpenAI SDK）。

### 2. 设置 API Key

```bash
# 使用 OpenAI
export OPENAI_API_KEY="sk-your-key-here"

# 或者使用 DeepSeek（更便宜，中文更好）
export OPENAI_API_KEY="sk-your-deepseek-key"
export OPENAI_BASE_URL="https://api.deepseek.com/v1"
export MODEL_NAME="deepseek-chat"
```

### 3. 运行

```bash
# 交互模式
python agent.py

# 或者直接给一个任务
python agent.py "在当前目录搜索所有包含 TODO 的文件"
```

### 4. 你会看到什么

```
============================================================
🤖 Agent 启动 | 模型: deepseek-chat | 最大循环: 10
============================================================

🔄 第 1 轮：正在调用 LLM...
   LLM 输出: {"action": "search_files", "args": {"directory": ".", "pattern": "TODO"}}
   🔧 调用工具: search_files({'directory': '.', 'pattern': 'TODO'})
   📋 结果: ./agent.py:45: # TODO: 完善错误处理

🔄 第 2 轮：正在调用 LLM...
   LLM 输出: {"final_answer": "找到 1 个 TODO: agent.py 第 45 行"}
✅ 任务完成（共 2 轮）

📝 最终答案:
找到 1 个 TODO: agent.py 第 45 行
```

---

## 📖 代码结构

```
minimal-agent/
├── agent.py      # Agent 主程序（核心逻辑 ~180 行）
├── tools.py      # 工具定义（3 个工具，约 180 行）
└── README.md     # 本文件
```

### `agent.py` —— Agent 的大脑

- `SystemPrompt`: 告诉 LLM 它是什么、能做什么、输出什么格式
- `run()`: ReAct 循环的核心——在其中依次完成 思考（调用LLM）→ 行动（执行工具）→ 观察（反馈结果）
- `_call_llm()`: 调用 LLM API，相当于"思考"阶段
- `_parse_response()`: 解析 LLM 返回的 JSON，判断是工具调用还是最终答案
- `_act()`: 执行 LLM 选择的工具
- `_force_final_answer()`: 达到最大循环次数时，强制 LLM 给出最终答案

> 💡 `_think()` 和 `_observe()` 在本代码中并非独立方法——思考逻辑在 `_call_llm()`+`_parse_response()` 中，观察逻辑直接内嵌在 `run()` 循环里。

### `tools.py` —— Agent 的手脚

- `ReadFileTool`: 读取文件内容
- `SearchFilesTool`: 在目录中搜索关键词
- `RunShellTool`: 执行 Shell 命令（带基础安全检查）

---

## 🧪 实验建议

跑通基础示例后，试试这些改动来加深理解：

### 初级实验
- 让 Agent 读取自己的源代码并解释它在做什么
- 让 Agent 搜索 `agent.py` 中所有的函数定义
- 故意给一个 Agent 无法完成的任务，观察它如何"放弃"

### 中级实验
- 在 `tools.py` 中添加一个新工具（比如 `write_file`、`web_search`）
- 修改 System Prompt，让 Agent 使用不同的"人格"
- 把 `temperature` 从 0.1 调到 0.8，观察 Agent 行为的变化

### 进阶实验
- 把 `MAX_ITERATIONS` 改大或改小，观察对任务完成率的影响
- 在 `_act()` 中添加重试逻辑（工具失败后自动重试）
- 记录每一轮的 Token 消耗，分析什么地方消耗最大

---

## ❓ 常见问题

**Q: 为什么 Agent 有时会卡住？**  
A: LLM 的输出格式可能不对（JSON 解析失败）。看到 `JSON 解析失败` 提示时，Agent 会尝试让 LLM 修正格式。如果持续失败，检查 System Prompt 中的格式要求是否被正确传递。

**Q: 能用于生产环境吗？**  
A: 不能。这个项目刻意保持极简，没有错误重试、上下文压缩、工具校验、权限控制等生产必需的功能。它的唯一目的是学习。

**Q: 支持哪些模型？**  
A: 任何 OpenAI 兼容的 API。测试过 GPT-4o-mini、DeepSeek-V3、Claude（通过兼容端点）。推荐 DeepSeek 因为便宜且中文能力强。

**Q: 如何添加更多工具？**  
A: 在 `tools.py` 中创建一个继承 `Tool` 的类，实现 `execute()` 方法，然后加到 `ALL_TOOLS` 列表里。Agent 会自动发现新工具。

---

## 📚 延伸阅读

完成这个实验后，推荐继续阅读：

1. **文档库核心文档**: [../docs/README.md](../docs/README.md) —— 深入理解 Agent 架构、MCP 协议、多租户等
2. **ReAct 论文**: [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
3. **LangChain Agent 文档**: 看看工业级 Agent 框架怎么做的
4. **Anthropic 的 MCP 协议**: [modelcontextprotocol.io](https://modelcontextprotocol.io/)

---

> 🎯 **一句话总结**：Agent = LLM + 循环（思考→行动→观察）+ 工具。这个项目用 200 行代码让你亲眼看到这三样东西怎么配合。
