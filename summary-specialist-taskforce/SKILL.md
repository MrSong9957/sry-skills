---
name: summary-specialist-taskforce
description: ">一个由 AI IDE 工作流研究员、工程经验提炼专家、技术文档架构师、失败模式分析师和提示词策略专家组成的团队型技能。负责从对话中提炼成功经验与失败教训，自动去重、分组、合并，并持续写入统一文档 docs/ai-ide-lessons.md，同时自动更新 Last Updated 时间戳。"
---

# 1. 触发条件（When to Trigger）
当用户需要：
- 总结 AI IDE 执行经验  
- 提炼成功模式与失败模式  
- 更新统一经验文档  
- 维护知识库  

此技能即被触发。

---

# 2. 输入（Inputs）
inputs:
  conversation_context:
    type: string
    required: true
    description: 对话上下文，用于提取经验与教训

---

# 3. 输出（Outputs）
outputs:
  document_update:
    type: object
    description: >
      结构化的文档更新内容，包括：
      - 文档路径
      - 更新后的完整文档内容
      - 自动更新的 Last Updated 时间戳

---

# 4. 前置条件（Preconditions）
preconditions:
  - 必须能够读取 docs/ai-ide-lessons.md（若存在）
  - 必须能够访问对话上下文
  - 禁止虚构不存在的上下文
  - 禁止创建多个文档

---

# 5. 执行步骤（Execution Steps）
steps:

  - id: extract-key-insights
    name: Step 1 — 提取上下文中的关键信息
    run: |
      从对话中提取：
      - 成功步骤、策略、提示词、技能调用
      - 失败步骤、原因、模式、触发条件
      - 用户与 AI IDE 的交互方式
      - 有效与无效的做法
      - 成功的提示词结构
      - 导致失败的上下文缺失
      要求：保留所有关键细节，但表达通俗易懂。
    output: extracted_insights

  - id: deduplicate
    name: Step 2 — 自动去重（Deduplication）
    run: |
      1. 检查 docs/ai-ide-lessons.md 中是否已有类似经验
      2. 若已有 → 合并、精炼，不重复写入
      3. 若没有 → 追加新的经验
      禁止：
      - 重复内容
      - 语义相同但表达不同的重复项
      - 冗余段落
    output: deduped_insights

  - id: cluster
    name: Step 3 — 自动分组（Clustering）
    run: |
      将经验自动归类到以下主题组：

      ## Success Patterns
      - Prompt Structure
      - Context Preparation
      - Skill Invocation
      - Workflow Sequencing
      - Debugging Strategy
      - Verification Strategy
      - Communication Strategy

      ## Failure Patterns
      - Missing Context
      - Wrong Skill
      - Workflow Break
      - Command Failure
      - Model Hallucination
      - Prompt Ambiguity
      - Over-scoped Tasks

      自动选择最合适的小节写入。
    output: clustered_insights

  - id: generate-document
    name: Step 4 — 生成文档（Documentation）
    run: |
      1. 写入统一文档：docs/ai-ide-lessons.md
      2. 自动更新 Last Updated: <YYYY-MM-DD HH:MM>
         - 使用 24 小时制
         - 使用用户所在时区
         - 必须位于文档最开头
      3. 文档结构必须保持一致：

         Last Updated: <当前日期时间>

         # AI IDE Execution Lessons

         ## Summary
         <内容>

         ## Success Patterns
         ### Prompt Structure
         <内容>
         ### Context Preparation
         <内容>
         ### Skill Invocation
         <内容>
         ### Workflow Sequencing
         <内容>
         ### Debugging Strategy
         <内容>
         ### Verification Strategy
         <内容>
         ### Communication Strategy
         <内容>

         ## Failure Patterns
         ### Missing Context
         <内容>
         ### Wrong Skill
         <内容>
         ### Workflow Break
         <内容>
         ### Command Failure
         <内容>
         ### Model Hallucination
         <内容>
         ### Prompt Ambiguity
         <内容>
         ### Over-scoped Tasks
         <内容>

         ## Practical Recommendations
         <内容>

      4. 文档必须：
         - 简洁
         - 通俗
         - 结构化
         - 不丢失任何关键细节
         - 持续累积（append + merge）
         - 永远只使用一个文件
    output: updated_document

---

# 6. 禁止事项（Hard Constraints）
forbidden:
  - 写代码
  - 执行技能
  - 执行 commands
  - 修改项目文件（除 docs/ai-ide-lessons.md 外）
  - 虚构不存在的上下文
  - 输出非结构化内容
  - 闲聊模式
  - 创建多个文档
  - 使用时间戳作为文件名
  - 重复写入相同经验

required:
  - 自动去重
  - 自动分组
  - 自动合并相似经验
  - 保留所有关键细节
  - 使用通俗语言
  - 输出结构化文档
  - 始终写入 docs/ai-ide-lessons.md
  - 每次更新文档时更新 Last Updated

---

# 7. 技能目标（Goals）
goals:
  - 构建统一的 AI IDE 经验知识库
  - 持续提炼成功经验与失败教训
  - 自动维护结构化文档
  - 保证文档可复用、可阅读、可学习
  - 自动记录更新时间
  - 作为经验提炼器，而非执行代理