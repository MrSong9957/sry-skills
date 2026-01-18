---
name: locate-ui-source
description: >
  根据给定页面路径，生成一份包含必要上下文的文档（UI Source Context Doc）。本文档是所有前端页面修改任务的前置信息：任何修改页面的技能、SOP 或 To‑Do List。都必须在执行前先运行 locate-ui-source，并读取它生成的文档。本技能会递归解析页面及其依赖的 import 链，定位所有 UI 源头文件。文档名称格式为：<shortname>-<timestamp>.md（全小写、简短、带时间戳）。
---

## 执行协议（Execution Protocol）

为确保执行过程稳定、可控、可复现，locate-ui-source 必须遵循以下协议：

### 1. 严格步骤顺序（Strict Step Order）
所有步骤必须按定义顺序执行，不得跳过、合并或重排。

### 2. 文档驱动（Document-Driven Execution）
- 每一步执行后必须写入文档（SSOT）。  
- 下一步执行前必须读取最新文档。  
- 文档是唯一事实来源（Single Source of Truth）。

### 3. 禁止推测（No Guessing）
不得基于推测生成不存在的文件路径、组件、布局或样式来源。

### 4. 递归解析（Recursive Import Resolution）
必须从页面文件开始，递归解析所有 import 链，直到找到所有源头文件。

### 5. 不可跳过写入（No Write Skipping）
每一步的写入操作都是强制性的，不得省略。

### 6. 不可跳过读取（No Read Skipping）
下一步执行前必须读取文档中对应字段，否则立即停止执行。

### 7. 断言强制（Assertions Required）
每一步的断言必须通过，否则立即停止执行。

### 8. 失败即停止（Fail Fast）
任意步骤失败、断言不通过、文档字段缺失 → 立即终止执行。

### 9. 输出文档必须符合命名规则（Output Naming Enforcement）
文档路径必须符合：  
`docs/<shortname>-<timestamp>.md`

### 10. 执行结果唯一性（Single Output Rule）
整个执行过程只生成一个文档，所有信息必须写入同一文档中。

---

## 1. Skill 目标（最小必要性）

locate-ui-source 的唯一目标是：

- 输入一个页面路径  
- 递归解析页面的 import 链（components / layouts / styles / theme / tokens）  
- 找到所有 UI 源头文件  
- 输出一份上下文文档（UI Source Context Doc）  
- 文档名称为：`<shortname>-<timestamp>.md`  
- 不执行任何修改、不生成 diff、不写文件  

任何前端页面修改任务，都必须先执行 locate-ui-source。

---

## 2. Skill 输入格式（结构化块）

```yaml
page: <页面路径>   # 必填，例如 src/pages/login/index.tsx
```

---

## 3. 执行步骤（最小必要性）

```text
Step 1：解析页面文件并提取 import 列表  
Step 2：递归解析 import 链并分类源头文件  
Step 3：生成上下文文档并写入指定路径  
```

---

## 4. 文档格式（UI Source Context Doc）

```yaml
page: <页面路径>

imports:
  direct: [...]        # 页面直接 import 的文件
  recursive: [...]     # 递归解析后的所有文件（去重）

ui_sources:
  layouts: [...]       # 布局源头文件
  components: [...]    # 组件源头文件
  styles: [...]        # 样式源头文件
  theme: [...]         # 主题文件
  tokens: [...]        # 设计 tokens

structure_summary:
  jsx_tree: <页面结构摘要>
  layout_used: <使用的布局>
  key_components: [...]
  style_sources: [...]

recommended_edit_points:
  - <源头文件路径>
  - <建议修改的组件或样式文件>
```

---

## 5. 文档命名规则（最终版）

```
docs/<shortname>-<timestamp>.md
```

### shortname 生成规则：
- 若文件名为 index，则取上级目录名  
- 去除扩展名  
- 全部转为小写  
- 去除非字母数字字符  

### timestamp 生成规则：
- 使用执行时的本地系统时间  
- 格式：`YYYYMMDD-HHMM`

示例：

```
docs/login-20260118-1921.md
docs/profile-20260118-1921.md
```

---

## 6. 可执行块（AI IDE 能执行）

```yaml
execute:
  step: generate_context_doc
  read:
    - input.page
  write:
    - field: output_doc_path
      value: "docs/{{shortname}}-{{timestamp}}.md"
    - field: ui_source_context
      value: "{{generated_context_doc}}"
    - field: execution_log.generate_context_doc
      value: success
  assert:
    - ui_source_context.page != null
```

---

## 7. 文档说明

生成的文档是：

- 所有前端页面修改任务的前置输入  
- 页面修改的唯一上下文来源（SSOT）  
- 包含页面的所有源头信息  
- 不包含 diff、不包含修改计划  
- 只包含“页面从哪里来”的信息  

---