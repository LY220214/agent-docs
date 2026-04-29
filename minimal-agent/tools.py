"""
最小 Agent 工具集 —— 给 Agent 提供与外部世界交互的能力。

每个工具就是一个普通 Python 函数，拥有：
  - name: 工具名称（Agent 用它来调用）
  - description: 描述（Agent 根据描述判断什么时候该用这个工具）
  - parameters: 参数说明（Agent 根据说明填写参数）
  - execute: 实际执行逻辑

新手提示：你可以把"工具"理解为 Agent 的"手脚"。
没有工具，Agent 只能说话；有了工具，Agent 能做事。
"""

import os
import re
import subprocess
from typing import Any

# ──────────────────────────────────────────────
# 工具基类
# ──────────────────────────────────────────────

class Tool:
    """工具基类。每个具体工具继承这个类。"""

    name: str = ""
    description: str = ""
    parameter_schema: dict = {}

    def execute(self, **kwargs) -> str:
        """执行工具，返回字符串结果。子类必须实现这个方法。"""
        raise NotImplementedError


# ──────────────────────────────────────────────
# 工具 1: 读文件
# ──────────────────────────────────────────────

class ReadFileTool(Tool):
    name = "read_file"
    description = (
        "读取指定文件的内容。适用于查看代码、配置文件或文档。"
        "参数 path 是文件的绝对或相对路径。"
    )
    parameter_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "要读取的文件路径",
            }
        },
        "required": ["path"],
    }

    def execute(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            # 限制返回长度，避免 Token 爆炸
            if len(content) > 5000:
                return content[:5000] + "\n... (内容过长，已截断)"
            return content
        except FileNotFoundError:
            return f"错误：文件不存在 —— {path}"
        except PermissionError:
            return f"错误：没有权限读取 —— {path}"
        except Exception as e:
            return f"读取文件时出错：{e}"


# ──────────────────────────────────────────────
# 工具 2: 搜索文件内容（简单 grep）
# ──────────────────────────────────────────────

class SearchFilesTool(Tool):
    name = "search_files"
    description = (
        "在指定目录中搜索包含特定关键词的文件。"
        "参数 directory 是搜索目录，pattern 是要搜索的关键词或正则表达式。"
        "返回匹配的文件名和行号。"
    )
    parameter_schema = {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "搜索的目标目录路径",
            },
            "pattern": {
                "type": "string",
                "description": "要搜索的关键词或正则表达式",
            },
        },
        "required": ["directory", "pattern"],
    }

    def execute(self, directory: str, pattern: str) -> str:
        results = []
        try:
            compiled = re.compile(pattern)
            for root, dirs, files in os.walk(directory):
                # 跳过隐藏目录和虚拟环境
                dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
                for filename in files:
                    if filename.startswith("."):
                        continue
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            for lineno, line in enumerate(f, 1):
                                if compiled.search(line):
                                    results.append(f"{filepath}:{lineno}: {line.strip()}")
                    except Exception:
                        continue  # 跳过无法读取的文件

            if not results:
                return f"在 {directory} 中没有找到匹配 '{pattern}' 的内容。"
            return "\n".join(results[:50])  # 最多返回 50 条
        except Exception as e:
            return f"搜索时出错：{e}"


# ──────────────────────────────────────────────
# 工具 3: 执行 Shell 命令（受限）
# ──────────────────────────────────────────────

class RunShellTool(Tool):
    name = "run_shell"
    description = (
        "执行一个 Shell 命令并返回输出。"
        "适用于运行测试、检查 git 状态、安装依赖等。"
        "⚠️ 仅供学习使用，生产环境需要沙箱隔离。"
    )
    parameter_schema = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要执行的 shell 命令",
            }
        },
        "required": ["command"],
    }

    # 危险命令黑名单 —— 学习用，真实项目需要更严格的控制
    DANGEROUS_COMMANDS = ["rm -rf", "sudo", "mkfs", "dd if=", ":(){ :|:& };:"]

    def execute(self, command: str) -> str:
        # 基础安全检查
        for dangerous in self.DANGEROUS_COMMANDS:
            if dangerous in command.lower():
                return f"安全拦截：命令包含危险操作 '{dangerous}'，已拒绝执行。"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,  # 30 秒超时
                cwd=os.getcwd(),
            )
            output = result.stdout
            if result.stderr:
                output += "\n[stderr]\n" + result.stderr
            if not output.strip():
                output = f"命令执行成功，无输出。（返回码: {result.returncode}）"
            return output.strip()
        except subprocess.TimeoutExpired:
            return "错误：命令执行超时（超过 30 秒）。"
        except Exception as e:
            return f"执行命令时出错：{e}"


# ──────────────────────────────────────────────
# 工具注册表
# ──────────────────────────────────────────────

# 所有可用工具列表。添加新工具只需在这里注册。
ALL_TOOLS: list[Tool] = [
    ReadFileTool(),
    SearchFilesTool(),
    RunShellTool(),
]


def get_tool_by_name(name: str) -> Tool | None:
    """根据名称获取工具实例。"""
    for tool in ALL_TOOLS:
        if tool.name == name:
            return tool
    return None


def get_tools_description() -> str:
    """生成所有工具的描述文本，用于注入 System Prompt。"""
    lines = []
    for tool in ALL_TOOLS:
        params = tool.parameter_schema.get("properties", {})
        param_desc = ", ".join(
            f"{k}: {v.get('description', '')}" for k, v in params.items()
        )
        lines.append(f"- **{tool.name}**: {tool.description}")
        if param_desc:
            lines.append(f"  参数: {param_desc}")
    return "\n".join(lines)
