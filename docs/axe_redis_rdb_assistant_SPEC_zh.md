# 基于 axe 的 Redis RDB 分析助手主 SPEC

> **Version**: 2.1  
> **Language**: 中文  
> **Status**: Draft for Review  
> **Assumed Repo Root**: `/Users/zqw/Desktop/Project/axe-dba-assistant`

---

## 一、文档定位

本文档是「基于 axe 的 Redis RDB 分析助手」的主规格说明，定义项目级稳定要求：建设目标、阶段规划、职责切分框架、Skill 与 Tool 的边界、行为边界、文档体系、验收标准。

主 SPEC 保持长期稳定，不承接具体实现细节，不细化每个阶段的开发任务，不列举 Redis RDB 分析字段全集。具体实现由阶段 SPEC、Skill 文档、references、assets、tools 文档承接。

---

## 二、项目背景与真实终态

当前已有一个基于 DeepAgents SDK 的 DBA Assistant 项目，已实现 Redis RDB 分析能力，但暴露出以下问题：

1. 业务流程容易写死在控制层；
2. Skill 作用边界不够清晰；
3. 目录结构混乱，实验代码、临时逻辑与正式能力混杂；
4. LLM 决策、Tool 执行、Skill 指导之间的边界不够稳定。

本项目基于 axe 重新实现 Redis RDB 分析助手。真实终态不是简单替代 DBA Assistant，而是为未来运维助手技术路线决策提供依据：到底应优先选择 axe，还是继续使用 DeepAgents SDK。

参考项目仅用于参考分析逻辑，不继承目录结构：

```text
本地：/Users/zqw/Desktop/Project/dba_assistant
GitHub：https://github.com/weiqinzhou3/dba_assistant
```

---

## 三、阶段规划与状态

### 3.1 阶段状态枚举

阶段状态使用以下枚举：

| 状态 | 含义 |
|---|---|
| `planning` | 已规划，尚未开始实现 |
| `starting` | 已开始，正在搭建或开发 |
| `in_progress` | 主体开发中 |
| `blocked` | 被外部条件或关键问题阻塞 |
| `reviewing` | 已完成实现，正在评审 |
| `finished` | 已完成、评审通过、关闭 |

### 3.2 当前阶段总表

> 本表是主 SPEC 的阶段索引。每个阶段的详细范围以对应 phase SPEC 为准。

| Phase | 阶段名称 | 当前状态 | 本地 Phase SPEC 绝对路径 | 阶段目标 |
|---|---|---|---|---|
| Phase-01 | Skill First 本地 RDB MVP | `finished` | `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-01-skill-first-local-rdb-mvp.md` | 建立 axe agent、Redis RDB Skill、RDB 本地分析脚本、最小 summary / JSON / docx 输出；验证 Skill 驱动闭环 |
| Phase-02 | 输出规范与三层验证强化 | `planning` | `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-02-output-validation-hardening.md` | 稳定 JSON schema、报告结构、机械验证、逻辑验证、充分性验证、source 约束、partial/failed/uncertainty 状态 |
| Phase-03 | References / Assets / Profiles 完整化 | `planning` | `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-03-skill-assets-references-profiles.md` | 完善 Big Key 阈值、风险等级、建议库、profile、docx 模板和报告资产；让 Skill 更薄、更稳定 |
| Phase-04 | 审计与可复现 | `planning` | `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-04-audit-repeatability.md` | 实现完整运行归档、stdout/stderr、axe verbose/json trace、token/latency/tool-call 记录和多次运行沉淀 |
| Phase-05 | Skill 经验与路线对比准备 | `planning` | `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-05-skill-experience-comparison-prep.md` | 输出 Skill 设计经验、反模式、axe 一侧证据材料，为人工对比 DeepAgents SDK 做准备 |

### 3.3 阶段边界原则

1. 主 SPEC 只维护阶段索引、状态和总体目标；
2. 阶段任务、非目标、验收清单写入独立 phase SPEC；
3. Phase SPEC 可以频繁演进，主 SPEC 不应因普通任务调整而频繁修改；
4. 进入下一阶段前必须完成上一阶段 closeout；
5. 如果阶段目标突破本 SPEC 的职责切分、axe 使用宪法或行为边界，必须先修订主 SPEC。

---

## 四、验证目标与对比维度

### 4.1 Skill / Tool 边界要回答的问题

本项目必须通过实践回答以下问题：

1. Skill 应承担什么职责；
2. Tool 或自定义功能应承担什么职责；
3. scripts、tools、references、assets 的边界在哪里；
4. 如何尽量用 Skill 驱动 Agent 行为；
5. 如何避免业务流程过度写死在代码中；
6. 如何让 Skill 成为项目中的核心资产；
7. 如何围绕 Skill 管理 assets、scripts、references、profiles；
8. 如何在保留 LLM 决策能力的同时保证结果可靠、可复核、可交付。

### 4.2 阶段一须沉淀的对比数据

| 维度 | 含义 | 阶段一须沉淀 |
|---|---|---|
| C1. Skill 可读性 | 第三方能否快速读懂助手在做什么 | Skill 主文档、引用资产、边界说明 |
| C2. 运行结果稳定性 | 同输入多次运行的一致性 | 同一 RDB 文件多次运行输出 |
| C3. LLM 决策空间 | LLM 决策 vs 代码/框架约束 | 每次运行的决策轨迹、调用路径 |
| C4. token / 时延 | 单次完整分析的成本与耗时 | axe verbose/json 中的 token/latency 信息 |
| C5. 可调试性 | 出错时定位问题难度 | 失败案例、stdout/stderr、trace 记录 |
| C6. 跨场景复用性 | 能否平移到巡检、CVE、慢 SQL 等分析场景 | tools、assets、references 是否可复用 |

阶段二对比由人工完成，本项目阶段一只负责沉淀 axe 一侧证据。

---

## 五、职责切分框架

### 5.1 五个职责层

| 层 | 判定问题 | 典型内容 |
|---|---|---|
| Code / Script | 同输入是否每次得出相同结果？是否无需理解自然语言？ | 本地 RDB 解析、统计、文件检查、SHA256、结构化结果生成 |
| Tool | 是否可被多个 Skill 复用？是否是稳定确定性能力？ | docx 渲染、通用验证、归档、文件指纹、通用格式转换 |
| References | 是否是数值、标准、阈值、风险等级、建议库？ | Big Key 阈值、风险等级、Redis 建议库、profiles |
| Assets | 是否是模板、样式、示例、静态交付资产？ | docx 模板、报告章节模板、样式文件 |
| Skill | 是否是稳定领域规则，需要让 LLM 在运行时读取并遵守？ | 意图识别规则、流程原则、调用规则、证据要求、禁止行为 |
| LLM Runtime | 是否需要理解或生成自然语言？是否需要多信号综合？ | 用户意图理解、综合风险判断、充分性判断、最终回复措辞 |

### 5.2 一句话原则

**RDB 专属执行动作放 Skill scripts；跨 Skill 复用的确定性能力放 tools；阈值、风险等级、建议库和 profiles 放 references；模板和版式资产放 assets；让 Skill 告诉 LLM 如何使用这些能力。**

### 5.3 scripts、tools、src 的项目约束

本项目初期不引入 `src/` 目录作为默认实现层，避免过早抽象。

Phase-01 约束：

1. Redis RDB 专属动作放入 `skills/redis-rdb-analysis/scripts/`；
2. 通用 docx 渲染能力放入 `tools/docx_renderer/`；
3. 通用验证能力放入 `tools/validation/`；
4. `skills/scripts` 可以内部调用 `tools`；
5. LLM 在 Phase-01 只需直接调用 RDB Skill script，不直接编排多个 tools；
6. 暂不创建 `src/`，除非后续阶段明确出现脚本膨胀或多 Skill 共享库需求。

### 5.4 三层验证

| 层 | 内容 | 责任方 |
|---|---|---|
| 机械验证 | RDB 文件存在？解析成功？命令退出码是否为 0？输出文件是否生成？ | Skill script + tools/validation |
| 逻辑验证 | Key 总数、类型分布、TTL 统计、source 字段、schema 是否一致？ | Skill script + tools/validation + references |
| 充分性验证 | 当前数据是否足以回答用户问题？哪些结论只能作为不确定项？ | LLM + SKILL.md |

---

## 六、axe 原生能力使用宪法

| axe 能力 | 本项目使用原则 |
|---|---|
| built-in tools | 允许使用，尤其是 read_file / write_file / list_directory / run_command |
| run_command | Phase-01 主要通过 run_command 调用 Skill scripts |
| Skill scripts | 允许使用，是本项目 Skill 能力包的重要组成部分 |
| `--verbose` / `--json` | 必须用于审计与对比数据沉淀 |
| memory | 默认不启用，除非后续阶段明确要求跨次分析对比 |
| sub-agent | 不使用，保持 single-agent |
| MCP server | 不使用，不在本项目范围 |
| patch axe | 禁止 |
| 封装 axe 本体 | 禁止 |

能力优先级：

```text
Skill scripts → run_command 调本地 CLI → tools 通用能力 → 自定义 agent tool（后续再评估）
```

---

## 七、核心能力总纲

助手最终应具备：

1. 接收并理解中英文自然语言 RDB 分析请求；
2. 识别 RDB 文件路径、分析目标、输出形式、profile；
3. 输入不完整时提示补充；
4. 完成本地 Redis RDB 基础分析、Big Key 分析、类型分布、TTL 分析；
5. 基于数据进行风险识别和优化建议；
6. 完成机械、逻辑、充分性三层验证；
7. 输出三种形态：终端摘要、JSON 结构化结果、docx 正式报告；
8. 明确标识 success、partial、failed、uncertainty；
9. 每次运行产出审计记录；
10. 为后续 axe vs DeepAgents SDK 人工对比沉淀证据。

---

## 八、输入与输出形态约束

### 8.1 输入

支持自然语言输入。Phase-01 只支持本地 RDB 文件。

### 8.2 输出

| 输出形态 | 用途 | 约束 |
|---|---|---|
| 终端摘要 | 快速查看 | 简洁、覆盖关键发现、说明状态和不确定项 |
| JSON 结构化结果 | 复核与后续处理 | 字段稳定、source 完整、可被工具校验 |
| docx 正式报告 | 交付与归档 | Phase-01 允许最小 docx；后续阶段增强版式与章节 |

### 8.3 docx 责任边界

1. 通用 docx 渲染引擎放入 `tools/docx_renderer/`；
2. Redis RDB 报告模板、章节配置、样式资产放入 `skills/redis-rdb-analysis/assets/`；
3. Skill 说明报告应包含哪些业务内容；
4. 脚本负责把 RDB 分析结果映射到模板输入；
5. LLM 不直接操作 docx 版式。

---

## 九、推荐仓库组织

```text
axe-dba-assistant/
├── agents/
│   └── redis/
│       └── redis-rdb-assistant.toml
├── skills/
│   └── redis-rdb-analysis/
│       ├── SKILL.md
│       ├── scripts/
│       │   └── analyze_local_rdb.py
│       ├── references/
│       │   ├── redis_bigkey_thresholds.yaml
│       │   ├── redis_risk_levels.yaml
│       │   ├── redis_recommendations.yaml
│       │   └── profiles/
│       │       ├── default.yaml
│       │       ├── rcs.yaml
│       │       └── concise.yaml
│       └── assets/
│           └── docx_templates/
├── tools/
│   ├── docx_renderer/
│   └── validation/
├── examples/
├── tests/
└── docs/
    ├── phases/
    ├── reviews/
    └── decisions/
```

目录约束：

1. Phase-01 不创建 `src/`；
2. 不创建根目录 `scripts/`，避免与 Skill scripts 混淆；
3. Redis RDB 专属动作留在 Skill 包内；
4. 跨 Skill 复用的确定性能力放入 `tools/`；
5. Phase 文档统一放入 `docs/phases/`。

---

## 十、归档与审计目录

运行产物归档至：

```text
/tmp/axe_rdb_assistant/<run_id>/
├── report.docx
├── result.json
├── summary.txt
├── audit/
│   ├── meta.json
│   ├── stdout.log
│   ├── stderr.log
│   └── trace.json
└── input/
    ├── user_request.txt
    └── rdb.fingerprint
```

Phase-01 可先实现最小归档，但最终阶段一必须满足完整结构。

---

## 十一、Skill 要求与反模式

### 11.1 Skill 定位

Skill 是给 LLM 在运行时消费的领域操作手册，不是工程师产品说明书，也不是代码仓库目录说明。

### 11.2 Skill 应描述

1. 任务目标；
2. 何时使用该 Skill；
3. 用户输入识别规则；
4. 本地 RDB 分析流程原则；
5. 应调用哪个 Skill script；
6. references、assets、tools 的使用规则；
7. 证据与 source 要求；
8. 输出要求；
9. 失败与不确定项处理；
10. 禁止行为。

### 11.3 反模式

禁止：

1. 在 SKILL.md 内嵌可执行代码；
2. 在 SKILL.md 写死阈值；
3. 在 SKILL.md 内嵌 docx 版式细节；
4. 让 tools 替代 Skill 成为流程大脑；
5. 让 scripts 绕过 Skill 形成黑盒；
6. 让 LLM 承担确定性统计、过滤、计算；
7. 将 partial 分析伪装为完整成功；
8. 继承原 DBA Assistant 的混乱结构。

---

## 十二、行为边界

### 12.1 允许

1. 分析用户指定的本地 RDB 文件；
2. 生成 summary、JSON、docx；
3. 基于 references 输出风险判断；
4. 基于 tools 做通用验证和 docx 渲染；
5. 明确说明无法判断和信息不足；
6. 基于 axe verbose/json 沉淀运行证据。

### 12.2 禁止

1. 无依据输出确定结论；
2. 伪造 Key、统计、风险；
3. 隐瞒失败；
4. 将部分分析伪装为全量；
5. patch axe；
6. 封装 axe 本体；
7. 引入 MCP；
8. 引入 sub-agent；
9. 让 Tool 替代 Skill 成为流程大脑；
10. 在 Phase-01 引入远程 Redis、SSH 拉取、MySQL staging。

---

## 十三、阶段一总体验收标准

阶段一结束时至少满足：

1. 可运行 axe agent；
2. Redis RDB Analysis Skill 可被加载；
3. 本地 RDB 文件端到端分析跑通；
4. 输出 summary、result.json、report.docx；
5. 三层验证可用；
6. 每条结论性输出可追溯 source；
7. 完整运行归档可生成；
8. Skill、scripts、tools、references、assets 边界清楚；
9. 未引入 MCP、sub-agent、axe patch；
10. 已沉淀 Skill 设计经验、反模式和 axe 一侧对比材料。

---

## 十四、文档体系

```text
主 SPEC
  ├── docs/phases/phase-01-skill-first-local-rdb-mvp.md
  ├── docs/phases/phase-02-output-validation-hardening.md
  ├── docs/phases/phase-03-skill-assets-references-profiles.md
  ├── docs/phases/phase-04-audit-repeatability.md
  ├── docs/phases/phase-05-skill-experience-comparison-prep.md
  ├── docs/reviews/
  ├── docs/decisions/
  ├── skills/redis-rdb-analysis/SKILL.md
  └── tools/*/README.md
```

---

## 十五、SPEC 演进规则

主 SPEC 仅在以下情况修改：

1. 项目目标变化；
2. 阶段规划变化；
3. 职责切分框架变化；
4. axe 使用宪法变化；
5. 行为边界变化；
6. 仓库组织原则变化；
7. 阶段状态需要更新。

普通实现细节、任务拆分、脚本参数、字段扩展，进入 phase SPEC、Skill 文档或 tools 文档，不修改主 SPEC。
