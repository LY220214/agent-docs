# Claude Code SDK 技术分析

> 📋 **阅读提示**：Claude Code 是闭源产品，本文内容是基于公开文档、官方博客、协议规范和社区分析的综合梳理，并非官方源码解读。文中代码为分析性伪代码，用于阐述设计思路和协议机制。具体实现以 [官方文档](https://code.claude.com/docs) 和 [MCP 规范](https://modelcontextprotocol.io) 为准。
>
> 难度：⭐⭐⭐⭐⭐  
> 核心概念：MCP协议、工具发现、ReAct循环、Session管理

---

## 📖 阅读前你需要知道

在阅读本文之前，你需要了解以下概念。如果某个概念让你困惑，可以参考术语表获取更详细的解释。

| 概念 | 简单定义 | 类比理解 |
|------|----------|----------|
| **MCP协议** | Model Context Protocol，定义了AI模型与外部工具之间如何"对话"的规则 | 就像USB协议：不管你插什么设备（鼠标、键盘、U盘），电脑都能识别和使用，因为大家都遵循同一套通信规则 |
| **状态机** | 一套定义好的状态和转换规则，系统只能在满足条件时从一种状态切换到另一种 | 就像地铁闸机：关→刷卡→开→通过→关。你不能跳过"刷卡"直接从"关"变到"开" |
| **ReAct循环** | AI交替进行推理和行动的工作模式：思考→行动→观察→再思考 | 就像你解数学题：先想思路→写步骤→看结果→不对就换思路→再写步骤→再看结果 |
| **Session** | 一次完整的对话会话，包含所有历史消息和状态信息 | 就像你和客服的聊天窗口：从打开到关闭，中间所有对话都保存在一个Session里 |
| **上下文压缩** | 当对话太长时，把早期内容压缩成摘要，只保留最近的消息 | 就像你看一本很长的书：前面内容记个摘要，最近几页逐字细读。这样既不丢失关键信息，又不会脑容量不够 |

> 💡 如果这些概念还是觉得抽象，别担心。本文会在每个关键代码块前加上"白话理解"，帮你把技术语言翻译成日常语言。

---

## 📋 问题回顾

**核心问题**："Claude Code SDK底层原理是什么？"

这是一个**架构理解类问题**，掌握这个知识点需要深入理解：
- MCP（Model Context Protocol）协议
- 工具发现与调用机制
- 状态机调度逻辑
- 会话管理与持久化
- 多轮对话实现

---

## 🎯 核心设计理念

### Claude Code SDK的定位

Claude Code SDK是**大模型与操作系统/外部API之间的翻译官和调度员**，核心职责：

1. **协议转换**：将LLM的自然语言输出转换为可执行的工具调用
2. **状态管理**：维护对话状态，支持多轮交互
3. **工具发现**：动态发现和加载可用工具（Skills）
4. **上下文控制**：智能管理上下文窗口，避免Token爆炸

> 💡 **白话理解**：Claude Code SDK就像一个翻译兼调度中心。大模型只会说"自然语言"，但操作系统和API只听得懂"指令"。SDK的工作就是：把大模型想说的话翻译成具体的工具调用，把工具返回的结果翻译成大模型能理解的格式，同时记住整个对话过程，确保多轮对话不会"失忆"。

```
┌────────────────────────────────────────────────────────────────┐
│                     Claude Code SDK 定位                        │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│   大模型 (Claude)                                               │
│        │                                                       │
│        │ 自然语言 + 工具调用意图                                 │
│        ▼                                                       │
│   ┌────────────────────────────────────────────────────────┐   │
│   │                   Claude Code SDK                       │   │
│   │  ┌──────────────────────────────────────────────────┐  │   │
│   │  │  MCP协议层：标准化工具接口定义                     │  │   │
│   │  │  - 工具发现 (Tool Discovery)                      │  │   │
│   │  │  - 参数验证 (Parameter Validation)                │  │   │
│   │  │  - 结果格式化 (Result Formatting)                 │  │   │
│   │  └──────────────────────────────────────────────────┘  │   │
│   │                                                          │   │
│   │  ┌──────────────────────────────────────────────────┐  │   │
│   │  │  状态机层：对话流程控制                            │  │   │
│   │  │  - ReAct循环 (Reasoning → Acting → Observing)    │  │   │
│   │  │  - 会话管理 (Session Management)                  │  │   │
│   │  │  - 上下文压缩 (Context Compression)               │  │   │
│   │  └──────────────────────────────────────────────────┘  │   │
│   │                                                          │   │
│   │  ┌──────────────────────────────────────────────────┐  │   │
│   │  │  持久化层：对话历史存储                            │  │   │
│   │  │  - Thread日志 (Conversation History)              │  │   │
│   │  │  - Checkpoint快照 (State Snapshots)               │  │   │
│  │  │  - Checkpoint快照 (State Snapshots)               │  │   │
│   │  └──────────────────────────────────────────────────┘  │   │
│   └────────────────────────────────────────────────────────┘   │
│        │                                                       │
│        │ 标准化API调用                                          │
│        ▼                                                       │
│   操作系统/外部API                                               │
│   - 文件系统操作                                                │
│   - Git命令                                                    │
│   - 数据库查询                                                  │
│   - 网络请求                                                    │
│   - 企业内部API                                                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ 从零理解 MCP 协议

在深入技术细节之前，让我们先用一个类比来理解MCP协议到底在解决什么问题。

### 类比：MCP就像USB协议

想象一下USB出现之前的世界：

```
  USB出现之前：每个设备都有自己的接口
  ┌──────────────────────────────────────────────────┐
  │                                                  │
  │  键盘 → PS/2接口    鼠标 → 串口    打印机 → 并口  │
  │  U盘 → IDE接口      摄像头 → FireWire             │
  │                                                  │
  │  问题：每加一个新设备，就要写一套新的驱动程序         │
  │  开发者痛苦：我要为每个设备写不同的接口代码          │
  │                                                  │
  └──────────────────────────────────────────────────┘

  USB出现之后：所有设备统一用USB
  ┌──────────────────────────────────────────────────┐
  │                                                  │
  │  键盘 ──→ USB ──→ 电脑                           │
  │  鼠标 ──→ USB ──→ 电脑                           │
  │  U盘  ──→ USB ──→ 电脑                           │
  │  打印机──→ USB ──→ 电脑                           │
  │                                                  │
  │  好处：电脑只需要一套USB协议，就能识别所有设备       │
  │  开发者轻松：新设备只要遵循USB协议就能直接使用       │
  │                                                  │
  └──────────────────────────────────────────────────┘
```

MCP协议做的事情完全一样，只不过连接的不是硬件设备，而是AI工具：

```
  MCP出现之前：每个AI工具都有自己的接口
  ┌──────────────────────────────────────────────────┐
  │                                                  │
  │  文件操作 → 自定义API    Git操作 → 命令行封装      │
  │  数据库    → SQL驱动      网络请求 → HTTP客户端     │
  │                                                  │
  │  问题：每加一个新工具，就要改SDK代码来适配           │
  │  开发者痛苦：我要为每个工具写不同的调用代码           │
  │                                                  │
  └──────────────────────────────────────────────────┘

  MCP出现之后：所有工具统一用MCP协议
  ┌──────────────────────────────────────────────────┐
  │                                                  │
  │  文件操作 ──→ MCP ──→ Claude Code SDK            │
  │  Git操作  ──→ MCP ──→ Claude Code SDK            │
  │  数据库    ──→ MCP ──→ Claude Code SDK            │
  │  网络请求  ──→ MCP ──→ Claude Code SDK            │
  │                                                  │
  │  好处：SDK只需要一套MCP协议，就能发现和调用所有工具  │
  │  开发者轻松：新工具只要遵循MCP协议就能直接接入       │
  │                                                  │
  └──────────────────────────────────────────────────┘
```

**MCP协议的核心价值：**

| 没有MCP | 有MCP |
|---------|-------|
| 每个工具需要单独写适配代码 | 所有工具遵循统一接口，即插即用 |
| 新增工具需要修改SDK核心代码 | 新增工具只需实现MCP接口，SDK自动发现 |
| 工具之间无法互相通信 | 通过SDK统一调度，工具可以组合使用 |
| 工具描述格式不统一，LLM难以理解 | JSON Schema标准描述（`inputSchema`），LLM直接读懂 |

> 💡 **白话理解**：MCP协议就是AI世界的"USB标准"。就像USB让电脑不用关心插的是什么设备，MCP让AI不用关心调用的是什么工具。只要工具遵循MCP协议，AI就能自动发现它、理解它、调用它。

---

## 🔧 MCP协议（Model Context Protocol）

> 📋 **技术说明**：以下内容基于 MCP 规范 2025-11-25 版本（最新）。MCP 基于 JSON-RPC 2.0 协议。本节代码示例综合了官方规范和实践中的常见封装模式。

### 什么是MCP？

MCP（Model Context Protocol）是 Anthropic 主导的**开放标准协议**，定义了一套标准化的工具接口，让 LLM 能够：
- **动态发现**环境中的可用工具
- **理解**工具的输入参数和输出格式
- **调用**工具并处理返回结果

> 💡 **白话理解**：MCP就像餐厅的菜单。菜单上写着每道菜的名字（工具名）、描述（工具描述）、需要什么食材（参数）、做出来长什么样（返回值）。顾客（LLM）不需要进厨房，看菜单就能点菜。而MCP发现机制就像餐厅的"今日菜单"黑板，每天自动更新有哪些菜可以点。

### MCP的核心组件

MCP协议基于 **JSON-RPC 2.0**，所有通信都遵循请求/响应模式。核心方法包括 `tools/list`（发现工具）、`tools/call`（调用工具）、`resources/list`（列出资源）、`resources/read`（读取资源）、`prompts/list`（列出提示词）。传输层支持 **stdio** 和 **Streamable HTTP** 两种方式。

```typescript
// 1. 工具定义（Tool Definition）—— 对应 tools/list 返回的 Tool 对象
interface MCPTool {
  name: string;                    // 工具名称（唯一标识符）
  title?: string;                  // 工具的人类可读标题（2025-11-25 新增）
  description: string;             // 工具描述（LLM用这个理解工具用途）
  inputSchema: {                   // 输入参数模式（JSON Schema格式）
    type: 'object';
    properties: Record<string, JSONSchema>;
    required?: string[];
    additionalProperties?: boolean;
  };
  // 注意：MCP规范中工具定义不包含returns字段，
  // 工具结果通过 tools/call 的返回值描述
}

// 2. 工具调用请求 —— 对应 JSON-RPC 2.0 的 tools/call 方法调用
interface ToolCallRequest {
  method: 'tools/call';            // JSON-RPC 方法名
  params: {
    name: string;                  // 要调用的工具名
    arguments: Record<string, any>; // 工具参数（需符合 inputSchema）
  };
  id: string | number;             // JSON-RPC 请求ID（用于关联响应）
}

// 3. 工具调用结果 —— 对应 tools/call 的 JSON-RPC 响应
interface ToolCallResult {
  content: ToolContent[];          // 内容数组（必须字段）
  structuredContent?: Record<string, any>; // 机器可读的结构化结果（2025-11-25 新增）
  isError: boolean;               // 是否为错误结果（必须字段）
}

// 内容类型：支持 text、image、audio、resource_link 四种
type ToolContent =
  | { type: 'text'; text: string }
  | { type: 'image'; data: string; mimeType: string }
  | { type: 'audio'; data: string; mimeType: string }
  | { type: 'resource_link'; uri: string; name?: string; mimeType?: string };

// 4. MCP服务器接口（封装层）
interface MCPServer {
  // 发现可用工具（底层调用 tools/list）
  discover(): Promise<MCPTool[]>;
  
  // 执行工具调用（底层调用 tools/call）
  execute(request: ToolCallRequest): Promise<ToolCallResult>;
  
  // 获取服务器元数据
  getMetadata(): ServerMetadata;
}
```

> 💡 **关于 `structuredContent`**：MCP 2025-11-25 规范新增了 `structuredContent` 字段，用于返回机器可读的 JSON 结构化数据。与 `content`（面向人类阅读的文本/图片/音频）不同，`structuredContent` 让调用方可以程序化地解析工具结果，而不需要从文本中提取信息。例如，一个查询数据库的工具可以同时返回 `content`（人类可读的表格文本）和 `structuredContent`（机器可读的 JSON 数组）。

### MCP工具定义示例

> 💡 **白话理解**：下面这段代码就是在写"菜单"。`readFileTool`就是菜单上的一道菜，名叫"read_file"，描述是"读取文件内容"，参数是"文件路径"和"读取行数"。LLM看到这个菜单，就知道该怎么点菜了。注意MCP规范中工具定义使用 `inputSchema`（而非自定义的 `parameters`），并且不包含 `returns` 字段，因为工具结果由 `tools/call` 的响应格式统一描述。

```typescript
// 文件读取工具（符合 MCP 2025-11-25 规范）
const readFileTool: MCPTool = {
  name: 'read_file',
  title: '读取文件',                   // 人类可读标题（2025-11-25 新增）
  description: `
读取指定文件的内容。适用于查看代码、配置文件或文档。
注意：
- 大文件建议先使用view工具查看结构
- 二进制文件将返回[Binary content]标记
- 如果文件不存在会返回错误
  `,
  inputSchema: {                        // 使用 inputSchema（JSON Schema格式）
    type: 'object',
    properties: {
      path: {
        type: 'string',
        description: '文件的绝对路径或相对路径'
      },
      offset: {
        type: 'integer',
        description: '开始读取的行号（1-based，可选）',
        minimum: 1
      },
      limit: {
        type: 'integer',
        description: '最多读取多少行（可选，默认100行）',
        minimum: 1,
        maximum: 500
      }
    },
    required: ['path'],
    additionalProperties: false
  }
  // 注意：MCP规范中工具定义不包含 returns 字段
  // 工具结果通过 tools/call 响应的 content 数组返回
};

// Git操作工具
const gitDiffTool: MCPTool = {
  name: 'git_diff',
  title: '查看Git变更',
  description: '查看Git工作区的变更。可以查看staged或未staged的修改。',
  inputSchema: {
    type: 'object',
    properties: {
      staged: {
        type: 'boolean',
        description: '是否只查看staged的变更',
        default: false
      },
      file: {
        type: 'string',
        description: '指定查看某个文件的变更（可选）'
      }
    },
    additionalProperties: false
  }
};

// 工具调用结果示例（符合 MCP 2025-11-25 规范）
const successResult: ToolCallResult = {
  content: [
    { type: 'text', text: '// 文件内容...\nconst app = express();' }
  ],
  isError: false
};

const errorResult: ToolCallResult = {
  content: [
    { type: 'text', text: '错误：文件不存在 /path/to/file.ts' }
  ],
  isError: true                    // isError 标记错误结果
};

// 同时返回人类可读和机器可读内容
const structuredResult: ToolCallResult = {
  content: [
    { type: 'text', text: '找到3个匹配项' }
  ],
  structuredContent: {             // 机器可读的结构化数据
    matches: [
      { file: 'app.ts', line: 42, text: 'const app = express()' },
      { file: 'server.ts', line: 15, text: 'app.listen(3000)' },
      { file: 'routes.ts', line: 8, text: 'app.use(router)' }
    ],
    total: 3
  },
  isError: false
};
```

### MCP发现机制

> 💡 **白话理解**：MCP发现机制就像你到了一个新城市，打开手机上的美食App。App会自动列出附近所有餐厅（发现工具），你输入想吃什么（意图），App帮你筛选出最合适的餐厅（匹配工具），然后你下单（调用工具），最后收到外卖（返回结果）。

```typescript
class MCPToolDiscovery {
  private servers: Map<string, MCPServer> = new Map();
  private toolRegistry: Map<string, RegisteredTool> = new Map();
  
  // 注册MCP服务器
  async registerServer(serverId: string, server: MCPServer) {
    this.servers.set(serverId, server);
    
    // 发现该服务器提供的工具
    const tools = await server.discover();
    
    for (const tool of tools) {
      const toolId = `${serverId}:${tool.name}`;
      this.toolRegistry.set(toolId, {
        ...tool,
        serverId,
        toolId,
        fullName: toolId
      });
    }
    
    console.log(`Registered ${tools.length} tools from server ${serverId}`);
  }
  
  // 获取所有可用工具（用于构建System Prompt）
  getAllTools(): MCPTool[] {
    return Array.from(this.toolRegistry.values());
  }
  
  // 根据意图匹配最合适的工具
  async matchTool(intent: string, llm: LLMClient): Promise<MCPTool | null> {
    const tools = this.getAllTools();
    
    // 构建工具选择的Prompt
    const prompt = `
根据用户意图，选择最合适的工具。

可用工具列表：
${tools.map(t => `- ${t.name}: ${t.description}`).join('\n')}

用户意图：${intent}

请返回最匹配的工具名称，如果没有合适的工具返回 "none"。
`;

    const response = await llm.generate(prompt);
    const selectedToolName = response.trim();

    if (selectedToolName === 'none') {
      return null;
    }

    return this.toolRegistry.get(selectedToolName) || null;
  }

  // 执行工具调用（JSON-RPC 2.0 格式）
  async executeTool(
    toolId: string,
    args: Record<string, any>
  ): Promise<ToolCallResult> {
    const tool = this.toolRegistry.get(toolId);
    if (!tool) {
      throw new Error(`Unknown tool: ${toolId}`);
    }
    
    const server = this.servers.get(tool.serverId);
    if (!server) {
      throw new Error(`Server not found: ${tool.serverId}`);
    }
    
    // 验证参数（使用 inputSchema）
    const validatedArgs = this.validateArgs(args, tool.inputSchema);
    
    // 执行调用（JSON-RPC 2.0 格式）
    return await server.execute({
      method: 'tools/call',
      params: {
        name: tool.name,
        arguments: validatedArgs
      },
      id: generateUUID()
    });
  }
  
  private validateArgs(
    args: Record<string, any>, 
    schema: JSONSchema
  ): Record<string, any> {
    // 使用JSON Schema验证参数
    const validator = new JSONSchemaValidator(schema);
    const result = validator.validate(args);
    
    if (!result.valid) {
      throw new Error(`参数验证失败: ${result.errors.join(', ')}`);
    }
    
    return args;
  }
}
```

---

## 🔄 状态机调度（State Machine Orchestration）

> 💡 **实现说明**：下面的状态机描述的是 ReAct 循环的**概念模型**。在实际的 Claude Code SDK 实现中，并不存在一个显式的有限状态机类，而是通过 `session_id` 模型来管理会话状态。每次对话都有一个唯一的 `session_id`，SDK 通过这个 ID 追踪当前会话的上下文、历史消息和工具调用记录，从而隐式地维护了 ReAct 循环的状态流转。

### ReAct循环的实现

Claude Code SDK的核心是**ReAct（Reasoning + Acting）循环**，实现从思考到行动的闭环。

> 💡 **白话理解**：ReAct循环就像你修电脑的过程。你不会一上来就拆机箱，而是先想"可能是内存条松了"（推理），然后打开机箱检查（行动），看到内存条确实松了（观察），再想"插紧后还要检查其他部件吗"（推理），然后继续检查（行动），直到确认修好了（完成）。

### 状态转换图

下面是ReAct循环的完整状态转换图，展示了Agent在每个状态之间如何流转：

```
                    ReAct 状态转换图

                          ┌─────────┐
                          │  IDLE    │
                          │  空闲    │
                          └────┬─────┘
                               │
                     收到新任务 │
                               ▼
                       ┌──────────────┐
                  ┌──→│  THINKING     │←──────────────┐
                  │   │  推理阶段      │                │
                  │   └──────┬───────┘                │
                  │          │                        │
                  │    需要调用工具？                    │
                  │    ┌─否──┴──是──┐                  │
                  │    │            │                  │
                  │    ▼            ▼                  │
                  │  ┌────────┐  ┌──────────┐         │
                  │  │COMPLETED│ │ ACTING    │         │
                  │  │ 完成    │  │ 执行动作   │         │
                  │  └────────┘  └─────┬────┘         │
                  │                    │              │
                  │              动作执行完毕            │
                  │                    │              │
                  │                    ▼              │
                  │             ┌──────────┐          │
                  │             │ OBSERVING │          │
                  │             │ 观察结果   │          │
                  │             └─────┬────┘          │
                  │                    │              │
                  │              结果需要进一步处理？    │
                  │                    │              │
                  │              是 ───┘              │
                  │                    │              │
                  └────────────────────┘              │
                                                      │
                  ┌───────────────────────────────────┘
                  │
                  │  验证阶段（可选）
                  │
                  │    ┌──────────────┐
                  │    │  VERIFYING   │
                  │    │  验证结果     │
                  │    └──────┬───────┘
                  │           │
                  │     ┌─────┴──────┐
                  │     │            │
                  │  目标达成？   需要重新规划？
                  │     │            │
                  │     ▼            │
                  │  ┌────────┐     │
                  │  │COMPLETED│     │
                  │  │ 完成    │     │
                  │  └────────┘     │
                  │                  │
                  └──────────────────┘

  异常路径：
  ┌──────────┐         ┌──────────┐
  │ 任何状态  │──超时──→│  FAILED  │
  │          │──重试耗尽→│  失败    │
  └──────────┘         └──────────┘
  ┌──────────┐         ┌──────────┐
  │ VERIFYING │──需要人工→│  PAUSED  │
  │          │         │ 等待人工   │
  └──────────┘         └──────────┘
```

**状态说明：**

| 状态 | 含义 | 进入条件 | 离开条件 |
|------|------|----------|----------|
| IDLE | 空闲，等待任务 | 初始状态 | 收到新任务 |
| THINKING | 推理阶段，分析问题 | 收到任务或观察完结果 | 决定调用工具或直接回答 |
| ACTING | 执行动作，调用工具 | THINKING决定需要调用工具 | 工具返回结果 |
| OBSERVING | 观察结果 | 工具返回结果 | 分析完毕，准备下一轮推理 |
| VERIFYING | 验证结果 | ACTING完成后可选 | 目标达成或需要重新规划 |
| COMPLETED | 任务完成 | 目标达成 | 终态 |
| FAILED | 任务失败 | 超时或重试耗尽 | 终态 |
| PAUSED | 暂停等待人工 | 需要人工介入 | 人工恢复后回到THINKING |

```typescript
// ReAct状态定义
enum ReActState {
  THINKING = 'thinking',      // 推理阶段：分析问题、制定计划
  ACTING = 'acting',          // 行动阶段：调用工具
  OBSERVING = 'observing',    // 观察阶段：处理工具返回
  COMPLETED = 'completed',    // 任务完成
  FAILED = 'failed'           // 任务失败
}

interface ReActStep {
  stepNumber: number;
  state: ReActState;
  thought?: string;            // 思考内容
  action?: ToolCallRequest;    // 执行的动作（JSON-RPC 2.0 格式）
  observation?: ToolCallResult; // 观察结果（content 数组 + isError 标记）
  timestamp: Date;
}

class ReActLoop {
  private steps: ReActStep[] = [];
  private currentState: ReActState = ReActState.THINKING;
  private context: AgentContext;
  private llm: LLMClient;
  private toolDiscovery: MCPToolDiscovery;
  private maxSteps: number = 50;  // 防止无限循环
  
  constructor(
    context: AgentContext,
    llm: LLMClient,
    toolDiscovery: MCPToolDiscovery
  ) {
    this.context = context;
    this.llm = llm;
    this.toolDiscovery = toolDiscovery;
  }
  
  async run(userMessage: string): Promise<AgentResponse> {
    // 初始化对话
    this.context.addUserMessage(userMessage);
    
    while (this.currentState !== ReActState.COMPLETED && 
           this.currentState !== ReActState.FAILED) {
      
      // 检查最大步数
      if (this.steps.length >= this.maxSteps) {
        this.currentState = ReActState.FAILED;
        break;
      }
      
      // 执行当前状态
      switch (this.currentState) {
        case ReActState.THINKING:
          await this.think();
          break;
        case ReActState.ACTING:
          await this.act();
          break;
        case ReActState.OBSERVING:
          await this.observe();
          break;
      }
    }
    
    return this.buildResponse();
  }
  
  private async think() {
    // 构建包含工具信息的Prompt
    const tools = this.toolDiscovery.getAllTools();
    const availableTools = tools.map(t => ({
      name: t.name,
      description: t.description,
      inputSchema: t.inputSchema
    }));
    
    const prompt = `
你是一个AI助手，可以使用以下工具来完成任务：

${JSON.stringify(availableTools, null, 2)}

对话历史：
${this.formatConversationHistory()}

请分析当前情况，决定下一步：
1. 如果需要调用工具，请输出工具调用意图
2. 如果任务已完成，请输出最终答案
3. 格式要求：
   - 工具调用: {"action": "tool_name", "args": {...}}
   - 完成: {"final_answer": "..."}
`;
    
    const response = await this.llm.generate(prompt);
    
    // 解析LLM输出
    const parsed = this.parseLLMResponse(response);
    
    this.steps.push({
      stepNumber: this.steps.length + 1,
      state: ReActState.THINKING,
      thought: parsed.thought,
      timestamp: new Date()
    });
    
    // 根据解析结果决定下一步状态
    if (parsed.finalAnswer) {
      this.context.finalAnswer = parsed.finalAnswer;
      this.currentState = ReActState.COMPLETED;
    } else if (parsed.action) {
      this.context.pendingAction = parsed.action;
      this.currentState = ReActState.ACTING;
    }
  }
  
  private async act() {
    const action = this.context.pendingAction;
    if (!action) {
      throw new Error('No pending action');
    }
    
    // 执行工具调用（JSON-RPC 2.0 格式）
    const result = await this.toolDiscovery.executeTool(
      action.params.name,
      action.params.arguments
    );
    
    this.context.lastObservation = result;
    
    this.steps.push({
      stepNumber: this.steps.length + 1,
      state: ReActState.ACTING,
      action: {
        method: 'tools/call',
        params: {
          name: action.params.name,
          arguments: action.params.arguments
        },
        id: generateUUID()
      },
      timestamp: new Date()
    });
    
    this.currentState = ReActState.OBSERVING;
  }
  
  private async observe() {
    const observation = this.context.lastObservation;
    
    this.steps.push({
      stepNumber: this.steps.length + 1,
      state: ReActState.OBSERVING,
      observation,
      timestamp: new Date()
    });
    
    // 将观察结果加入上下文
    this.context.addObservation(observation);
    
    // 回到思考阶段
    this.currentState = ReActState.THINKING;
  }
  
  private formatConversationHistory(): string {
    // 格式化对话历史，包括之前的思考、行动和观察
    return this.steps.map(step => {
      if (step.thought) {
        return `思考: ${step.thought}`;
      } else if (step.action) {
        return `行动: 调用 ${step.action.params.name}`;
      } else if (step.observation) {
        return `观察: ${JSON.stringify(step.observation.content)}`;
      }
      return '';
    }).filter(Boolean).join('\n');
  }
  
  private parseLLMResponse(response: string) {
    try {
      return JSON.parse(response);
    } catch {
      // 如果不是JSON，尝试提取信息
      const actionMatch = response.match(/action["\']?\s*:\s*["\']?(\w+)/);
      const answerMatch = response.match(/final_answer["\']?\s*:\s*["\']?([^"\']+)/);
      
      return {
        thought: response,
        action: actionMatch ? { tool: actionMatch[1] } : undefined,
        finalAnswer: answerMatch ? answerMatch[1] : undefined
      };
    }
  }
  
  private buildResponse(): AgentResponse {
    return {
      answer: this.context.finalAnswer || '任务未完成',
      steps: this.steps,
      toolCalls: this.steps.filter(s => s.action).length,
      totalTime: Date.now() - this.context.startTime
    };
  }
}
```

---

## 💾 会话管理与持久化

### Session架构

> 💡 **白话理解**：Session就像你的聊天记录本。每次对话都记录在里面，包括你说了什么、AI回了什么、调用了哪些工具、返回了什么结果。如果对话太长，记录本写不下了，就把前面的内容压缩成摘要，只保留最近几页的详细内容。这样AI就不会"失忆"，也不会因为信息太多而"脑子不够用"。

```typescript
interface Session {
  id: string;                    // Session唯一ID
  userId: string;                // 用户ID
  createdAt: Date;
  updatedAt: Date;
  messages: Message[];           // 对话消息历史
  state: SessionState;           // 会话状态
  metadata: SessionMetadata;     // 元数据
  checkpoint?: Checkpoint;       // 检查点（用于恢复）
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp: Date;
  metadata?: {
    toolCall?: ToolCallRequest;   // 工具调用信息（JSON-RPC 2.0 格式）
    toolResult?: ToolCallResult;  // 工具返回结果（content 数组 + isError 标记）
    tokenCount?: number;          // Token使用量
  };
}

interface SessionState {
  variables: Record<string, any>;  // 会话变量
  workingDirectory: string;         // 当前工作目录
  environment: Record<string, string>;  // 环境变量
}

class SessionManager {
  private storage: SessionStorage;
  private activeSessions: Map<string, Session> = new Map();
  private config: SessionConfig;
  
  constructor(storage: SessionStorage, config: SessionConfig) {
    this.storage = storage;
    this.config = config;
  }
  
  // 创建新会话
  async createSession(userId: string, initialContext?: any): Promise<Session> {
    const session: Session = {
      id: generateUUID(),
      userId,
      createdAt: new Date(),
      updatedAt: new Date(),
      messages: [],
      state: {
        variables: initialContext || {},
        workingDirectory: process.cwd(),
        environment: { ...process.env }
      },
      metadata: {
        version: '1.0',
        clientInfo: {}
      }
    };
    
    // 保存到存储
    await this.storage.save(session);
    this.activeSessions.set(session.id, session);
    
    return session;
  }
  
  // 加载会话
  async loadSession(sessionId: string): Promise<Session | null> {
    // 先检查活跃会话
    if (this.activeSessions.has(sessionId)) {
      return this.activeSessions.get(sessionId)!;
    }
    
    // 从存储加载
    const session = await this.storage.load(sessionId);
    if (session) {
      this.activeSessions.set(sessionId, session);
    }
    
    return session;
  }
  
  // 添加消息
  async addMessage(
    sessionId: string, 
    message: Omit<Message, 'id' | 'timestamp'>
  ): Promise<Message> {
    const session = await this.loadSession(sessionId);
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }
    
    const newMessage: Message = {
      ...message,
      id: generateUUID(),
      timestamp: new Date()
    };
    
    session.messages.push(newMessage);
    session.updatedAt = new Date();
    
    // 检查上下文长度，必要时压缩
    if (this.estimateTokenCount(session.messages) > this.config.maxContextTokens) {
      await this.compressContext(session);
    }
    
    // 保存会话
    await this.storage.save(session);
    
    return newMessage;
  }
  
  // 上下文压缩
  // 注意：Claude Code SDK 内置了自动压缩（compaction）机制，
  // 当对话 token 数超过阈值时会自动触发压缩，无需手动调用。
  // 下面的 compressContext 方法展示了压缩的基本逻辑，
  // 实际产品中 SDK 会在 token 阈值触发时自动执行。
  private async compressContext(session: Session) {
    // 保留最近的消息
    const recentMessages = session.messages.slice(-this.config.keepRecentMessages);
    
    // 压缩更早的消息
    const olderMessages = session.messages.slice(
      0, 
      -this.config.keepRecentMessages
    );
    
    if (olderMessages.length > 0) {
      // 使用轻量级模型生成摘要
      const summary = await this.summarizeMessages(olderMessages);
      
      // 替换为摘要消息
      session.messages = [
        {
          id: generateUUID(),
          role: 'system',
          content: `[历史对话摘要] ${summary}`,
          timestamp: new Date()
        },
        ...recentMessages
      ];
    }
  }
  
  private async summarizeMessages(messages: Message[]): Promise<string> {
    const prompt = `
请总结以下对话的核心内容，保留关键事实和决策：

${messages.map(m => `${m.role}: ${m.content}`).join('\n')}

请用一段话总结：
`;
    
    // 使用轻量级模型进行摘要
    return await this.llm.generate(prompt, { model: 'lightweight' });
  }
  
  private estimateTokenCount(messages: Message[]): number {
    // 简化的Token估算（实际应使用tokenizer）
    return messages.reduce((sum, m) => 
      sum + Math.ceil(m.content.length / 4), 0
    );
  }
}
```

> 💡 **白话理解**：上下文压缩就像你读一本很长的书。你不可能逐字记住每一页，所以你会对前面的章节做个摘要（"第一章讲了主角出生，第二章讲了主角上学"），然后对最近几页逐字细读。这样既不会丢失关键信息，又不会超出你的记忆容量。SessionManager做的就是这个工作：当对话太长时，把早期消息压缩成摘要，只保留最近的消息原文。在 Claude Code SDK 中，这个过程是**自动触发**的，当对话 token 数超过阈值时，SDK 会自动执行压缩（compaction），不需要开发者手动管理。

### 持久化存储实现

> 💡 **白话理解**：持久化存储就像把聊天记录保存到云端。你关掉聊天窗口后，下次打开还能看到之前的对话。Redis就像一个超快的备忘录，读写速度极快，适合存储需要频繁访问的会话数据。

```typescript
interface SessionStorage {
  save(session: Session): Promise<void>;
  load(sessionId: string): Promise<Session | null>;
  delete(sessionId: string): Promise<void>;
  list(userId?: string): Promise<Session[]>;
}

// Redis实现
class RedisSessionStorage implements SessionStorage {
  private redis: RedisClient;
  private keyPrefix: string = 'claude:session:';
  
  constructor(redisUrl: string) {
    this.redis = new Redis(redisUrl);
  }
  
  async save(session: Session): Promise<void> {
    const key = `${this.keyPrefix}${session.id}`;
    const value = JSON.stringify(session);
    
    // 使用Hash存储Session数据
    await this.redis.hset(key, {
      data: value,
      userId: session.userId,
      updatedAt: session.updatedAt.toISOString()
    });
    
    // 设置TTL（30天）
    await this.redis.expire(key, 30 * 24 * 3600);
    
    // 维护用户的Session索引
    await this.redis.sadd(
      `${this.keyPrefix}user:${session.userId}`,
      session.id
    );
  }
  
  async load(sessionId: string): Promise<Session | null> {
    const key = `${this.keyPrefix}${sessionId}`;
    const data = await this.redis.hget(key, 'data');
    
    if (!data) {
      return null;
    }
    
    return JSON.parse(data) as Session;
  }
  
  async delete(sessionId: string): Promise<void> {
    const session = await this.load(sessionId);
    if (session) {
      const key = `${this.keyPrefix}${sessionId}`;
      await this.redis.del(key);
      
      // 从用户索引中移除
      await this.redis.srem(
        `${this.keyPrefix}user:${session.userId}`,
        sessionId
      );
    }
  }
  
  async list(userId?: string): Promise<Session[]> {
    if (!userId) {
      // 获取所有Session（仅用于管理）
      const keys = await this.redis.keys(`${this.keyPrefix}*`);
      const sessions = await Promise.all(
        keys.map(key => this.load(key.replace(this.keyPrefix, '')))
      );
      return sessions.filter((s): s is Session => s !== null);
    }
    
    // 获取特定用户的Session
    const sessionIds = await this.redis.smembers(
      `${this.keyPrefix}user:${userId}`
    );
    
    const sessions = await Promise.all(
      sessionIds.map(id => this.load(id))
    );
    
    return sessions.filter((s): s is Session => s !== null);
  }
}
```

---

## 📁 SDK 分析性文件结构

> ⚠️ **说明**：以下是基于 MCP 协议规范和 Agent SDK 公开接口分析得出的**推测性结构示例**，并非 Claude Code 的实际源码目录。Claude Code 的实际源码未公开，此结构仅用于帮助理解一个完整的 Agent SDK 可能包含哪些模块。

```
# 分析性结构示例（非真实源码）
claude-agent-analysis/
├── src/
│   ├── core/
│   │   ├── index.ts                    # SDK入口
│   │   ├── agent.ts                    # Agent主类
│   │   └── config.ts                   # 配置管理
│   │
│   ├── mcp/
│   │   ├── protocol.ts                 # MCP协议定义
│   │   ├── server.ts                   # MCP服务器基类
│   │   ├── discovery.ts                # 工具发现
│   │   └── client.ts                   # MCP客户端
│   │
│   ├── react/
│   │   ├── loop.ts                     # ReAct循环实现
│   │   ├── state.ts                    # 状态管理
│   │   └── types.ts                    # 类型定义
│   │
│   ├── session/
│   │   ├── manager.ts                  # Session管理器
│   │   ├── storage.ts                  # 存储接口
│   │   ├── redis.ts                    # Redis实现
│   │   └── compression.ts              # 上下文压缩
│   │
│   ├── tools/
│   │   ├── builtin/                    # 内置工具
│   │   │   ├── file.ts                 # 文件操作
│   │   │   ├── git.ts                  # Git命令
│   │   │   ├── search.ts               # 代码搜索
│   │   │   └── bash.ts                 # 命令执行
│   │   └── registry.ts                 # 工具注册表
│   │
│   ├── llm/
│   │   ├── client.ts                   # LLM客户端
│   │   ├── anthropic.ts                # Anthropic Claude
│   │   └── types.ts                    # LLM类型定义
│   │
│   └── utils/
│       ├── tokenizer.ts                # Token计算
│       ├── logger.ts                   # 日志
│       └── errors.ts                   # 错误处理
│
├── prompts/
│   ├── system.txt                      # 系统Prompt
│   ├── react.txt                       # ReAct Prompt模板
│   └── tools/                          # 工具特定Prompt
│       ├── file.txt
│       ├── git.txt
│       └── ...
│
├── config/
│   ├── mcp.json                        # MCP工具定义
│   ├── skills/                         # Skills配置
│   └── permissions.json                # 权限配置
│
└── storage/                            # 本地存储（开发模式）
    ├── sessions/                       # Session数据
    └── logs/                           # 日志文件
```

---

## 💡 理解要点

理解Claude Code SDK底层原理，可以从以下层次展开：

### 1. 宏观层面
"Claude Code SDK是**大模型与外部环境之间的桥梁**，核心职责是：
- 让LLM能够**发现和调用**外部工具
- 维护**多轮对话**的状态
- 提供**可扩展**的工具接入机制"

### 2. 协议层面
"SDK基于**MCP（Model Context Protocol）协议**，MCP 基于 **JSON-RPC 2.0**，定义了：
- 工具的标准化描述格式（`inputSchema`，JSON Schema格式）
- 工具发现机制（`tools/list`、`resources/list`、`prompts/list`）
- 调用和返回的数据格式（`tools/call`，结果使用 `content` 数组 + `isError` 标记）
- 传输层支持 stdio 和 Streamable HTTP"

### 3. 架构层面
"核心架构包含**三层**：
- **协议层**：MCP工具定义与发现
- **状态层**：ReAct循环 + Session管理
- **持久层**：对话历史存储 + 上下文压缩"

### 4. 细节层面
可以补充：
- 上下文压缩策略（SDK内置自动compaction + 手动滑动窗口）
- 工具选择的置信度机制
- 错误处理和降级策略
- MCP的JSON-RPC 2.0传输机制（stdio vs Streamable HTTP）

---

## 📝 学习检查清单

阅读完本文后，你应该能够回答以下问题。如果某个问题答不上来，建议回到对应章节重新阅读：

1. **MCP协议解决了什么问题？** 如果没有MCP，每新增一个工具需要做什么？有了MCP之后呢？

2. **MCP的四个核心组件（工具定义、调用请求、调用结果、服务器接口）分别对应USB协议中的什么？** 提示：想想设备描述、数据传输、状态反馈、设备驱动。注意MCP基于JSON-RPC 2.0，工具定义使用`inputSchema`，调用结果使用`content`数组加`isError`标记。

3. **ReAct循环中，THINKING状态有两条出路（调用工具或直接回答），是什么决定了走哪条路？** 如果LLM的输出解析失败会怎样？

4. **状态转换图中，VERIFYING状态可以回到THINKING，这个设计解决了什么问题？** 如果没有这个回路会怎样？

5. **上下文压缩的策略是"保留最近消息+压缩早期消息"，为什么不全压缩或全保留？** 各有什么问题？

6. **Redis存储Session时，为什么要同时维护一个用户索引（`user:{userId}`的Set）？** 直接用key前缀查询不行吗？

7. **MCP发现机制中，`matchTool`方法让LLM来选择工具，这有什么优缺点？** 有没有更高效的选择方式？

8. **如果ReAct循环达到了maxSteps（50步）还没完成，系统会怎么处理？** 这和前面学到的LoopDetector有什么关系？

---

> **上一篇**：[Subagent协作与代码评审设计](./02-subagent-code-review.md)
> **下一篇**：[Claude Code相关技术对比与深度问题](../04-comparative-analysis/01-claude-comparison.md)