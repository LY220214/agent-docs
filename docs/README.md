# AI Agent 技术学习指南

> 📋 **阅读提示**：本文档库中的技术讨论基于公开资料分析，代码示例为分析性伪代码。涉及 Claude Code 的具体实现细节以 [官方文档](https://code.claude.com/docs) 为准。

> 基于真实AI应用场景的深度技术文档，涵盖Agent架构、MCP协议、Claude Agent SDK（`@anthropic-ai/claude-agent-sdk`）、Subagent协作、多租户系统等核心知识点  
> **术语说明**：文中的"Claude Code SDK"泛指 Claude Code 生态的开发工具链，包括 Claude Code CLI 工具和 `@anthropic-ai/claude-agent-sdk` 程序化 SDK。具体语境下会区分两者。  
> 从概念到实战，帮你真正理解AI Agent技术

---

## 🚀 新手必读

**你可能是这样的读者**：听说过ChatGPT，知道AI很火，但"Agent""MCP""Subagent"这些词看着像天书。别担心，这份文档就是为你准备的。

### 这是什么？

这是一份**AI Agent技术学习指南**。它来自真实的技术实践，把40多道核心技术问题拆解成了9篇深度文档。从最基础的概念到最硬核的架构设计，全部用中文讲清楚。

不管你是刚听说AI Agent想搞明白它到底是什么，还是已经写过一些代码想深入理解底层原理，这里都有适合你的内容。

### 谁适合看？

- 🔰 **零基础小白**：对AI感兴趣但还没入门，想快速了解Agent是什么
- 🎓 **有基础的开发者**：用过ChatGPT或写过一些AI代码，想深入理解底层原理
- 🛠️ **动手实践者**：想自己动手搭建Agent系统，需要系统性的知识框架
- 🧠 **技术好奇者**：就是想搞明白Claude Code、MCP这些热门技术到底怎么回事

### 你会学到什么？

1. AI Agent的核心工作原理（它不是聊天机器人，而是一个能自主完成任务的系统）
2. MCP协议如何让AI"长出手脚"去调用外部工具
3. Claude Code SDK的底层设计，理解一个商业级AI产品是怎么搭的
4. 多个AI如何像团队一样协作（Subagent机制）
5. 企业级系统怎么做到让成千上万个用户同时用AI而不互相干扰（多租户架构）

### 怎么用这份文档？

```
如果你是零基础 → 从「术语速查表」开始，然后按L1路径阅读
如果你有基础   → 直接看「文档导航」，挑你薄弱的章节精读
如果你想动手   → 先过L1概念，然后跳到「动手实践」开始写代码
```

---

## 📖 术语速查表

看到不懂的词，回来查这张表。每个术语都配了通俗的类比，帮你快速建立直觉。

| 术语 | 通俗解释 | 类比 |
|------|----------|------|
| **Agent** | 能自主感知环境、做出决策并执行动作的AI程序。不是简单的问答机器人，而是有目标、有计划、能自己想办法完成任务的智能体。它和聊天机器人的核心区别在于：聊天机器人只能你问它答，而Agent会自己规划步骤、调用工具、检查结果 | 像一个能独立干活的实习生，你交代一个目标，他自己查资料、用工具、一步步完成 |
| **Agent Loop** | Agent的核心运行循环：观察→思考→行动→再观察，不断重复直到任务完成。这是Agent能"自主"工作的关键机制，每一次循环都是一次决策点 | 像做菜的流程：尝一口→觉得淡→加盐→再尝一口，循环往复直到味道对了 |
| **MCP协议** | Model Context Protocol，让AI能调用外部工具的标准协议。定义了AI怎么发现工具、怎么传参数、怎么拿结果。有了MCP，AI就不再只是"说话"，而是能真正"做事" | 像USB接口标准，不管什么设备，插上就能用。MCP让AI能"插上"各种工具 |
| **ReAct范式** | Reasoning + Acting，一种让AI边推理边行动的方法论。先想清楚再动手，做完再想下一步。比纯推理更接地气，比纯行动更靠谱 | 像下棋：先想"他走这步我该怎么应对"，然后落子，再根据局面想下一步 |
| **Subagent** | 主Agent派出的子Agent，专门处理某个子任务。多个Subagent可以并行工作，各自完成后把结果汇总给主Agent。这种设计让复杂任务可以被拆解和并行处理 | 像项目经理把任务拆给不同组员，各组员同时干活，最后汇总给项目经理 |
| **SDK** | Software Development Kit，软件开发工具包。封装好了复杂功能，开发者直接调用就行，不用从零开始造轮子 | 像买了个半成品家具包，螺丝和板材都配好了，你只需要按说明书组装 |
| **上下文(Context)** | AI在当前对话中能"看到"的所有信息，包括之前的对话、系统指令、工具结果等。上下文越长，AI理解越准确，但消耗的Token也越多 | 像你跟朋友聊天时的"前情提要"，没有上下文AI就不知道你们在聊什么 |
| **状态机** | 一种概念模型，把系统分成若干个状态，每个状态下有特定的行为和转换规则。在 Agent 系统中，状态机是**理解** Agent 循环的思维工具——实际的 SDK 实现通常通过 session_id 等方式管理状态，而非显式状态机类 | 像红绿灯：红灯→绿灯→黄灯→红灯，每个状态对应不同行为，转换有固定规则 |
| **多租户** | 一套系统同时服务多个客户（租户），每个客户的数据和配置互相隔离。在AI系统中尤其重要，因为不同用户的对话和知识必须严格分开 | 像一栋公寓楼，每户有自己的房间和门锁，互不干扰，但共享同一栋楼的基础设施 |
| **Skills** | AI可以调用的能力模块，每个Skill解决一类特定问题。Skills太多会让AI"选择困难"，太少又不够用，需要精心设计数量和分类 | 像瑞士军刀上的不同工具，开瓶器、剪刀、螺丝刀，需要哪个用哪个 |
| **Token** | AI处理文本的最小单位，大约一个汉字=1-2个Token。Token数量决定AI能处理多长的文本，也直接影响使用成本 | 像自助餐的餐券，每张券换一口菜。Token越多，AI能"吃"的信息就越多 |
| **思维链(CoT)** | Chain-of-Thought，让AI把推理过程一步步写出来，而不是直接给答案。这不仅能提高准确率，还让结果可解释、可检查 | 像数学考试写解题步骤，而不是只写答案。写步骤不仅让结果更准，还方便检查 |
| **RAG** | Retrieval-Augmented Generation，先从知识库里检索相关内容，再让AI基于检索结果生成回答。解决了AI"记不住"和"会编造"的问题 | 像开卷考试：先翻书找到相关章节，再用自己的话写答案，比纯靠记忆靠谱得多 |
| **置信度** | AI对自己给出的结果有多"确定"。置信度高说明AI很有把握，低说明结果可能不太靠谱。在Subagent协作中，置信度用来过滤低质量结果 | 像天气预报说"降水概率90%"，这个90%就是置信度。概率低的时候你就不太信它 |
| **Harness（驾驭工程）** | Harness Engineering，OpenAI 于 2026 年开创的新兴工程学科。核心理念：Agent = Model + Harness。Harness 是围绕 AI 模型构建的一切——约束机制（Guides，告诉 Agent 能做什么不能做什么）、反馈回路（Sensors，观测 Agent 的行为并纠偏）、工作流控制（Orchestration）和持续改进循环（Steering Loop，人在循环外迭代优化 Harness）。不优化模型本身，而是优化模型运行的环境 | 像骑马用的全套马具（缰绳、马鞍、嚼子）——不是去驯服马本身，而是通过装备引导它跑得又快又稳 |
| **Session** | 一次完整的对话会话，从开始到结束。Session管理确保对话状态不丢失，包括上下文、工具调用历史、用户偏好等 | 像打电话：从拨号到挂断是一个Session。中间聊的内容都在这个Session里 |
| **懒加载** | 不一次性加载所有东西，而是用到的时候才加载。节省资源，加快启动速度。在Skills系统中尤其重要，因为工具太多会拖慢系统 | 像网购不把所有商品都搬进客厅，而是需要什么再从仓库拿 |
| **语义摘要** | 不是简单截断文本，而是理解内容后提取核心意思，用更少的文字表达相同的信息。是上下文压缩的核心技术之一 | 像看完一部两小时电影后，用三句话讲清楚剧情，而不是把台词砍掉一半 |
| **沙箱** | 隔离的运行环境，AI在里面执行代码不会影响真实系统。出了问题也不怕，沙箱外的世界毫发无伤 | 像游乐场的沙坑，小朋友在里面怎么折腾都不会弄脏外面的路 |
| **降级** | 当系统遇到问题（比如服务器压力大、某个服务挂了）时，自动切换到简化版功能，保证基本可用。是高可用设计的重要组成部分 | 像手机信号不好时自动从5G切到4G，网速慢了但至少还能用 |

---

## ❓ 常见疑问

### Q1：AI Agent到底是什么？和ChatGPT有什么区别？

ChatGPT是**对话式AI**，你问它答，它不会主动做事。Agent是**自主式AI**，你给它一个目标，它会自己规划步骤、调用工具、检查结果，直到任务完成。打个比方：ChatGPT像百科全书，你翻到哪页看哪页；Agent像私人助理，你交代一件事，它自己跑腿办完。

更具体地说，ChatGPT只能处理文本，而Agent能调用外部工具（搜索网页、读写文件、执行代码、操作数据库）。Agent的核心是Agent Loop：观察当前状态→决定下一步→执行动作→再观察，循环往复直到目标达成。

### Q2：我需要会什么才能看懂这些文档？

最低要求：会一门编程语言（Python或JavaScript最好），了解基本的Web开发概念（API、数据库）。如果你连这些都没有，建议先花一周学Python基础，再来这里。文档里的术语都可以在「术语速查表」里查到。

如果你有半年以上后端开发经验，这些文档对你来说会比较轻松。如果你是前端开发者，可能需要额外补一些后端架构的知识（比如状态机、分布式系统基础）。

### Q3：MCP协议难不难学？我需要先学什么？

MCP本身不难，它本质上就是一个让AI调用工具的通信标准。你需要先理解"API"是什么（就是程序之间互相调用的接口），然后理解"协议"是什么（就是大家约定好的通信规则）。有了这两个概念，MCP就是：AI按照约定好的规则，去调用各种API。

MCP的核心就三件事：1）工具定义，告诉AI有哪些工具可以用；2）发现机制，让AI能自动找到新工具；3）调用流程，规定AI怎么传参数、怎么拿结果。理解了这三点，MCP你就懂了。

### Q4：一定要学Claude Code吗？

不一定。Claude Code只是众多AI开发工具中的一个。但理解它的设计思想（Agent Loop、状态机、上下文管理）非常有帮助，因为这些是通用的架构模式。学技术最重要的是理解原理，而不是会用某个特定工具。

建议的学习路径：先理解Agent Loop和ReAct范式（这是所有Agent系统的通用原理），再了解MCP协议（这是工具调用的标准），最后看Claude Code的具体实现（这是商业级产品的设计参考）。

### Q5：这些文档要按顺序读吗？

不用。每篇文档都是独立的，可以按需阅读。但如果你是零基础，建议按「文档导航」里的L1→L2→L3顺序来，这样知识是递进的，不会跳级。

一个实用的技巧：先花15分钟看「核心知识点索引」，找到你最感兴趣或最薄弱的2-3个知识点，然后直接去对应的文档精读。带着问题去读，比从头到尾顺序读效率高得多。

### Q6：Subagent和普通Agent有什么区别？

Subagent是Agent的"下属"。主Agent负责整体规划和结果汇总，Subagent负责执行具体的子任务。区别在于：Subagent通常只做一件事，做完就把结果交回给主Agent，不会自己决定下一步做什么。就像组长分配任务给组员，组员做完汇报，组长再决定下一步。

一个关键的设计决策是：什么时候该用Subagent，什么时候该让主Agent自己干？简单说，如果一个任务需要不同的专业知识（比如代码评审需要安全专家、性能专家、风格专家），就适合用Subagent并行处理；如果任务简单直接，主Agent自己处理更高效。

### Q7：多租户架构为什么在AI系统中特别重要？

因为AI系统的资源消耗很大（Token要花钱、GPU要排队），而且不同用户的数据必须严格隔离（你不会想让别的用户看到你的对话记录）。多租户架构解决了两个核心问题：一是资源怎么公平分配，二是数据怎么安全隔离。

在传统Web应用中，多租户主要是数据库层面的隔离。但在AI系统中，多租户还涉及上下文隔离（不同用户的对话历史不能混在一起）、知识隔离（不同租户可能有专属的知识库）、以及成本控制（每个租户用了多少Token要精确计量）。

### Q8：学习路径可以压缩到更短吗？

可以，但要看你的基础。如果你已经有AI开发经验，10天就能过完核心内容。如果你是零基础，建议老老实实按30天来，每天的内容都是精心安排的，跳着学容易留下知识盲区。

一个折中方案：如果你时间紧张，可以只做每周的"周复盘"日，把核心概念过一遍。但这样你会缺少动手实践的部分，理解可能不够深入。

---

## 📚 文档导航

每篇文档都标注了难度等级和预计阅读时间，方便你按需选择。

| 难度 | 文档 | 内容概要 | 阅读时长 | 核心关键词 |
|------|------|----------|----------|------------|
| ⭐⭐ | 📋 [问题归类总结](./00-问题归类总结.md) | 40+技术问题分类与难度评估 | 15min | 知识全景、问题分类 |
| ⭐⭐ | 🔍 [字节跳动飞书AI技术概览](./01-overview/01-byte-interview-overview.md) | 真实AI应用场景与8道核心问题 | 30min | 应用场景、技术分析 |
| ⭐⭐⭐ | 🏗️ [项目架构与技术难点](./02-technical-deep-dive/01-project-architecture.md) | AI代码修复+Agent Loop实现 | 45min | Agent Loop、状态机、代码修复 |
| ⭐⭐⭐ | 🤝 [Subagent协作与代码评审](./02-technical-deep-dive/02-subagent-code-review.md) | 多专家并联+置信度过滤 | 40min | Subagent、置信度、代码评审 |
| ⭐⭐⭐⭐ | ⚙️ [Claude Code SDK底层原理](./02-technical-deep-dive/03-claude-sdk-internals.md) | MCP协议+状态机+Session管理 | 50min | MCP协议、SDK架构、Session |
| ⭐⭐⭐⭐ | 🏢 [SDK轻量化与多租户架构](./03-architecture-design/01-multi-tenant-architecture.md) | API封装层设计+分布式部署 | 45min | 多租户、调用层、上下文压缩 |
| ⭐⭐⭐ | ⚔️ [Claude Code技术对比](./04-comparative-analysis/01-claude-comparison.md) | 工具对比+思维链+记忆架构 | 35min | 技术选型、思维链、记忆 |
| ⭐⭐⭐ | 🛠️ [AI Coding与Skills系统](./05-practical-experience/01-ai-coding-practices.md) | 人vs AI+Skills设计 | 30min | AI Coding、Skills、工具管理 |
| ⭐⭐⭐ | 🛡️ [威胁情报Agent案例学习](./06-case-studies/01-sangfor-case-study.md) | 14个知识点详解+实操分析 | 25min | 威胁情报、实战应用 |

---

## 🎯 知识图谱（分层学习路径）

### L1 入门层（零基础起步）

如果你刚接触AI Agent，先搞懂这些概念：

```
L1 入门：建立基本认知
│
├── Agent是什么？
│   ├── Agent ≠ 聊天机器人
│   ├── Agent = 感知 + 推理 + 行动
│   └── Agent Loop：观察→思考→行动→再观察
│
├── Agent怎么用工具？
│   ├── 工具是什么？（API、函数、数据库查询...）
│   ├── MCP协议：AI调用工具的"USB标准"
│   └── 从"只会说话"到"能动手干活"
│
├── 怎么让Agent想清楚再动手？
│   ├── 思维链(CoT)：把推理过程写出来
│   ├── ReAct范式：边想边做
│   └── 为什么"想清楚"比"做得快"更重要
│
└── 多个Agent怎么合作？
    ├── 主Agent负责规划
    ├── Subagent负责执行
    └── 结果汇总与置信度过滤
```

**推荐阅读**：问题归类总结 → 技术概览 → AI Coding与Skills系统

### L2 进阶层（理解架构设计）

有了基础概念后，深入理解系统是怎么设计的：

```
L2 进阶：理解系统设计
│
├── Claude Code SDK是怎么设计的？
│   ├── 核心组件：Agent Loop、Tool Manager、Context Manager
│   ├── 状态机（概念模型）：Idle → Running → Waiting → Completed
│   └── Session管理：对话状态怎么保持不丢失
│
├── Subagent协作机制
│   ├── 多专家并联：多个Subagent同时干活
│   ├── Aggregator Agent：汇总结果的角色
│   └── 置信度过滤：怎么判断哪个结果更靠谱
│
├── 工程优化
│   ├── SDK轻量化：去掉不需要的功能，减少资源消耗
│   ├── Harness 驾驭工程：为 Agent 设计约束、反馈和控制系统
│   └── 上下文压缩：用更少的Token表达同样的信息
│
└── 技术选型
    ├── Claude Code vs Cursor vs Copilot
    ├── 各自的设计哲学和适用场景
    └── 为什么选这个不选那个
```

**推荐阅读**：项目架构与技术难点 → Subagent协作 → Claude Code技术对比

### L3 高级层（架构设计与实战）

能独立设计企业级AI系统：

```
L3 高级：架构设计与实战
│
├── 多租户架构
│   ├── 会话隔离：不同用户的数据互不可见
│   ├── 权限控制：谁能做什么，做到什么程度
│   ├── 知识隔离：每个租户有自己的知识库
│   └── 上下文压缩：多租户场景下的资源优化
│
├── 高可用设计
│   ├── 心跳检测：怎么知道服务还活着
│   ├── 自动降级：出问题时怎么保证基本可用
│   └── 故障恢复：挂了之后怎么快速恢复
│
├── Skills系统
│   ├── 工具管理：怎么管理几十上百个工具
│   ├── 动态加载：按需加载，不浪费资源
│   └── 数量优化：工具太多AI会犯选择困难症
│
└── 实战经验
    ├── AI Coding实践：人和AI怎么配合写代码
    ├── 代码评审自动化：让AI帮你Review代码
    └── 论文处理流水线：多Agent协同处理学术论文
```

**推荐阅读**：SDK底层原理 → 多租户架构 → 威胁情报Agent实战

---

## 🔥 核心知识点索引

### 重点知识 Top 10

| 排名 | 知识点 | 难度 | 文档位置 |
|------|--------|------|----------|
| 1 | Agent Loop怎么实现？难点在哪？ | ⭐⭐⭐⭐⭐ | [项目架构](./02-technical-deep-dive/01-project-architecture.md) |
| 2 | Claude Code SDK底层原理 | ⭐⭐⭐⭐⭐ | [SDK原理](./02-technical-deep-dive/03-claude-sdk-internals.md) |
| 3 | Subagent设计有什么讲究？ | ⭐⭐⭐⭐⭐ | [Subagent设计](./02-technical-deep-dive/02-subagent-code-review.md) |
| 4 | 多租户多轮对话后端实现 | ⭐⭐⭐⭐⭐ | [多租户架构](./03-architecture-design/01-multi-tenant-architecture.md) |
| 5 | 为什么想替换官方SDK？ | ⭐⭐⭐⭐⭐ | [轻量化重构](./03-architecture-design/01-multi-tenant-architecture.md) |
| 6 | AI如何给出代码级修复建议？ | ⭐⭐⭐⭐⭐ | [项目架构](./02-technical-deep-dive/01-project-architecture.md) |
| 7 | Claude Code vs Cursor 本质区别 | ⭐⭐⭐⭐ | [技术对比](./04-comparative-analysis/01-claude-comparison.md) |
| 8 | Skills过多导致模型困惑？ | ⭐⭐⭐⭐⭐ | [Skills系统](./05-practical-experience/01-ai-coding-practices.md) |
| 9 | 上下文压缩策略 | ⭐⭐⭐⭐ | [多租户架构](./03-architecture-design/01-multi-tenant-architecture.md) |
| 10 | 思维链修正机制 | ⭐⭐⭐⭐⭐ | [技术对比](./04-comparative-analysis/01-claude-comparison.md) |

---

## 📅 学习路径建议

每天1-2小时，30天从零到能独立搭建Agent系统。

### 第一周：打基础（Day 1-7）

| 天数 | 学习内容 | 具体任务 | 实践产出 |
|------|----------|----------|----------|
| Day 1 | 认识Agent | 阅读「术语速查表」和「常见疑问」，建立基本概念 | 写一份自己的术语笔记 |
| Day 2 | 知识全景 | 阅读[问题归类总结](./00-问题归类总结.md)，了解Agent技术全貌 | 列出自己最想深入的知识点 |
| Day 3 | 应用场景 | 阅读[字节跳动飞书AI概览](./01-overview/01-byte-interview-overview.md) | 用自己的话复述8个核心问题 |
| Day 4 | Agent Loop | 阅读[项目架构](./02-technical-deep-dive/01-project-architecture.md)前半部分 | 画出Agent Loop的流程图 |
| Day 5 | 代码修复 | 阅读项目架构后半部分，理解AI代码修复的实现 | 写一段伪代码描述修复流程 |
| Day 6 | MCP协议 | 搜索MCP官方文档，理解工具定义和调用流程 | 用自己的话解释MCP是什么 |
| Day 7 | 周复盘 | 回顾本周内容，整理笔记，补全遗漏 | 完成一份L1知识脑图 |

### 第二周：深入核心（Day 8-14）

| 天数 | 学习内容 | 具体任务 | 实践产出 |
|------|----------|----------|----------|
| Day 8 | Subagent | 阅读[Subagent协作](./02-technical-deep-dive/02-subagent-code-review.md) | 画出Subagent协作时序图 |
| Day 9 | 置信度 | 深入理解置信度过滤机制 | 用例子解释置信度怎么工作 |
| Day 10 | SDK架构 | 阅读[SDK底层原理](./02-technical-deep-dive/03-claude-sdk-internals.md)前半部分 | 画出SDK核心组件图 |
| Day 11 | 状态机 | 阅读SDK原理后半部分，理解状态机设计 | 写出状态转换表 |
| Day 12 | Session | 深入理解Session管理和持久化 | 解释Session生命周期 |
| Day 13 | 技术对比 | 阅读[Claude Code技术对比](./04-comparative-analysis/01-claude-comparison.md) | 列出三个工具的优缺点对比表 |
| Day 14 | 周复盘 | 回顾本周内容，重点理解SDK和Subagent | 完成一份L2知识脑图 |

### 第三周：架构设计（Day 15-21）

| 天数 | 学习内容 | 具体任务 | 实践产出 |
|------|----------|----------|----------|
| Day 15 | 多租户 | 阅读[多租户架构](./03-architecture-design/01-multi-tenant-architecture.md)前半部分 | 画出多租户架构图 |
| Day 16 | 会话隔离 | 深入理解会话隔离和权限控制 | 写出隔离方案的关键设计点 |
| Day 17 | Harness 驾驭工程 | 理解 Harness = 模型之外的一切（约束+反馈+控制） | 用自己的话解释 Agent = Model + Harness |
| Day 18 | 上下文压缩 | 学习语义摘要和上下文压缩策略 | 写出压缩前后的对比示例 |
| Day 19 | Skills系统 | 阅读[AI Coding实践](./05-practical-experience/01-ai-coding-practices.md) | 列出Skills设计的核心原则 |
| Day 20 | 实战案例 | 阅读[威胁情报 Agent 案例](./06-case-studies/01-sangfor-case-study.md) | 对比两个实战案例的异同 |
| Day 21 | 周复盘 | 回顾本周内容，重点理解架构设计 | 完成一份L3知识脑图 |

### 第四周：动手实践（Day 22-30）

| 天数 | 学习内容 | 具体任务 | 实践产出 |
|------|----------|----------|----------|
| Day 22 | 搭建最小Agent | 克隆minimal-agent项目，跑通第一个Agent | Agent能成功调用一个工具 |
| Day 23 | 添加新工具 | 给Agent添加一个自定义工具（比如天气查询） | 新工具能正常工作 |
| Day 24 | Subagent实践 | 实现一个简单的多Agent协作场景 | 两个Subagent能并行工作并汇总结果 |
| Day 25 | 状态机实现 | 为Agent添加状态机，管理运行状态 | 状态转换逻辑正确 |
| Day 26 | Session管理 | 实现对话历史的持久化和恢复 | 重启后能恢复之前的对话 |
| Day 27 | 上下文压缩 | 实现简单的上下文摘要功能 | 长对话能自动压缩而不丢失关键信息 |
| Day 28 | 论文阅读 | 阅读「必读论文」中的ReAct和CoT论文 | 写出论文核心观点摘要 |
| Day 29 | 全面复盘 | 回顾30天所有笔记和脑图 | 整理出一份个人知识体系图 |
| Day 30 | 项目收尾 | 完善实践项目，写一份技术总结 | 🎉 完成学习路径！ |

---

## 🎯 核心技能清单

### 必备技能（必须掌握）

- [ ] **Agent架构**：ReAct循环、状态机设计、任务管理
- [ ] **Harness 驾驭工程**：理解 Agent = Model + Harness，Guides（约束）+ Sensors（反馈）+ Steering Loop（持续改进）
- [ ] **MCP协议**：工具定义、发现机制、调用流程
- [ ] **Claude Code**：SDK架构、Session管理、上下文控制
- [ ] **系统设计**：多租户隔离、权限控制、高可用设计
- [ ] **工程实践**：代码评审、Subagent协作、Skills管理

### 进阶技能（优先掌握）

- [ ] 上下文压缩与语义摘要
- [ ] 多轮对话状态保持
- [ ] 工具选择的置信度机制
- [ ] 自动降级与故障恢复
- [ ] AI Coding最佳实践

---

## 🛠️ 动手实践

光看不练假把式。理解了概念之后，最重要的是动手写代码。我们准备了一个配套的实践项目，帮你从零开始搭建一个真正的Agent系统。

### minimal-agent 项目

👉 **[minimal-agent](../minimal-agent/)** — 一个最小化的AI Agent实现

这个项目从最简单的Agent Loop开始，一步步带你实现：

1. **基础Agent Loop**：观察→思考→行动的完整循环
2. **工具调用**：通过MCP协议让Agent调用外部工具
3. **Subagent协作**：多个Agent分工合作完成复杂任务
4. **状态管理**：用状态机管理Agent的运行状态
5. **上下文压缩**：当对话过长时自动摘要

每个章节都有完整的代码和详细的注释，你可以直接运行、修改、实验。

### 实战项目建议

#### 项目一：智能代码评审系统（初级 ⭐⭐）

**目标**：实现一个基于Subagent的代码评审工具  
**技术栈**：Python/TypeScript + Claude SDK + GitHub API  
**预计耗时**：1-2周  
**学习点**：
- Subagent协作机制
- 置信度过滤
- Git集成

**实现步骤**：
1. 用Claude SDK创建一个主Agent，负责接收代码变更
2. 创建3个Subagent：安全审查、性能分析、代码风格
3. 每个Subagent独立分析代码并给出评分和置信度
4. 主Agent汇总结果，过滤低置信度建议，输出最终评审报告

**收获**：理解为什么用Subagent而不是一个Agent全干，置信度过滤的具体实现方式

#### 项目二：多租户AI网关（中级 ⭐⭐⭐）

**目标**：构建支持多租户的Claude Code后端服务  
**技术栈**：Go + Redis + PostgreSQL + Kubernetes  
**预计耗时**：2-3周  
**学习点**：
- 会话隔离
- 上下文压缩
- 水平扩展

**实现步骤**：
1. 设计多租户数据模型，每个租户有独立的配置和知识库
2. 实现Session管理，确保不同租户的对话互不干扰
3. 加入上下文压缩，当对话过长时自动摘要
4. 用Redis做缓存，PostgreSQL做持久化
5. 部署到Kubernetes，支持水平扩展

**收获**：能画出完整的架构图，讲清楚会话隔离的具体方案，上下文压缩的触发条件和策略

#### 项目三：AI论文助手（高级 ⭐⭐⭐⭐）

**目标**：多Agent协同完成论文检索、摘要、分析  
**技术栈**：Python + LangChain + Vector DB + Arxiv API  
**预计耗时**：3-4周  
**学习点**：
- 多Agent编排
- RAG检索增强
- 知识图谱

**实现步骤**：
1. 创建检索Agent，负责从Arxiv搜索相关论文
2. 创建摘要Agent，负责提取论文核心观点
3. 创建分析Agent，负责对比多篇论文的异同
4. 创建编排Agent，负责协调以上三个Agent的工作流程
5. 用Vector DB存储论文向量，支持语义检索
6. 实现RAG流程：检索→增强→生成

**收获**：理解多Agent编排的挑战（比如Agent之间的通信协议、错误处理、结果聚合），RAG的检索策略和效果评估

---

## 🔗 外部资源

### 必读论文

1. **ReAct**: Synergizing Reasoning and Acting in Language Models
   - 核心观点：让AI边推理边行动，比纯推理或纯行动效果都好
   - 阅读建议：先看摘要和实验结果，再看方法细节

2. **Chain-of-Thought**: Large Language Models are Zero-Shot Reasoners (Kojima et al.)
   - 核心观点：只需加上"Let's think step by step"，就能让AI自动进行逐步推理，无需少样本示例
   - 阅读建议：重点看"Let's think step by step"这个prompt的实验效果

3. **Toolformer**: Language Models Can Teach Themselves to Use Tools
   - 核心观点：AI可以自己学会调用外部工具
   - 阅读建议：关注工具调用的训练方法，这是MCP的理论基础

### 开源项目

- [Claude Code](https://github.com/anthropics/claude-code) - Claude Code CLI 工具仓库
- [Claude Agent SDK](https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk) - `@anthropic-ai/claude-agent-sdk`，可编程的 Agent SDK
- [LangChain](https://github.com/langchain-ai/langchain) - Agent框架，适合入门学习Agent开发
- [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) - 复杂Agent示例，展示了Agent的潜力

### 学习资料

- [Anthropic Engineering Blog](https://www.anthropic.com/engineering) - Anthropic官方技术博客，了解Claude的最新设计思路
- [LangChain Documentation](https://python.langchain.com/) - LangChain官方文档，Agent开发的入门教程
- [MCP Protocol](https://modelcontextprotocol.io/) - MCP协议官方文档，工具调用的标准规范

---

## 🚀 下一步

读完了所有文档，然后呢？知识只有在实践中才能真正变成你的。以下是一个循序渐进的实践路径：

### 第一步：跑通 minimal-agent

去 [minimal-agent](../minimal-agent/) 项目，按照README把最基础的Agent跑起来。看到Agent第一次成功调用工具的那一刻，你就真正理解了Agent Loop。

### 第二步：给 Agent 添加一个新工具

minimal-agent自带了几个基础工具。试着添加一个自己的工具，比如：
- 一个查询天气的工具
- 一个计算器工具
- 一个读取本地文件的工具

这个过程会让你理解MCP协议的核心：工具定义、参数传递、结果返回。

### 第三步：替换 LLM 后端

minimal-agent默认使用Claude。试着把LLM后端换成其他模型（比如GPT-4、本地运行的Llama等）。你会发现：
- 不同模型的Agent Loop行为差异很大
- Prompt工程对Agent表现的影响巨大
- 理解为什么"Agent = Model + Harness"——模型只是引擎，Harness 才是整辆车

### 第四步：实现 Subagent 协作

在minimal-agent的基础上，实现一个简单的多Agent协作场景：
- 一个主Agent负责规划
- 两个Subagent分别处理不同子任务
- 主Agent汇总结果

这是理解Subagent机制最直接的方式。

### 第五步：挑战一个完整项目

从「实战项目建议」中选一个，从头到尾做完。不用追求完美，能跑起来就是胜利。遇到问题就回来翻文档，这时候你会发现之前读的内容突然都变得有用了。

### 持续学习

- 关注 [Anthropic Engineering Blog](https://www.anthropic.com/engineering) 和 [MCP Protocol](https://modelcontextprotocol.io/) 的更新
- 在GitHub上找有趣的Agent项目，读源码
- 尝试把学到的架构模式应用到自己的项目中
- 和其他学习者交流，分享你的实践心得

---

## 🤝 贡献指南

欢迎提交PR补充：
- 技术细节勘误
- 实战项目案例
- 学习心得体会
- 新的知识点补充

### 贡献方式

1. Fork本仓库
2. 创建你的特性分支（`git checkout -b feature/your-feature`）
3. 提交你的修改（`git commit -m 'Add some feature'`）
4. 推送到分支（`git push origin feature/your-feature`）
5. 创建Pull Request

### 文档规范

- 使用Markdown格式
- 中文为主，技术术语保留英文原文
- 每篇文档控制在3000-5000字
- 配合代码示例和架构图

---

## 📄 License

本知识库仅供学习交流使用。

---

**最后更新**：2026年4月  
**文档数量**：9篇核心文档  
**覆盖知识点**：40+核心技术点  
**总字数**：5万+技术干货

> 🎯 **学以致用，理解万岁！**