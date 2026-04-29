# AI Coding实践与Skills系统设计

> 深入探讨AI Coding实战经验、Skills系统设计与优化  
> 涵盖：人vs AI编码、Skills数量管理、模型困惑问题

---

## 📖 阅读前你需要知道

在阅读本文之前，建议你了解以下概念：

- **AI Coding**：用AI辅助编写代码，包括代码补全、代码生成、代码审查等。不是让AI完全替代程序员，而是让AI成为你的"超级助手"
- **Skills系统**：AI Agent的能力模块，每个Skill定义了一种AI能做的事情。就像手机上的App，你不会一次性打开所有App，而是按需启动
- **上下文窗口**：AI模型一次能"看到"的文本长度。就像人的短期记忆容量有限，AI也不能一次处理无限长的内容
- **Token**：AI处理文本的基本单位，大约1个中文字=1-2个Token，1个英文单词=1个Token
- **幻觉（Hallucination）**：AI生成看似合理但实际错误的内容，比如编造不存在的API函数

如果你对这些概念还不太熟悉，别担心，本文会在遇到时用通俗的方式解释。

---

## 📋 学习要点

| 编号 | 主题 | 难度 |
|------|------|------|
| 1 | 目前写代码用人写还是AI写 | ⭐⭐⭐ |
| 2 | AI Coding的优缺点 | ⭐⭐⭐⭐ |
| 3 | AI交互过程中的经验沉淀 | ⭐⭐⭐⭐ |
| 4 | AI审核生成代码的效果 | ⭐⭐⭐⭐ |
| 5 | 大量Skills如何精准找到所需 | ⭐⭐⭐⭐⭐ |
| 6 | Skills过多导致上下文过大 | ⭐⭐⭐⭐⭐ |
| 7 | Skills过多导致模型困惑 | ⭐⭐⭐⭐⭐ |
| 8 | 项目中沉淀的Skill案例 | ⭐⭐⭐⭐ |

---

## 📝 第一部分：AI Coding实践

### 人写 vs AI写：当前状态

```
当前编码工作分配（典型企业场景）：

┌────────────────────────────────────────────────────────────┐
│                                                            │
│   架构设计          ░░░░░░░░░░░░░░░░░░░░  人类 100%       │
│   ├─ 系统架构设计                                          │
│   ├─ 技术选型决策                                          │
│   └─ 复杂算法实现                                          │
│                                                            │
│   业务逻辑开发      ██████░░░░░░░░░░░░░░  混合 70/30      │
│   ├─ 标准CRUD操作  → AI生成 60%                           │
│   ├─ 业务规则编写  → 人类主导 80%                          │
│   └─ 异常处理      → AI辅助 40%                           │
│                                                            │
│   样板代码          ████████████████░░░░  AI 80%          │
│   ├─ API接口定义   → AI生成 90%                           │
│   ├─ 数据模型      → AI生成 85%                           │
│   └─ 配置文件      → AI生成 95%                           │
│                                                            │
│   测试代码          ██████████████░░░░░░  AI 70%          │
│   ├─ 单元测试      → AI生成 80%                           │
│   ├─ 集成测试      → 混合 50%                             │
│   └─ 测试数据      → AI生成 90%                           │
│                                                            │
│   Bug修复           ████████░░░░░░░░░░░░  混合 60/40      │
│   ├─ 简单Bug       → AI修复 70%                           │
│   ├─ 复杂Bug       → 人类主导 80%                          │
│   └─ 回归验证      → AI辅助 50%                           │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 什么时候用人写，什么时候用AI写？

> 💡 **白话理解**：人写代码就像大厨做招牌菜，需要创意和经验；AI写代码就像流水线做快餐，速度快但千篇一律。关键是知道什么时候该请大厨，什么时候该用流水线。

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  具体场景：什么时候用人，什么时候用AI？
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 适合AI写的场景（AI为主，人审查）：

1. 样板代码
   场景：你需要写10个CRUD接口，每个接口结构几乎一样
   AI做法："帮我根据User模型生成CRUD接口"
   人做的事：审查生成的代码是否符合项目规范

2. 单元测试
   场景：你写了一个工具函数，需要测试各种边界情况
   AI做法："帮我为formatDate函数写单元测试，覆盖所有边界情况"
   人做的事：确认测试用例覆盖了关键场景

3. 文档编写
   场景：函数写完了，需要补充注释和文档
   AI做法："帮我为这个函数生成JSDoc注释"
   人做的事：检查描述是否准确

4. 代码重构
   场景：需要把一个500行的函数拆分成5个小函数
   AI做法："帮我把这个大函数按职责拆分"
   人做的事：确认拆分后的逻辑是否正确

5. 格式转换
   场景：需要把JSON数据转成TypeScript类型定义
   AI做法："根据这个JSON生成对应的TypeScript接口"
   人做的事：确认类型定义是否完整

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 适合人写的场景（人为主，AI辅助）：

1. 架构设计
   场景：新项目的技术选型和模块划分
   人做法：分析业务需求、评估技术方案、做权衡决策
   AI辅助：提供技术方案的对比信息

2. 核心业务逻辑
   场景：支付系统的核心结算逻辑
   人做法：仔细设计业务规则、处理各种边界情况
   AI辅助：帮忙写测试用例验证逻辑

3. 安全关键代码
   场景：用户认证和授权逻辑
   人做法：严格遵循安全最佳实践
   AI辅助：帮忙做安全审查

4. 性能关键路径
   场景：高并发场景下的核心处理逻辑
   人做法：精心设计数据结构和算法
   AI辅助：帮忙做性能分析和优化建议

5. 复杂Bug修复
   场景：一个涉及多个模块的并发Bug
   人做法：分析调用链、定位根因、设计修复方案
   AI辅助：帮忙搜索相关代码、生成修复后的测试

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### AI Coding优缺点

#### 优势
- ✅ 速度：生成样板代码效率提升10x
- ✅ 覆盖：自动补全减少遗漏
- ✅ 学习：快速理解陌生代码库
- ✅ 一致性：保持代码风格统一

#### 劣势
- ❌ 幻觉：生成不存在API调用
- ❌ 理解：缺乏业务上下文
- ❌ 安全：可能引入漏洞
- ❌ 架构：无法进行高层设计

### 🔰 新人常见误区

> 💡 **白话理解**：刚接触AI编程的新人容易踩坑。下面列出了最常见的5个误区，以及正确的做法。

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  新人使用AI编程的5大误区
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ 误区1：AI生成的代码直接用，不审查
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  新人做法：
  AI生成代码 → 复制粘贴 → 提交 ✅

  正确做法：
  AI生成代码 → 阅读理解 → 检查逻辑 → 修改问题 → 测试验证 → 提交

  为什么：AI可能生成看似正确但有隐藏Bug的代码。
  比如：AI可能用了已废弃的API、忽略了边界情况、引入了安全漏洞。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ 误区2：把AI当搜索引擎，只问不学
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  新人做法：
  "帮我写一个排序函数" → 复制结果 → 下次再问同样的问题

  正确做法：
  "帮我写一个排序函数" → 阅读代码 → 理解原理 → 自己能写 → 下次自己写

  为什么：如果你不理解AI生成的代码，出了Bug你也没法修。
  AI是学习工具，不是偷懒工具。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ 误区3：给AI的Prompt太模糊
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  新人做法：
  "帮我写个函数"  → AI不知道写什么，瞎猜

  正确做法：
  "帮我用TypeScript写一个函数，输入是数字数组，输出是数组中所有偶数的平方和。
   要求：1. 使用列表推导式  2. 添加类型注解  3. 处理空数组情况"

  为什么：Prompt越具体，AI生成的代码越准确。
  模糊的Prompt = 模糊的结果。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ 误区4：过度依赖AI，遇到问题先问AI而不是先思考
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  新人做法：
  报错了 → 直接把错误信息贴给AI → AI给答案 → 复制粘贴

  正确做法：
  报错了 → 先读错误信息 → 尝试理解原因 → 查文档 → 还不行再问AI
  → 问AI时说明你已经尝试了什么

  为什么：先自己思考能加深理解。直接问AI会让你越来越依赖它，
  遇到AI也解决不了的问题时就束手无策了。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ 误区5：忽略AI生成代码的安全性
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  新人做法：
  AI生成了SQL查询 → 直接用 → 没注意到有SQL注入风险

  正确做法：
  AI生成了SQL查询 → 检查是否使用参数化查询 → 确认没有注入风险 → 再用

  为什么：AI不了解你的安全要求，可能生成有漏洞的代码。
  常见安全问题：SQL注入、XSS、硬编码密钥、不安全的随机数。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 📋 日常开发 Checklist

> 💡 **白话理解**：这份清单就像飞行员起飞前的检查表。每次用AI写代码前过一遍，能帮你避免大部分常见问题。

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AI辅助开发日常Checklist
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 使用AI之前：
□ 我是否清楚要AI帮我做什么？（目标明确）
□ 我是否已经自己思考过解决方案？（先想后问）
□ 我是否准备好了足够的上下文信息？（相关代码、错误信息等）
□ 我是否选择了合适的AI工具？（简单补全用Copilot，复杂任务用Claude Code）

📝 使用AI之后：
□ 我是否阅读并理解了AI生成的每一行代码？（不要盲目复制）
□ 我是否检查了AI使用的API是否存在且版本正确？（防幻觉）
□ 我是否验证了边界情况的处理？（空值、异常、并发）
□ 我是否检查了安全性问题？（注入、权限、敏感信息）
□ 我是否运行了测试？（不要只看代码，要跑起来验证）

📝 提交代码之前：
□ 我是否添加了必要的注释？（AI生成的代码也需要注释）
□ 我是否确认代码风格与项目一致？（AI可能用不同风格）
□ 我是否清理了AI生成的冗余代码？（AI有时会生成不必要的代码）
□ 我是否更新了相关文档？（接口变更需要更新文档）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🛠️ 第二部分：Skills系统设计

> 📋 **技术说明**：Claude Code 官方通过 `.claude/commands/` 目录下的 Markdown 文件（YAML frontmatter）定义 Skills，通过 `description` 字段进行匹配。以下讨论的设计模式（SkillRegistry、触发词索引、置信度过滤）是基于实践的分析性设计，展示了 Skills 管理系统的常见设计考量。

### Skills是什么？生活中的类比

> 💡 **白话理解**：Skills就像手机上的App。你不会一次性打开所有App，而是按需启动。需要导航时打开地图App，需要支付时打开支付宝App。同样，AI也不会一次性加载所有Skills，而是根据你的需求，智能地选择加载哪些Skills。

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Skills系统 vs 手机App：详细对照
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  手机App                        Skills系统
  ──────────────                ──────────────
  你买手机时预装了几个核心App      系统启动时加载核心Skills
  （电话、短信、设置）             （文件操作、代码搜索、Git）

  你按需下载其他App               系统按需加载其他Skills
  （需要导航时下载地图App）        （需要测试时加载测试Skill）

  你不会同时打开所有App           系统不会同时加载所有Skills
  （太耗内存，手机会卡）           （太占上下文，AI会困惑）

  App有分类（社交、工具、游戏）    Skills有分类（核心、常用、专业）
  你按分类找App                   系统按分类检索Skills

  App有版本号和更新               Skills有版本号和迭代
  你需要更新App                   系统需要更新Skills

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  核心问题（也是本节Skills部分要解决的）：

  Q14: 手机上有100个App，你怎么快速找到你要的？
       → Skills太多，怎么精准找到需要的？

  Q15: 同时打开50个App，手机会卡死
       → Skills太多，上下文窗口装不下

  Q16: 同时收到50个App的通知，你不知道先看哪个
       → Skills太多，AI不知道该用哪个

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Skills架构

> 💡 **白话理解**：下面的代码定义了Skill的结构和注册表。Skill就像App的应用商店，每个Skill有名字、描述、触发条件、参数和实现。注册表就像应用商店的搜索引擎，帮你快速找到需要的Skill。

```typescript
// Skill定义 —— 就像App Store里的一个App
interface Skill {
  name: string;              // 技能名称（App名字）
  description: string;       // 技能描述（App简介，给AI看的）
  triggers: Trigger[];       // 触发条件（什么时候启动这个App）
  parameters: Parameter[];   // 参数定义（App需要什么输入）
  implementation: Handler;   // 实现函数（App的具体功能）
  metadata: SkillMetadata;   // 元数据（版本号、分类等）
}

interface SkillMetadata {
  version: string;
  author: string;
  category: string;          // 分类（就像App的分类：社交、工具、游戏）
  confidence: number;        // 默认置信度（AI对这个Skill的信任程度）
  examples: Example[];       // 示例（怎么使用这个Skill）
  dependencies: string[];    // 依赖的skills（这个Skill需要先加载哪些其他Skill）
}

// Skill注册表 —— 就像App Store的搜索引擎
class SkillRegistry {
  private skills: Map<string, Skill> = new Map();
  private categoryIndex: Map<string, Set<string>> = new Map();
  private triggerIndex: Map<string, Set<string>> = new Map();
  
  // 注册Skill —— 就像App上架到App Store
  register(skill: Skill) {
    this.skills.set(skill.name, skill);
    
    // 建立分类索引 —— 按类别归档
    if (!this.categoryIndex.has(skill.metadata.category)) {
      this.categoryIndex.set(skill.metadata.category, new Set());
    }
    this.categoryIndex.get(skill.metadata.category)!.add(skill.name);
    
    // 建立触发词索引 —— 按关键词建立搜索索引
    for (const trigger of skill.triggers) {
      const keywords = trigger.keywords;
      for (const kw of keywords) {
        if (!this.triggerIndex.has(kw)) {
          this.triggerIndex.set(kw, new Set());
        }
        this.triggerIndex.get(kw)!.add(skill.name);
      }
    }
  }
  
  // 智能检索（解决Q14：怎么精准找到需要的Skill）
  // 三种方式综合判断：关键词匹配 + 语义相似度 + 上下文匹配
  async findRelevantSkills(
    intent: string,
    context: Context,
    llm: LLMClient
  ): Promise<RankedSkill[]> {
    // 1. 关键词匹配 —— 就像在App Store搜索关键词
    const keywordMatches = this.matchByKeywords(intent);
    
    // 2. 语义相似度 —— 就像App Store的"你可能还喜欢"
    const semanticMatches = await this.matchBySemantics(intent, llm);
    
    // 3. 上下文匹配 —— 根据你当前在做什么推荐
    const contextMatches = this.matchByContext(context);
    
    // 4. 合并并排序 —— 综合三种推荐结果
    const allMatches = this.mergeMatches(
      keywordMatches,
      semanticMatches,
      contextMatches
    );
    
    // 5. 限制数量（解决Q15：上下文窗口装不下太多Skills）
    return this.selectTopK(allMatches, 10);
  }
  
  // 限制上下文大小 —— 就像手机不会同时打开所有App
  private selectTopK(skills: RankedSkill[], k: number): RankedSkill[] {
    // 按置信度排序 —— 最相关的排前面
    skills.sort((a, b) => b.confidence - a.confidence);
    
    // 选择前k个，确保总token数在限制内
    let totalTokens = 0;
    const selected: RankedSkill[] = [];
    
    for (const skill of skills) {
      const skillTokens = this.estimateTokens(skill);
      if (totalTokens + skillTokens > 2000) {  // 限制
        break;
      }
      selected.push(skill);
      totalTokens += skillTokens;
    }
    
    return selected;
  }
}
```

### 解决模型困惑

> 💡 **白话理解**：模型困惑就像你同时收到50条微信消息，不知道先看哪条。解决方案是：先按重要性排序，只看最相关的几条，其他的先忽略。

```typescript
// 技能选择优化器 —— 帮AI从众多Skills中选出最合适的
class SkillSelectionOptimizer {
  // 策略1：分类过滤 —— 先缩小范围
  // 就像你找餐厅，先选"中餐"类别，再从中选
  filterByCategory(intent: string, skills: Skill[]): Skill[] {
    const category = this.classifyIntent(intent);
    return skills.filter(s => s.metadata.category === category);
  }
  
  // 策略2：置信度阈值 —— 只保留足够相关的
  // 就像你只看评分4星以上的餐厅
  filterByConfidence(skills: Skill[], threshold: number = 0.7): Skill[] {
    return skills.filter(s => s.metadata.confidence >= threshold);
  }
  
  // 策略3：去重与冲突消解 —— 去掉功能重叠的Skills
  // 就像你不会同时打开两个导航App
  resolveConflicts(skills: Skill[]): Skill[] {
    const resolved: Skill[] = [];
    const seen = new Set<string>();
    
    for (const skill of skills) {
      // 检查是否与已选skill冲突
      const hasConflict = resolved.some(selected => 
        this.isConflicting(skill, selected)
      );
      
      if (!hasConflict && !seen.has(skill.name)) {
        resolved.push(skill);
        seen.add(skill.name);
      }
    }
    
    return resolved;
  }
  
  // 策略4：分层加载 —— 先加载核心Skills，有空间再加载次要的
  // 就像手机先保证电话和短信能用，再考虑其他App
  async loadSkillsHierarchically(
    primarySkills: Skill[],
    secondarySkills: Skill[]
  ): Promise<Skill[]> {
    // 先加载核心技能
    const loaded = [...primarySkills];
    
    // 如果有空间，加载次要技能
    const remainingTokens = this.calculateRemainingTokens(loaded);
    for (const skill of secondarySkills) {
      if (this.estimateTokens(skill) <= remainingTokens) {
        loaded.push(skill);
        remainingTokens -= this.estimateTokens(skill);
      }
    }
    
    return loaded;
  }
}
```

---

## 💼 第三部分：项目Skill案例

### 典型Skill示例

> 💡 **白话理解**：下面是两个具体的Skill例子。第一个是代码搜索Skill，就像手机上的搜索App；第二个是代码审查Skill，就像手机上的安全扫描App。

```typescript
// Skill 1: 代码搜索 —— 就像手机上的搜索App
const codeSearchSkill: Skill = {
  name: "search_code",
  description: "在代码库中搜索特定模式或符号",
  triggers: [
    { keywords: ["search", "find", "grep", "在哪里"] }
  ],
  parameters: [
    {
      name: "pattern",
      type: "string",
      description: "搜索模式（支持正则）",
      required: true
    },
    {
      name: "file_pattern",
      type: "string",
      description: "文件过滤模式（如*.ts）",
      required: false
    }
  ],
  implementation: async (args) => {
    const results = await ripgrep(args.pattern, args.file_pattern);
    return formatResults(results);
  },
  metadata: {
    version: "1.0",
    category: "code_navigation",
    confidence: 0.95,
    examples: [
      { input: "查找所有使用useState的地方", output: "search_code pattern='useState'" }
    ]
  }
};

// Skill 2: 智能代码审查 —— 就像手机上的安全扫描App
const codeReviewSkill: Skill = {
  name: "review_code",
  description: "对代码变更进行自动化审查",
  triggers: [
    { keywords: ["review", "审查", "检查代码", "code review"] }
  ],
  parameters: [
    {
      name: "diff",
      type: "string",
      description: "代码diff内容",
      required: true
    },
    {
      name: "focus_areas",
      type: "array",
      description: "重点关注领域（security/performance/style）",
      required: false
    }
  ],
  implementation: async (args) => {
    const subagents = [
      securityAgent,
      performanceAgent,
      styleAgent
    ].filter(agent => 
      !args.focus_areas || args.focus_areas.includes(agent.type)
    );
    
    const findings = await Promise.all(
      subagents.map(agent => agent.review(args.diff))
    );
    
    return aggregateResults(findings);
  },
  metadata: {
    version: "2.0",
    category: "code_quality",
    confidence: 0.92
  }
};
```

---

## 📊 Skills管理最佳实践

### 数量管理策略

```
Skills数量管理金字塔：

                    ┌─────────┐
                    │  1-3个   │  核心Skills（必须加载）
                    │  核心    │  - 文件操作
                    └────┬────┘  - 代码搜索
                         │       - Git操作
                    ┌────┴────┐
                    │  5-10个  │  常用Skills（按需加载）
                    │  常用    │  - 测试生成
                    └────┬────┘  - 文档编写
                         │       - 代码重构
                    ┌────┴────┐
                    │  10-20个 │  专业Skills（场景加载）
                    │  专业    │  - 安全审计
                    └────┬────┘  - 性能分析
                         │       - 数据库优化
                    ┌────┴────┐
                    │  20+个   │  扩展Skills（惰性加载）
                    │  扩展    │  - 特定框架支持
                    └─────────┘  - 企业定制工具
```

### 配置示例

```json
{
  "skills": {
    "core": {
      "always_load": ["file_ops", "code_search", "git_ops"],
      "max_tokens": 1000
    },
    "dynamic": {
      "load_on_demand": true,
      "trigger_keywords": {
        "test": ["test_gen", "coverage_check"],
        "doc": ["doc_gen", "api_doc"],
        "refactor": ["code_smell", "complexity_check"]
      },
      "max_tokens": 2000
    },
    "lazy": {
      "load_on_first_use": true,
      "categories": ["security", "performance", "custom"],
      "max_tokens": 3000
    }
  }
}
```

---

## 📝 学习检查清单

完成本节学习后，你应该能够回答以下问题：

- [ ] **人vs AI**：在你的日常开发中，哪些任务适合交给AI？哪些必须自己来？为什么？
- [ ] **常见误区**：新人使用AI编程最容易犯的5个错误是什么？你有没有犯过其中一些？
- [ ] **日常Checklist**：使用AI写代码时，你应该在哪些环节做检查？
- [ ] **Skills类比**：用你自己的话解释Skills系统，并举一个生活中的类比
- [ ] **Skills检索**：当Skills数量很多时，系统如何精准找到需要的Skill？有哪几种策略？
- [ ] **上下文管理**：为什么不能一次性加载所有Skills？selectTopK函数是如何解决这个问题的？
- [ ] **模型困惑**：当Skills太多导致AI困惑时，有哪4种策略可以解决？每种策略的核心思想是什么？
- [ ] **实际应用**：如果你要设计一个AI编程助手的Skills系统，你会如何分类和管理？

> **上一篇**：[Claude Code相关技术对比与深度问题](../03-comparative-analysis/01-claude-comparison.md)
> **下一篇**：[案例学习：威胁情报 Agent 系统设计](../05-case-studies/01-sangfor-case-study.md)

---

## 📎 附录：Claude Code 官方 Skills 机制

上面讨论的 SkillRegistry、触发词索引、置信度过滤等是一种分析性设计框架，用于理解 Skills 管理的核心问题。Claude Code 官方的 Skills 机制实现方式如下：

### Skills 定义格式

在 `.claude/commands/` 目录下创建 Markdown 文件即可定义 Skill：

```markdown
---
name: review-code
description: "对代码变更进行自动化审查，检测安全漏洞、性能问题和代码规范"
---

你是一名资深代码审查工程师。请对以下代码变更进行审查：

1. 检查安全漏洞（SQL注入、XSS、硬编码密钥等）
2. 检查性能问题（N+1查询、内存泄漏等）
3. 检查代码规范（命名、文档、复杂度等）

输出格式：按严重程度排序的问题列表，每个问题包含位置、描述和修复建议。
```

### 关键字段说明

| 字段 | 作用 | 示例 |
|------|------|------|
| `name` | Skill 的唯一标识符 | `review-code` |
| `description` | 描述 Skill 的功能，用于触发匹配 | `"对代码变更进行自动化审查"` |
| 正文内容 | Skill 被激活后的系统提示词 | 完整的审查指令 |

### 触发机制

Claude Code 通过 `description` 字段进行语义匹配：当用户请求与某个 Skill 的描述相关时，该 Skill 被激活，其正文内容作为系统提示词注入到对话上下文中。

### 隔离执行

```yaml
---
name: deep-analysis
description: "深度代码分析"
context: fork  # 在隔离的子代理中执行
---
```

`context: fork` 选项会让 Skill 在独立的子代理中运行，避免污染主对话上下文。

### 与本节设计框架的关系

| 本节概念 | 官方机制对应 |
|----------|-------------|
| SkillRegistry | `.claude/commands/` 目录 + YAML frontmatter |
| 触发词索引 | `description` 字段的语义匹配 |
| 置信度过滤 | 模型内部的匹配度判断 |
| 分层加载 | `context: fork` 隔离执行 |
| Skill 参数 | 用户在调用时提供的参数 |

> 💡 **理解桥梁**：本节的 SkillRegistry、触发词索引等概念与官方机制的关系，就像"数据库索引原理"与"MySQL B+树索引"的关系。前者回答的是"为什么需要这些机制"，后者回答的是"具体如何实现"。