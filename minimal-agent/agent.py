#!/usr/bin/env python3
"""
最小 ReAct Agent —— 理解 AI Agent 工作原理的最简实现。

这个文件实现了 ReAct（Reasoning + Acting）范式的核心循环：
  1. 思考（Think）: 让 LLM 分析当前状态，决定下一步
  2. 行动（Act）:  执行 LLM 选择的工具
  3. 观察（Observe）: 获取工具执行结果，更新上下文
  4. 重复，直到任务完成

依赖安装：
  pip install openai

使用方法：
  export OPENAI_API_KEY="your-key"
  export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选，默认 OpenAI
  python agent.py

或者使用 DeepSeek / 其他兼容 API：
  export OPENAI_API_KEY="sk-xxx"
  export OPENAI_BASE_URL="https://api.deepseek.com/v1"
  export MODEL_NAME="deepseek-chat"
  python agent.py

新手提示：
  这个文件大约 180 行，建议逐段阅读。核心逻辑在 run() 方法里。
"""

import json
import os
import sys
from openai import OpenAI

from tools import ALL_TOOLS, get_tool_by_name, get_tools_description

# ──────────────────────────────────────────────
# 配置（通过环境变量，方便切换不同 LLM）
# ──────────────────────────────────────────────

API_KEY = os.environ.get("OPENAI_API_KEY", "sk-your-key-here")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "10"))


# ──────────────────────────────────────────────
# System Prompt —— 告诉 LLM 它是什么，能做什么
# ──────────────────────────────────────────────

SYSTEM_PROMPT = f"""你是一个 AI 助手，拥有调用外部工具的能力。

## 你的工作方式

你按照 ReAct（Reasoning + Acting）范式工作：
1. 先思考用户需要什么
2. 如果需要外部信息（读文件、搜索代码、执行命令），调用对应的工具
3. 根据工具返回的结果继续思考
4. 直到你能给出最终答案

## 可用工具

{get_tools_description()}

## 输出格式要求（极其重要）

你的每次回复必须是**纯 JSON**，不要带任何额外的文字。格式如下：

如果需要调用工具：
{{{{
  "action": "工具名称",
  "args": {{"参数名": "参数值"}}
}}}}

如果任务完成，可以给出最终答案：
{{{{
  "final_answer": "你的最终答案"
}}}}

注意：
- 一次只能调用一个工具
- 如果工具返回错误，尝试其他方式
- 如果多次尝试仍然失败，承认无法完成任务并给出原因
"""


# ──────────────────────────────────────────────
# Agent 核心类
# ──────────────────────────────────────────────

class SimpleAgent:
    """
    一个最小化的 ReAct Agent。

    工作流程：
      run(用户输入)
        → think()     # 让 LLM 决定做什么
        → act()       # 执行 LLM 选择的动作
        → observe()   # 把结果反馈给 LLM
        → 重复，直到 LLM 说"完成了"
    """

    def __init__(self):
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        self.messages: list[dict] = []  # 对话历史
        self.iteration = 0               # 当前循环次数

    def run(self, user_input: str) -> str:
        """
        运行 Agent，处理用户输入直到任务完成或达到最大循环次数。

        这是整个文件的入口，所有 ReAct 循环逻辑都在这里。
        """
        print(f"\n{'='*60}")
        print(f"🤖 Agent 启动 | 模型: {MODEL_NAME} | 最大循环: {MAX_ITERATIONS}")
        print(f"{'='*60}\n")

        # 初始化对话：System Prompt + 用户输入
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]

        final_answer = None

        while self.iteration < MAX_ITERATIONS:
            self.iteration += 1

            # ── 第 1 步：思考（Think）──
            # 让 LLM 分析当前对话，决定下一步行动
            response = self._call_llm()
            parsed = self._parse_response(response)
            if parsed is None:
                # LLM 返回了无效响应，继续循环让 LLM 自我纠正
                continue

            # ── 检查是否是最终答案 ──
            if "final_answer" in parsed:
                final_answer = parsed["final_answer"]
                print(f"✅ 任务完成（共 {self.iteration} 轮）\n")
                break

            # ── 第 2 步：行动（Act）──
            # 解析 LLM 的工具调用请求并执行
            if "action" not in parsed:
                # LLM 既没给最终答案也没给工具调用，提示它重新输出
                self.messages.append({
                    "role": "user",
                    "content": "请按照格式输出 JSON：调用工具用 {action, args}，完成任务用 {final_answer}。"
                })
                continue

            tool_result = self._act(parsed["action"], parsed.get("args", {}))

            # ── 第 3 步：观察（Observe）──
            # 将工具执行结果作为新消息加入对话，让 LLM 在下一轮看到
            self.messages.append({
                "role": "user",
                "content": f"[工具执行结果]\n{tool_result}\n\n请继续分析并决定下一步行动。"
            })

        # ── 循环结束，返回结果 ──
        if final_answer:
            return final_answer

        # 达到最大循环次数仍未完成
        return self._force_final_answer()

    def _call_llm(self) -> str:
        """调用 LLM API，返回模型输出的文本。"""
        print(f"🔄 第 {self.iteration} 轮：正在调用 LLM...")
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=self.messages,
                temperature=0.1,  # 低温度，让输出更确定
                max_tokens=1000,
            )
            content = response.choices[0].message.content or ""
            print(f"   LLM 输出: {content[:200]}...")
            return content
        except Exception as e:
            print(f"   ❌ LLM 调用失败: {e}")
            return json.dumps({"final_answer": f"API 调用失败：{e}"})

    def _parse_response(self, response: str) -> "dict | None":
        """解析 LLM 的 JSON 响应。返回 None 表示解析失败。"""
        try:
            # 提取 JSON（LLM 可能在外面包了 markdown 代码块）
            response = response.strip()
            if response.startswith("```"):
                # 去掉 markdown 代码块标记
                lines = response.split("\n")
                # 至少3行才安全切片（```json / {content} / ```）
                if len(lines) >= 3:
                    response = "\n".join(lines[1:-1])
                else:
                    # 单行或双行不做切片，直接交给 JSON 解析
                    pass
            return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON 解析失败: {e}")
            # 把错误反馈给 LLM，让它修正格式
            self.messages.append({
                "role": "user",
                "content": f"你的上一个回复不是有效的 JSON，请修正。错误：{e}\n请严格按照格式输出。"
            })
            return None

    def _act(self, tool_name: str, args: dict) -> str:
        """执行工具调用。"""
        tool = get_tool_by_name(tool_name)
        if tool is None:
            return f"错误：没有找到工具 '{tool_name}'。可用工具：{[t.name for t in ALL_TOOLS]}"

        print(f"   🔧 调用工具: {tool_name}({args})")
        try:
            result = tool.execute(**args)
            print(f"   📋 结果: {result[:200]}...")
            return result
        except Exception as e:
            return f"工具执行异常：{e}"

    def _force_final_answer(self) -> str:
        """达到最大迭代次数后，强制 LLM 给出基于已有信息的最终答案。"""
        self.messages.append({
            "role": "user",
            "content": "已达到最大循环次数。请基于已有的信息给出你能给出的最佳答案。"
        })
        response = self._call_llm()
        try:
            parsed = self._parse_response(response)
            if parsed and "final_answer" in parsed:
                return parsed["final_answer"]
        except Exception:
            pass
        return f"任务未能在 {MAX_ITERATIONS} 轮内完成。最后输出：{response}"


# ──────────────────────────────────────────────
# 命令行入口
# ──────────────────────────────────────────────

def main():
    """命令行入口。支持交互模式。"""
    print("""
╔══════════════════════════════════════════════════════╗
║           🧠 Minimal ReAct Agent                    ║
║                                                      ║
║  一个最小化的 AI Agent 实现，用于学习 Agent 原理。    ║
║  约 180 行代码，实现了完整的 ReAct 循环。             ║
║                                                      ║
║  可用工具: read_file, search_files, run_shell        ║
║  模型: {model:40} ║
╚══════════════════════════════════════════════════════╝
""".format(model=MODEL_NAME))

    # 检查 API Key
    if not API_KEY or API_KEY == "sk-your-key-here" or len(API_KEY) < 20:
        print("⚠️  请先设置有效的 OPENAI_API_KEY 环境变量。")
        print("   export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)

    agent = SimpleAgent()

    # 交互模式
    if len(sys.argv) > 1:
        # 命令行参数模式：直接执行
        task = " ".join(sys.argv[1:])
        result = agent.run(task)
        print(f"\n📝 最终答案:\n{result}\n")
        return

    print("输入你的任务（输入 'quit' 退出）：\n")
    while True:
        try:
            user_input = input("👤 你: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("👋 再见！")
                break

            result = agent.run(user_input)
            print(f"\n📝 最终答案:\n{result}\n")

        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}\n")


if __name__ == "__main__":
    main()
