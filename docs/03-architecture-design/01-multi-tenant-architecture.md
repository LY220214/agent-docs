# SDK轻量化重构与多租户架构

> 深度解析Claude Code SDK的轻量化改造与大规模部署架构  
> 难度：⭐⭐⭐⭐⭐  
> 核心概念：Harness抽象、多租户网关、上下文压缩、高可用设计

---

## 📖 阅读前你需要知道

在阅读本文之前，建议你了解以下概念：

- **SDK（Software Development Kit）**：软件开发工具包，就像给你一套现成的积木，你可以直接拼装而不需要自己从零开始削木头
- **CLI（Command Line Interface）**：命令行工具，就是在终端里敲命令用的程序，比如 `git`、`npm`
- **多租户（Multi-Tenant）**：一套系统同时服务多个客户，每个客户的数据互相隔离。下文有详细解释
- **MCP协议**：Model Context Protocol，AI模型与外部工具通信的标准协议，可以理解为AI的"USB接口"
- **ReAct循环**：一种AI推理模式，先思考（Reason），再行动（Act），观察结果后继续思考，循环往复直到任务完成
- **上下文压缩**：当对话历史太长时，把旧内容压缩成摘要，只保留最近的消息，类似你看书时只记笔记而不背全文

如果你对这些概念还不太熟悉，别担心，本文会在遇到时用通俗的方式解释。

---

## 🏢 多租户是什么？

> 💡 **白话理解**：想象一栋写字楼，不同公司租不同楼层。每家公司有自己的门禁卡，只能进自己的楼层；每层的装修风格、办公设备都由租户自己决定；物业负责整栋楼的电梯、水电等公共设施。租户之间互不干扰，但共享同一栋楼的基础设施。

在软件世界里，"多租户"就是：

- **一栋楼** = 一套后端服务
- **不同楼层** = 不同团队/公司的独立空间
- **门禁卡** = 租户ID + 权限验证
- **物业** = 网关层（负责路由、限流、隔离）
- **互不干扰** = 数据隔离、权限隔离、资源隔离

**为什么需要多租户？** 假设你们公司有100个开发团队同时使用AI助手。如果每个团队都部署一套独立的后端服务，那运维成本会爆炸。多租户架构让100个团队共享同一套服务，但每个团队只能看到和操作自己的数据，就像100家公司共用一栋写字楼，但彼此互不干扰。

---

## 📋 学习要点

本节涵盖两个核心主题：
1. **SDK轻量化重构**：为什么需要替换官方SDK，以及如何重构
2. **多租户架构**：多租户多轮对话后端的实现方案

---

## 🎯 为什么替换官方SDK？

### 官方CLI的问题

```
官方Claude Code CLI的问题：
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  ❌ 问题1: TUI交互逻辑臃肿                                   │
│     - 大量终端UI渲染代码                                      │
│     - 难以与后端服务集成                                      │
│     - 交互逻辑与业务逻辑耦合                                  │
│                                                            │
│  ❌ 问题2: 资源预加载过多                                     │
│     - 启动时加载所有Tools                                     │
│     - 内存占用高                                             │
│     - 冷启动慢（5-10秒）                                     │
│                                                            │
│  ❌ 问题3: 难以嵌入分布式后端                                 │
│     - 设计为单机CLI工具                                       │
│     - 无状态管理                                             │
│     - 不支持水平扩展                                         │
│                                                            │
│  ❌ 问题4: 权限控制粒度粗                                     │
│     - 全局统一的权限配置                                      │
│     - 无法针对不同用户动态调整                                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 重构前后对比（更清晰的视图）

> 💡 **白话理解**：官方CLI就像一辆房车，厨房、卧室、客厅全塞在一起，开起来很重。我们把它拆成核心引擎（Harness）和可选配件，就像把房车改造成模块化卡车，需要什么装什么，轻装上阵。

```
重构前 vs 重构后 —— 逐层对比：

┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  【重构前：官方CLI】              【重构后：轻量化SDK】                  │
│                                                                      │
│  ┌────────────────────┐          ┌────────────────────┐              │
│  │  TUI渲染层          │          │                    │              │
│  │  （终端交互界面）    │  ❌ 剥离  │  后端网关层         │              │
│  │  · 光标控制         │ ────────→ │  （HTTP API接口）   │              │
│  │  · 颜色渲染         │          │  · RESTful接口      │              │
│  │  · 键盘监听         │          │  · WebSocket流式    │              │
│  └────────────────────┘          └────────────────────┘              │
│                                                                      │
│  ┌────────────────────┐          ┌────────────────────┐              │
│  │  命令解析层          │          │  Harness抽象层      │              │
│  │  （CLI参数处理）    │  ❌ 剥离  │  （核心引擎）        │              │
│  │  · /help, /clear   │ ────────→ │  · Agent控制器     │              │
│  │  · 参数校验         │          │  · MCP接口栈        │              │
│  │  · 命令路由         │          │  · Prompt管理       │              │
│  └────────────────────┘          │  · 会话管理         │              │
│                                  └────────────────────┘              │
│  ┌────────────────────┐                                               │
│  │  Agent Loop         │          （以上两层保留，是核心能力）            │
│  │  （状态机）         │  ✅ 保留                                       │
│  └────────────────────┘                                               │
│                                                                      │
│  ┌────────────────────┐          ┌────────────────────┐              │
│  │  MCP协议栈           │          │  MCP协议栈          │              │
│  │  （工具通信）        │  ✅ 保留  │  （工具通信）        │              │
│  └────────────────────┘          └────────────────────┘              │
│                                                                      │
│  ┌────────────────────┐          ┌────────────────────┐              │
│  │  工具预加载          │          │  LLM客户端          │              │
│  │  （启动时全部加载）  │  ❌ 改为   │  （按需连接）        │              │
│  │  · 50+工具全量加载  │  懒加载   │  · 用到才加载        │              │
│  │  · 内存500MB+      │ ────────→ │  · 内存仅50MB      │              │
│  │  · 启动5-10秒      │          │  · 启动<500ms       │              │
│  └────────────────────┘          └────────────────────┘              │
│                                                                      │
│  关键变化：                                                          │
│  · 去掉了"只给终端看"的UI代码 → 换成"给后端用"的API接口               │
│  · 去掉了"启动就全加载" → 换成"用到才加载"的懒加载机制                │
│  · 保留了核心推理能力（Agent Loop + MCP）不变                        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 轻量化重构方案

#### 核心思想：Harness抽象

将"推理执行"与"交互逻辑"彻底分离，只保留核心能力：

```
重构前后对比：

【重构前 - 官方CLI】                【重构后 - 轻量化SDK】
┌─────────────────────┐           ┌─────────────────────┐
│   TUI渲染层          │           │                     │
│   (终端交互)         │   ❌ 剥离  │   后端网关层         │
├─────────────────────┤           │   (HTTP API)        │
│   命令解析层         │           ├─────────────────────┤
│   (CLI参数)         │   ❌ 剥离  │   Harness抽象层      │
├─────────────────────┤           │   (核心引擎)         │
│   Agent Loop        │           │   • Agent控制器      │
│   (状态机)          │   ✅ 保留  │   • MCP接口栈        │
├─────────────────────┤           │   • Prompt管理       │
│   MCP协议栈          │   ✅ 保留  │   • 会话管理         │
├─────────────────────┤           ├─────────────────────┤
│   工具预加载         │   ❌ 懒加载 │   LLM客户端         │
│   (全部加载)         │           │   (按需连接)         │
└─────────────────────┘           └─────────────────────┘
```

#### Harness架构设计

> 💡 **白话理解**：Harness就像一个"万能遥控器"。你不需要知道电视、空调、音响各自怎么工作，只需要按遥控器上的按钮。Harness把复杂的AI推理过程封装起来，对外只暴露简单的接口：初始化、执行对话、流式输出、管理会话。

```typescript
// Harness核心接口
interface ClaudeCodeHarness {
  // 初始化（轻量级）—— 就像开机，只建立基本连接
  initialize(config: HarnessConfig): Promise<void>;
  
  // 执行单次对话 —— 就像对遥控器说"换台"，它帮你完成整个操作
  execute(
    sessionId: string,
    message: string,
    context?: ExecutionContext
  ): Promise<ExecutionResult>;
  
  // 流式执行 —— 就像看直播，内容一段一段实时推送给你
  executeStream(
    sessionId: string,
    message: string,
    callbacks: StreamCallbacks
  ): Promise<void>;
  
  // 工具管理（懒加载）—— 需要什么工具才加载什么，不提前占内存
  registerTool(tool: ToolDefinition): void;
  loadTools(toolNames: string[]): Promise<void>;
  
  // 会话管理 —— 管理每个用户的对话状态
  createSession(config: SessionConfig): Promise<string>;
  destroySession(sessionId: string): Promise<void>;
}

// Harness配置
interface HarnessConfig {
  // LLM配置 —— 连哪个AI模型，用什么密钥
  llm: {
    provider: 'anthropic' | 'openai';
    apiKey: string;
    model: string;
    maxTokens: number;
  };
  
  // 工具配置（按需加载）—— 哪些工具一开始就加载，哪些用到才加载
  tools: {
    builtin: string[];      // 内置工具列表
    custom: ToolConfig[];   // 自定义工具
    lazyLoad: boolean;      // 是否懒加载（推荐开启）
  };
  
  // 会话配置 —— 对话历史存在哪，最多保留多少上下文
  session: {
    storage: 'memory' | 'redis';
    maxContextTokens: number;
    compressionThreshold: number;
  };
  
  // 权限配置（支持动态调整）—— 不同用户能做什么
  permissions: PermissionConfig;
}
```

#### 核心实现代码

> 💡 **白话理解**：下面这段代码是轻量化SDK的"心脏"。它做了几件关键的事：启动时只建立基本连接（不加载所有工具），执行时才按需加载需要的工具，用完就释放。这就像你不会一次性打开手机上所有App，而是需要哪个开哪个。

```typescript
class LightweightHarness implements ClaudeCodeHarness {
  private config: HarnessConfig;
  private llmClient: LLMClient;
  private toolRegistry: ToolRegistry;
  private sessionManager: SessionManager;
  private reactLoop: ReActLoop;
  private initialized = false;
  
  // 启动时间：~200ms（相比官方的5-10秒）
  // 为什么这么快？因为我们只建立连接，不加载工具
  async initialize(config: HarnessConfig): Promise<void> {
    this.config = config;
    
    // 1. 初始化LLM客户端（仅建立连接，不发送请求）
    this.llmClient = this.createLLMClient(config.llm);
    
    // 2. 初始化工具注册表（不加载具体工具，只记录有哪些工具可用）
    this.toolRegistry = new ToolRegistry({
      lazyLoad: config.tools.lazyLoad
    });
    
    // 3. 注册工具定义（仅元数据，不加载实现代码）
    // 就像餐厅菜单上写了有哪些菜，但厨房还没开始做
    for (const toolName of config.tools.builtin) {
      const toolDef = await this.loadToolDefinition(toolName);
      this.toolRegistry.register(toolDef);
    }
    
    // 4. 初始化会话管理器（负责记住每个用户的对话状态）
    this.sessionManager = new SessionManager({
      storage: config.session.storage
    });
    
    // 5. 初始化ReAct循环（轻量级状态机，AI推理的核心引擎）
    this.reactLoop = new ReActLoop({
      llmClient: this.llmClient,
      toolRegistry: this.toolRegistry,
      maxIterations: 50
    });
    
    this.initialized = true;
    console.log('Harness initialized in', Date.now() - startTime, 'ms');
  }
  
  // 执行一次对话：加载会话 → 预测需要哪些工具 → 执行推理 → 保存状态
  async execute(
    sessionId: string,
    message: string,
    context?: ExecutionContext
  ): Promise<ExecutionResult> {
    if (!this.initialized) {
      throw new Error('Harness not initialized');
    }
    
    // 1. 加载会话（从Redis或内存中恢复之前的对话状态）
    const session = await this.sessionManager.load(sessionId);
    
    // 2. 按需加载工具（根据用户消息预测需要哪些工具，只加载这些）
    const requiredTools = await this.predictRequiredTools(message);
    await this.loadTools(requiredTools);
    
    // 3. 执行ReAct循环（AI思考→调用工具→观察结果→再思考，直到得出答案）
    const result = await this.reactLoop.run({
      session,
      message,
      context
    });
    
    // 4. 保存会话状态（下次对话时能接着聊）
    await this.sessionManager.save(session);
    
    return result;
  }
  
  // 工具懒加载：只加载还没加载过的工具
  private async loadTools(toolNames: string[]): Promise<void> {
    const unloadedTools = toolNames.filter(
      name => !this.toolRegistry.isLoaded(name)
    );
    
    for (const toolName of unloadedTools) {
      const toolImpl = await this.loadToolImplementation(toolName);
      this.toolRegistry.load(toolName, toolImpl);
    }
  }
  
  // 智能工具预测（减少不必要的加载）
  // 三种方式综合判断：关键词匹配 + 历史模式 + AI意图识别
  private async predictRequiredTools(message: string): Promise<string[]> {
    // 基于关键词匹配（比如消息里有"搜索"就加载搜索工具）
    const keywords = this.extractKeywords(message);
    
    // 基于历史模式（这个用户之前常用哪些工具）
    const historicalPattern = await this.sessionManager.getToolUsagePattern();
    
    // 基于LLM意图识别（用轻量级模型判断用户想做什么）
    const intent = await this.classifyIntent(message);
    
    // 合并预测结果（三种方式投票，取交集和并集的平衡）
    return this.mergePredictions(keywords, historicalPattern, intent);
  }
}
```

### 重构收益

| 指标 | 重构前 | 重构后 | 提升 |
|------|--------|--------|------|
| **冷启动时间** | 5-10秒 | <500ms | **90%+** |
| **内存占用** | 500MB+ | 50MB | **90%** |
| **代码体积** | 完整CLI | 核心SDK | **70%** |
| **可嵌入性** | ❌ CLI工具 | ✅ 库/服务 | - |
| **水平扩展** | ❌ 单机 | ✅ 分布式 | - |

### 🏗️ 真实场景：100个开发团队同时使用AI助手

> 💡 **白话理解**：假设你们公司有100个开发团队同时使用AI助手。如果没有多租户架构，每个团队要么共享一个AI（互相能看到对方的代码，安全风险巨大），要么各自部署一套（运维成本爆炸）。多租户架构让100个团队共享同一套后端，但数据完全隔离。

```
场景：公司有100个开发团队，每个团队10-50人

没有多租户架构时：
┌────────────────────────────────────────────────────────────┐
│  方案A：每个团队独立部署                                      │
│  · 100套后端服务 → 运维成本爆炸                               │
│  · 100个Redis实例 → 资源浪费                                  │
│  · 版本管理混乱 → 升级噩梦                                    │
│                                                            │
│  方案B：共享一个实例                                          │
│  · 团队A能看到团队B的代码 → 安全事故                           │
│  · 一个团队的高峰影响所有团队 → 性能问题                       │
│  · 无法按团队限流 → 资源争抢                                  │
└────────────────────────────────────────────────────────────┘

有多租户架构后：
┌────────────────────────────────────────────────────────────┐
│  · 1套后端服务，100个租户隔离                                 │
│  · 每个团队只能看到自己的数据（租户隔离）                       │
│  · 按团队独立限流（团队A用多了不影响团队B）                    │
│  · 统一升级，一次部署全部生效                                  │
│  · 按团队统计用量，方便内部结算                                │
└────────────────────────────────────────────────────────────┘
```

---

## 🎯 多租户与大规模会话后端实现

### 架构概览

> 💡 **白话理解**：这个架构就像一个大型商场。API Gateway是商场大门的保安，检查你的会员卡（认证鉴权）和购物袋大小（限流熔断），然后指引你去正确的楼层（路由分发）。Go Gateway是商场管理办公室，负责记住每个顾客的购物偏好（Session管理）、确保不同品牌的店铺互不干扰（多租户隔离）、控制谁能进哪个仓库（权限控制）。Redis是商场的储物柜，LLM Pool是商场里的AI导购员团队，MCP Pool是各种专业服务柜台。

```
┌─────────────────────────────────────────────────────────────────────┐
│                        多租户Agent网关架构                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐       │
│   │   用户A      │     │   用户B      │     │   用户C      │       │
│   │  (Team A)    │     │  (Team B)    │     │  (Team C)    │       │
│   └──────┬───────┘     └──────┬───────┘     └──────┬───────┘       │
│          │                    │                    │               │
│          └────────────────────┼────────────────────┘               │
│                               │                                     │
│                    ┌──────────┴──────────┐                         │
│                    │   API Gateway       │                         │
│                    │   (Kong/Nginx)      │                         │
│                    │                     │                         │
│                    │ • 认证鉴权           │                         │
│                    │ • 限流熔断           │                         │
│                    │ • 路由分发           │                         │
│                    └──────────┬──────────┘                         │
│                               │                                     │
│                    ┌──────────┴──────────┐                         │
│                    │   Go Gateway        │                         │
│                    │   (核心业务逻辑)      │                         │
│                    │                     │                         │
│                    │ • Session管理        │                         │
│                    │ • 多租户隔离         │                         │
│                    │ • 权限控制           │                         │
│                    │ • 上下文压缩         │                         │
│                    └──────────┬──────────┘                         │
│                               │                                     │
│           ┌───────────────────┼───────────────────┐                │
│           │                   │                   │                │
│           ▼                   ▼                   ▼                │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐          │
│   │   Redis      │   │   LLM Pool   │   │   MCP Pool   │          │
│   │  (Session)   │   │  (Claude)    │   │  (Tools)     │          │
│   └──────────────┘   └──────────────┘   └──────────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Go Gateway核心实现

> 💡 **白话理解**：下面这段Go代码是多租户网关的核心实现。每个函数都有中文注释解释它的作用，帮助你理解"这段代码在干什么"以及"为什么要这样写"。

```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis/v8"
)

// Session定义 —— 一个会话就是一次完整的对话过程
// 就像你去理发店，从进门到离开，Tony老师记住你的所有要求
type Session struct {
	ID        string                 `json:"id"`        // 会话唯一标识
	UserID    string                 `json:"user_id"`   // 哪个用户的会话
	TenantID  string                 `json:"tenant_id"` // 哪个租户（团队）的会话
	Messages  []Message              `json:"messages"`  // 对话消息列表
	State     map[string]interface{} `json:"state"`     // 会话状态（比如当前在做什么任务）
	CreatedAt time.Time              `json:"created_at"`
	UpdatedAt time.Time              `json:"updated_at"`
	ExpiresAt time.Time              `json:"expires_at"` // 过期时间，超时自动清理
}

// Message定义 —— 对话中的一条消息
type Message struct {
	ID        string                 `json:"id"`
	Role      string                 `json:"role"` // user=用户说的, assistant=AI回复的, system=系统指令, tool=工具返回
	Content   string                 `json:"content"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"` // 附加信息（如工具调用详情）
	Timestamp time.Time              `json:"timestamp"`
}

// 多租户网关 —— 整个系统的"大管家"
// 负责管理所有租户的会话、权限、上下文压缩等
type MultiTenantGateway struct {
	redis      *redis.Client          // Redis：用来存储会话数据（快速读写）
	harness    *ClaudeCodeHarness     // Harness：AI推理引擎
	compressor *ContextCompressor     // 上下文压缩器：对话太长时自动压缩
}

// NewGateway —— 创建网关实例
// 就像开一家新商场，需要准备好储物柜（Redis）、导购员（Harness）、压缩机器（Compressor）
func NewGateway(redisURL string) (*MultiTenantGateway, error) {
	// 初始化Redis连接 —— 连接数据存储
	opt, err := redis.ParseURL(redisURL)
	if err != nil {
		return nil, err
	}
	rdb := redis.NewClient(opt)

	// 初始化Harness —— 准备AI推理引擎
	harness, err := NewHarness(HarnessConfig{
		// ... 配置
	})
	if err != nil {
		return nil, err
	}

	// 初始化上下文压缩器 —— 对话太长时自动压缩历史
	compressor := NewContextCompressor(Config{
		Model:              "lightweight",  // 用轻量级模型做压缩，省钱
		CompressionRatio: 0.5,             // 压缩到原来的一半
		MinMessages:      20,              // 至少20条消息才开始压缩
	})

	return &MultiTenantGateway{
		redis:      rdb,
		harness:    harness,
		compressor: compressor,
	}, nil
}

// CreateSession —— 创建新会话
// 就像顾客进商场，给他发一张会员卡，记录他的信息
func (g *MultiTenantGateway) CreateSession(
	ctx context.Context,
	userID string,
	tenantID string,
) (*Session, error) {
	session := &Session{
		ID:        generateUUID(),
		UserID:    userID,
		TenantID:  tenantID,
		Messages:  []Message{},
		State:     make(map[string]interface{}),
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		ExpiresAt: time.Now().Add(24 * time.Hour), // 24小时过期
	}

	// 保存到Redis（使用租户隔离的Key）
	// Key格式：tenant:{租户ID}:session:{会话ID}
	// 这样不同租户的会话数据在Redis中天然隔离
	key := g.sessionKey(tenantID, session.ID)
	data, err := json.Marshal(session)
	if err != nil {
		return nil, err
	}

	// 使用Hash存储Session —— 方便按字段查询
	err = g.redis.HSet(ctx, key, map[string]interface{}{
		"data":      string(data),
		"user_id":   userID,
		"tenant_id": tenantID,
		"created_at": session.CreatedAt.Format(time.RFC3339),
	}).Err()
	if err != nil {
		return nil, err
	}

	// 设置TTL（过期时间）—— 24小时后自动清理，防止Redis被撑爆
	err = g.redis.Expire(ctx, key, 24*time.Hour).Err()
	if err != nil {
		return nil, err
	}

	// 维护用户的Session索引 —— 方便查询"这个用户有哪些会话"
	userSessionsKey := fmt.Sprintf("tenant:%s:user:%s:sessions", tenantID, userID)
	err = g.redis.SAdd(ctx, userSessionsKey, session.ID).Err()
	if err != nil {
		return nil, err
	}

	return session, nil
}

// GetSession —— 获取会话
// 就像顾客回来时，用会员卡号查他的历史记录
func (g *MultiTenantGateway) GetSession(
	ctx context.Context,
	tenantID string,
	sessionID string,
) (*Session, error) {
	key := g.sessionKey(tenantID, sessionID)
	
	// 验证租户隔离 —— 确保A租户不能访问B租户的会话
	data, err := g.redis.HGet(ctx, key, "data").Result()
	if err == redis.Nil {
		return nil, fmt.Errorf("session not found")
	}
	if err != nil {
		return nil, err
	}

	var session Session
	err = json.Unmarshal([]byte(data), &session)
	if err != nil {
		return nil, err
	}

	// 二次验证：确保会话确实属于这个租户
	// 防止通过篡改sessionID来越权访问
	if session.TenantID != tenantID {
		return nil, fmt.Errorf("tenant mismatch")
	}

	return &session, nil
}

// Execute —— 执行对话
// 这是核心流程：加载会话 → 检查上下文长度 → 添加用户消息 → AI推理 → 保存结果
func (g *MultiTenantGateway) Execute(
	ctx context.Context,
	tenantID string,
	sessionID string,
	message string,
) (*ExecutionResult, error) {
	// 1. 加载会话 —— 恢复之前的对话状态
	session, err := g.GetSession(ctx, tenantID, sessionID)
	if err != nil {
		return nil, err
	}

	// 2. 检查上下文长度 —— 对话太长会超出AI模型的处理能力
	// 如果超过8000 token，就压缩历史对话
	tokenCount := g.estimateTokenCount(session.Messages)
	if tokenCount > 8000 { // 超过阈值进行压缩
		session, err = g.compressContext(ctx, session)
		if err != nil {
			return nil, err
		}
	}

	// 3. 添加用户消息 —— 把用户说的话记录到会话中
	userMsg := Message{
		ID:        generateUUID(),
		Role:      "user",
		Content:   message,
		Timestamp: time.Now(),
	}
	session.Messages = append(session.Messages, userMsg)

	// 4. 调用Harness执行 —— 让AI开始思考并回复
	result, err := g.harness.Execute(session, message)
	if err != nil {
		return nil, err
	}

	// 5. 添加助手回复 —— 把AI的回复也记录下来
	assistantMsg := Message{
		ID:        generateUUID(),
		Role:      "assistant",
		Content:   result.Response,
		Timestamp: time.Now(),
		Metadata: map[string]interface{}{
			"tool_calls": result.ToolCalls,
			"token_usage": result.TokenUsage,
		},
	}
	session.Messages = append(session.Messages, assistantMsg)

	// 6. 更新会话 —— 保存最新的对话状态，下次能接着聊
	session.UpdatedAt = time.Now()
	err = g.saveSession(ctx, session)
	if err != nil {
		return nil, err
	}

	return result, nil
}

// compressContext —— 上下文压缩
// 就像你看一本很厚的书，不会逐字逐句记住所有内容，
// 而是记住最近几章的细节，前面的内容只记摘要
func (g *MultiTenantGateway) compressContext(
	ctx context.Context,
	session *Session,
) (*Session, error) {
	if len(session.Messages) < 20 {
		return session, nil // 消息太少，不需要压缩
	}

	// 保留最近的消息（最近10条，这些是"新鲜记忆"）
	recentMessages := session.Messages[len(session.Messages)-10:]
	// 较旧的消息需要压缩（这些是"历史记忆"）
	olderMessages := session.Messages[:len(session.Messages)-10]

	// 用AI把旧消息压缩成一段摘要
	summary, err := g.compressor.Compress(olderMessages)
	if err != nil {
		return nil, err
	}

	// 构建新的消息列表：摘要 + 最近消息
	compressedSession := &Session{
		ID:       session.ID,
		UserID:   session.UserID,
		TenantID: session.TenantID,
		Messages: append([]Message{
			{
				ID:      "summary",
				Role:    "system",
				Content: fmt.Sprintf("[历史对话摘要] %s", summary),
			},
		}, recentMessages...),
		State:     session.State,
		CreatedAt: session.CreatedAt,
		UpdatedAt: time.Now(),
	}

	return compressedSession, nil
}

// sessionKey —— 生成Redis Key（包含租户隔离）
// Key格式：tenant:{租户ID}:session:{会话ID}
// 这样不同租户的数据在Redis中天然隔离，不会互相干扰
func (g *MultiTenantGateway) sessionKey(tenantID, sessionID string) string {
	return fmt.Sprintf("tenant:%s:session:%s", tenantID, sessionID)
}

// estimateTokenCount —— 估算Token数量
// 简化估算：每个中文字约1个token，每个英文单词约1个token
// 实际生产中会用更精确的tokenizer
func (g *MultiTenantGateway) estimateTokenCount(messages []Message) int {
	// 简化的估算：每个字符约0.25个token
	totalChars := 0
	for _, msg := range messages {
		totalChars += len(msg.Content)
	}
	return totalChars / 4
}
```

### 多租户隔离机制

> 💡 **白话理解**：多租户隔离就像写字楼的门禁系统。每个公司有自己的门禁卡，只能进自己的楼层。即使你知道别的楼层在哪，没有门禁卡也进不去。代码里的 `TenantID` 就是门禁卡号，中间件会检查每次请求的"门禁卡"是否有效。

```go
// 租户上下文 —— 相当于"门禁卡"，记录你是谁、能去哪、能做什么
type TenantContext struct {
	TenantID    string           // 你属于哪个租户（哪个公司）
	UserID      string           // 你是谁
	Permissions PermissionSet    // 你能做什么（权限）
	Quota       QuotaInfo        // 你能用多少（配额）
}

// 权限控制 —— 定义"门禁卡"能打开哪些门
type PermissionSet struct {
	AllowedTools   []string          // 允许使用的工具（能进哪些房间）
	AllowedDirs    []string          // 允许访问的目录（能看哪些文件柜）
	MaxTokens      int               // Token使用上限（能用多少电）
	RateLimit      RateLimitConfig   // 限流配置（每分钟能进几次）
}

// 中间件：租户隔离 —— 每个请求进来时，先检查"门禁卡"
func (g *MultiTenantGateway) TenantIsolationMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 从Header获取租户信息 —— 刷门禁卡
		tenantID := c.GetHeader("X-Tenant-ID")
		userID := c.GetHeader("X-User-ID")
		apiKey := c.GetHeader("X-API-Key")

		// 没有门禁卡？拒绝进入
		if tenantID == "" || userID == "" {
			c.JSON(401, gin.H{"error": "missing tenant or user info"})
			c.Abort()
			return
		}

		// 验证API Key —— 门禁卡是否有效
		if !g.validateAPIKey(tenantID, apiKey) {
			c.JSON(401, gin.H{"error": "invalid api key"})
			c.Abort()
			return
		}

		// 加载租户权限 —— 查看这张门禁卡能去哪些楼层
		permissions, err := g.loadTenantPermissions(tenantID)
		if err != nil {
			c.JSON(500, gin.H{"error": "failed to load permissions"})
			c.Abort()
			return
		}

		// 设置租户上下文 —— 把门禁信息存到请求中，后续处理可以随时查看
		ctx := &TenantContext{
			TenantID:    tenantID,
			UserID:      userID,
			Permissions: permissions,
		}
		c.Set("tenant", ctx)

		c.Next()
	}
}

// 知识隔离：不同租户的数据完全隔离
// 就像不同公司的文件柜，A公司看不到B公司的文件
func (g *MultiTenantGateway) KnowledgeIsolation(
	tenantID string,
	toolName string,
) (map[string]interface{}, error) {
	switch toolName {
	case "file_operations":
		// 返回租户特定的目录白名单 —— A公司只能访问A公司的文件夹
		return g.getTenantAllowedDirs(tenantID)
		
	case "git_operations":
		// 返回租户可访问的仓库列表 —— A公司只能看A公司的代码仓库
		return g.getTenantRepositories(tenantID)
		
	case "database_query":
		// 返回租户的数据库连接信息 —— A公司只能连A公司的数据库
		return g.getTenantDatabaseConfig(tenantID)
		
	default:
		return nil, fmt.Errorf("unknown tool: %s", toolName)
	}
}
```

### 高可用设计

> 💡 **白话理解**：高可用就像一家餐厅准备了三个厨师。主厨（主LLM）正常做菜；如果主厨突然请假，副厨（备用LLM）顶上；如果副厨也不行，还有学徒（本地模型）能做简单的菜。总之，餐厅不会因为一个厨师不在就关门。

```go
// MCP Server健康检查 —— 定期检查所有"厨师"是否在岗
type HealthChecker struct {
	servers []MCPServer
	status  map[string]ServerStatus
}

type ServerStatus struct {
	Name        string
	Healthy     bool          // 是否健康
	LastChecked time.Time     // 上次检查时间
	Latency     time.Duration // 响应延迟
	ErrorCount  int           // 最近错误次数
}

// Start —— 启动健康检查，每30秒检查一次
func (h *HealthChecker) Start() {
	ticker := time.NewTicker(30 * time.Second)
	go func() {
		for range ticker.C {
			h.checkAll()
		}
	}()
}

func (h *HealthChecker) checkAll() {
	for _, server := range h.servers {
		status := h.checkServer(server)
		h.status[server.Name] = status
		
		if !status.Healthy {
			log.Printf("Server %s is unhealthy: %v", server.Name, status)
		}
	}
}

// ExecuteWithFallback —— 带降级的执行策略
// 主LLM挂了用备用LLM，备用也挂了用本地模型，保证服务不中断
func (g *MultiTenantGateway) ExecuteWithFallback(
	ctx context.Context,
	session *Session,
	message string,
) (*ExecutionResult, error) {
	// 1. 尝试主LLM（最好的厨师）
	result, err := g.executeWithLLM(ctx, session, message, "primary")
	if err == nil {
		return result, nil
	}

	log.Printf("Primary LLM failed: %v, trying fallback", err)

	// 2. 主LLM失败，尝试备用LLM（副厨）
	result, err = g.executeWithLLM(ctx, session, message, "fallback")
	if err == nil {
		return result, nil
	}

	log.Printf("Fallback LLM also failed: %v, using local model", err)

	// 3. 都失败，使用轻量级本地模型提供基础服务（学徒）
	// 虽然质量可能差一点，但至少不会完全不可用
	return g.executeWithLocalModel(ctx, session, message)
}
```

---

## 📊 性能对比与收益

### 重构收益汇总

| 维度 | 指标 | 优化前 | 优化后 | 提升 |
|------|------|--------|--------|------|
| **性能** | 启动延迟 | 5-10秒 | <500ms | **90%+** |
| | 内存占用 | 500MB | 50MB | **90%** |
| | 并发能力 | 10 QPS | 1000 QPS | **100x** |
| **架构** | 部署方式 | 单机CLI | 分布式服务 | - |
| | 扩展性 | 垂直扩展 | 水平扩展 | - |
| | 多租户 | ❌ | ✅ | - |
| **功能** | 上下文压缩 | ❌ | ✅（节省60%Token） | - |
| | 动态权限 | ❌ | ✅（System Prompt） | - |
| | 高可用 | ❌ | ✅（自动降级） | - |

---

## 📝 学习检查清单

完成本节学习后，你应该能够回答以下问题：

- [ ] **概念理解**：用你自己的话解释"多租户"是什么，并举一个生活中的例子
- [ ] **架构理解**：官方CLI有哪些问题？轻量化重构解决了哪些？
- [ ] **Harness理解**：Harness抽象的核心思想是什么？为什么要把"推理执行"和"交互逻辑"分离？
- [ ] **懒加载**：为什么工具懒加载比全量加载好？在什么场景下懒加载可能反而更慢？
- [ ] **租户隔离**：代码中是如何保证不同租户的数据互不可见的？有哪几层保护？
- [ ] **上下文压缩**：什么时候需要压缩上下文？压缩的策略是什么？
- [ ] **高可用**：三级降级策略（主LLM → 备用LLM → 本地模型）各自的优缺点是什么？
- [ ] **实际应用**：如果你要在公司内部部署一个AI编程助手，你会如何设计多租户方案？

> **上一篇**：[Claude Code SDK底层原理](../02-technical-deep-dive/03-claude-sdk-internals.md)  
> **下一篇**：[Claude Code相关技术对比与深度问题](../04-comparative-analysis/01-claude-comparison.md)