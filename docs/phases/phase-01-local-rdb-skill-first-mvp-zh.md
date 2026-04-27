# Phase-01 SPEC：最小 MVP —— 本地 RDB 分析跑通与 Skill First 骨架

> **Project**: axe-dba-assistant  
> **Phase**: Phase-01  
> **Phase Name**: 最小 MVP：本地 RDB 分析跑通与 Skill First 骨架  
> **Status**: planning  
> **Language**: 中文  
> **Owner**: TBD  
> **Main SPEC**: `axe_redis_rdb_assistant_SPEC_zh_v2_1.md`  
> **Local Phase SPEC Path**: `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-01-local-rdb-skill-first-mvp.md`

---

## 一、阶段定位

Phase-01 是「基于 axe 的 Redis RDB 分析助手」的最小 MVP 阶段。

本阶段的目标不是完成一个完整成熟的 DBA Assistant，而是在 axe 的运行模型下跑通一个**可验证、可复核、Skill First** 的最小 Redis RDB 分析闭环。

本阶段必须回答四个问题：

1. axe agent 是否可以通过 `SKILL.md` 驱动 Redis RDB 分析任务；
2. Redis RDB 本地文件分析是否可以通过 Skill 内 scripts 跑通；
3. 通用 docx 渲染与通用验证能力是否可以作为 `tools/` 被 RDB Skill script 复用；
4. 最小产物是否满足后续 Phase-02 / Phase-03 继续增强的基础。

---

## 二、阶段目标

### 2.1 最小功能目标

Phase-01 结束时，必须支持以下场景：

```bash
axe run --agents-dir agents/redis redis-rdb-assistant \
  -p "请分析本地 RDB 文件 /tmp/dump.rdb，按照默认 profile 输出摘要、JSON 和 docx 报告"
```

最小可接受结果：

1. axe agent 能启动；
2. agent 能加载 `redis-rdb-analysis` Skill；
3. LLM 能基于 `SKILL.md` 判断这是本地 Redis RDB 分析请求；
4. LLM 能识别用户提供的本地 RDB 文件路径；
5. LLM 能通过 `run_command` 调用 Skill script；
6. Skill script 能完成本地 RDB 文件基础分析；
7. 能生成：
   - `summary.txt`
   - `result.json`
   - `report.docx`
8. 能完成最小机械验证、逻辑验证和充分性验证；
9. 输出结论必须能追溯 source；
10. 失败时不得伪装成功。

### 2.2 架构目标

Phase-01 必须建立以下职责边界：

| 层级 | Phase-01 实物 | 说明 |
|---|---|---|
| Agent | `agents/redis/redis-rdb-assistant.toml` | axe agent 配置 |
| Skill | `skills/redis-rdb-analysis/SKILL.md` | LLM 的领域操作手册 |
| Skill Scripts | `skills/redis-rdb-analysis/scripts/analyze_local_rdb.py` | Redis RDB 专属执行入口 |
| Skill References | `skills/redis-rdb-analysis/references/` | RDB 阈值、风险等级、建议库、profiles |
| Skill Assets | `skills/redis-rdb-analysis/assets/` | RDB 报告模板、章节配置、样式资产 |
| Tools | `tools/docx_renderer/`, `tools/validation/` | 多 Skill 可复用的确定性能力 |
| Examples | `examples/` | 示例请求与输出 |
| Tests | `tests/` | 最小 schema / validation / docx 测试 |
| Docs | `docs/` | phase spec、review、closeout、decisions |

---

## 三、本阶段明确不做

Phase-01 严格禁止 scope creep。

本阶段不做：

1. 不做远程 Redis 连接；
2. 不做 SSH 拉取 RDB；
3. 不做触发 `BGSAVE`；
4. 不做 MySQL staging；
5. 不做多 RDB 合并分析；
6. 不做复杂 profile 继承体系；
7. 不做完整 Big Key 深度诊断；
8. 不做完整风险知识库；
9. 不做复杂 docx 版式；
10. 不做 Web / API；
11. 不做 MCP；
12. 不做 sub-agent；
13. 不 patch axe；
14. 不封装 axe 本体；
15. 不引入 `src/`；
16. 不创建根目录 `scripts/`；
17. 不把原 DBA Assistant 的目录结构搬过来。

如实现过程中发现上述需求，只能记录到 `docs/reviews/phase-01-closeout.md` 的 Deferred Items，不得在 Phase-01 实现。

---

## 四、最终目录结构

Phase-01 采用如下目录结构：

```text
axe-dba-assistant/
├── agents/
│   └── redis/
│       └── redis-rdb-assistant.toml
├── skills/
│   └── redis-rdb-analysis/
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── analyze_local_rdb.py
│       │   └── README.md
│       ├── references/
│       │   ├── redis_bigkey_thresholds.yaml
│       │   ├── redis_risk_levels.yaml
│       │   ├── redis_recommendations.yaml
│       │   └── profiles/
│       │       ├── default.yaml
│       │       ├── rcs.yaml
│       │       └── concise.yaml
│       └── assets/
│           ├── report_outline.yaml
│           └── docx_templates/
│               └── minimal_report_template.docx
├── tools/
│   ├── docx_renderer/
│   │   ├── render_docx.py
│   │   └── README.md
│   └── validation/
│       ├── validate_result.py
│       └── README.md
├── examples/
│   ├── requests/
│   │   └── local_rdb_default_zh.txt
│   └── outputs/
│       └── README.md
├── tests/
│   ├── test_result_schema.py
│   ├── test_validation.py
│   └── test_docx_renderer.py
├── docs/
│   ├── phases/
│   │   └── phase-01-local-rdb-skill-first-mvp.md
│   ├── reviews/
│   │   ├── phase-01-review.md
│   │   └── phase-01-closeout.md
│   └── decisions/
│       └── decisions.md
├── pyproject.toml
└── README.md
```

### 4.1 目录边界说明

| 目录 | 允许内容 | 禁止内容 |
|---|---|---|
| `agents/` | axe agent 配置 | 业务逻辑 |
| `skills/redis-rdb-analysis/SKILL.md` | LLM 行为规则、调用规则、输出约束、禁止行为 | Python / Shell 可执行代码 |
| `skills/redis-rdb-analysis/scripts/` | Redis RDB 分析专属脚本 | 通用 docx 引擎、通用验证框架 |
| `skills/redis-rdb-analysis/references/` | 阈值、风险等级、建议库、profiles | 执行逻辑 |
| `skills/redis-rdb-analysis/assets/` | docx 模板、报告大纲、样式资产 | RDB 解析逻辑 |
| `tools/docx_renderer/` | 通用 docx 渲染能力 | Redis RDB 领域判断 |
| `tools/validation/` | 通用验证能力 | Redis RDB 专属阈值 |
| `examples/` | 示例请求与示例输出 | 测试主逻辑 |
| `tests/` | 自动化测试 | 运行时产物 |
| `docs/` | 设计、评审、closeout | 可执行业务逻辑 |

---

## 五、执行链路

Phase-01 的执行链路必须保持简单：

```text
用户自然语言请求
  ↓
axe agent 启动
  ↓
读取 agents/redis/redis-rdb-assistant.toml
  ↓
加载 skills/redis-rdb-analysis/SKILL.md
  ↓
LLM 基于 SKILL.md 判断：
  - 是否为 Redis RDB 分析请求
  - 是否为本地 RDB 文件
  - 是否已提供 RDB 路径
  - 应使用哪个 profile
  ↓
LLM 使用 run_command 调用：
skills/redis-rdb-analysis/scripts/analyze_local_rdb.py
  ↓
analyze_local_rdb.py 执行 RDB 专属动作：
  - 文件存在性检查
  - SHA256 指纹计算
  - RDB 基础解析
  - 类型分布统计
  - TTL 概况统计
  - 最小 Big Key 占位或基础识别
  - 读取 references / profiles
  ↓
analyze_local_rdb.py 调用 tools/validation：
  - schema 校验
  - required fields 校验
  - source 字段校验
  - 加总一致性校验
  - status 规范化
  ↓
analyze_local_rdb.py 调用 tools/docx_renderer：
  - 读取 Skill assets 中的模板和大纲
  - 生成最小 report.docx
  ↓
输出到 /tmp/axe_rdb_assistant/<run_id>/
  - result.json
  - summary.txt
  - report.docx
  - input/user_request.txt
  - input/rdb.fingerprint
  ↓
LLM 读取 result.json / summary.txt
  ↓
LLM 根据 SKILL.md 输出最终回复
```

### 5.1 本阶段禁止的执行链路

禁止：

```text
LLM → tools/docx_renderer
LLM → tools/validation
LLM → 多个工具自行编排流程
```

Phase-01 中，LLM 只直接调用 RDB Skill script：

```text
LLM → skills/redis-rdb-analysis/scripts/analyze_local_rdb.py
```

`tools/docx_renderer` 与 `tools/validation` 由 `analyze_local_rdb.py` 内部调用。

---

## 六、Skill 要求

### 6.1 SKILL.md 必须包含的章节

`skills/redis-rdb-analysis/SKILL.md` 必须至少包含：

```markdown
# Redis RDB Analysis Skill

## 1. Purpose
## 2. When to Use This Skill
## 3. Supported Inputs
## 4. Unsupported Inputs
## 5. User Intent Recognition Rules
## 6. Local RDB Analysis Workflow
## 7. Script Invocation Contract
## 8. References and Profiles
## 9. Assets and Report Template
## 10. Evidence and Source Requirements
## 11. Output Requirements
## 12. Validation Requirements
## 13. Uncertainty Handling
## 14. Failure Handling
## 15. Forbidden Behaviors
```

### 6.2 SKILL.md 的职责

SKILL.md 负责：

1. 告诉 LLM 什么时候使用 Redis RDB Analysis Skill；
2. 告诉 LLM 如何识别本地 RDB 文件路径；
3. 告诉 LLM 缺少路径时必须要求补充；
4. 告诉 LLM 本阶段只支持本地 RDB；
5. 告诉 LLM 如何选择 profile；
6. 告诉 LLM 应调用哪个 script；
7. 告诉 LLM 调用 script 后必须读取 `result.json`；
8. 告诉 LLM 如何区分事实、推断、不确定项和失败；
9. 告诉 LLM 不得伪造 Key、统计值、风险和建议；
10. 告诉 LLM 输出必须与 source 对齐。

### 6.3 SKILL.md 不得承担的职责

SKILL.md 不得：

1. 内嵌 Python / Shell 代码；
2. 硬编码 Big Key 阈值；
3. 硬编码完整风险等级表；
4. 定义 docx 底层渲染逻辑；
5. 承担 RDB 文件解析；
6. 承担 key 数量统计；
7. 承担 SHA256 计算；
8. 承担 JSON schema 校验；
9. 承担加总一致性校验；
10. 代替 tools 进行 docx 渲染。

---

## 七、Skill Script 要求

### 7.1 主入口脚本

本阶段只暴露一个主要执行入口：

```text
skills/redis-rdb-analysis/scripts/analyze_local_rdb.py
```

### 7.2 调用接口

脚本必须支持：

```bash
python skills/redis-rdb-analysis/scripts/analyze_local_rdb.py \
  --rdb /tmp/dump.rdb \
  --output-dir /tmp/axe_rdb_assistant/<run_id> \
  --profile default
```

### 7.3 参数要求

| 参数 | 必需 | 说明 |
|---|---:|---|
| `--rdb` | 是 | 本地 RDB 文件绝对路径 |
| `--output-dir` | 是 | 本次运行产物目录 |
| `--profile` | 否 | 默认 `default` |
| `--language` | 否 | 默认由 profile 决定 |
| `--top-n` | 否 | 默认由 profile 决定 |

### 7.4 脚本职责

`analyze_local_rdb.py` 负责：

1. 解析命令行参数；
2. 检查 RDB 文件是否存在；
3. 计算 RDB 文件 SHA256；
4. 调用本地 RDB 解析能力；
5. 生成基础统计；
6. 读取 references；
7. 读取 profile；
8. 生成 `result.json`；
9. 生成 `summary.txt`；
10. 调用 `tools/validation/validate_result.py`；
11. 调用 `tools/docx_renderer/render_docx.py`；
12. 生成最小 `report.docx`；
13. 返回明确退出码。

### 7.5 脚本禁止行为

`analyze_local_rdb.py` 不得：

1. 解析自然语言；
2. 判断用户真实意图；
3. 自行扩展到远程 Redis；
4. 自行 SSH 登录服务器；
5. 自行触发 `BGSAVE`；
6. 自行写死复杂业务流程；
7. 伪造 RDB 分析结果；
8. 失败时返回成功；
9. 把未实现能力包装成已实现能力。

---

## 八、Tools 要求

### 8.1 `tools/docx_renderer/`

#### 8.1.1 定位

`tools/docx_renderer/` 是通用 docx 渲染能力，不属于 Redis RDB 专属逻辑。

它可以被未来多个 Skill 复用，例如：

1. Redis RDB 分析；
2. Redis 巡检；
3. MySQL 慢 SQL 分析；
4. MongoDB 诊断；
5. Kafka 巡检；
6. ES 日志分析。

#### 8.1.2 输入

最小输入：

```json
{
  "result_json": "/tmp/axe_rdb_assistant/<run_id>/result.json",
  "template": "skills/redis-rdb-analysis/assets/docx_templates/minimal_report_template.docx",
  "outline": "skills/redis-rdb-analysis/assets/report_outline.yaml",
  "output": "/tmp/axe_rdb_assistant/<run_id>/report.docx"
}
```

#### 8.1.3 输出

```text
/tmp/axe_rdb_assistant/<run_id>/report.docx
```

#### 8.1.4 职责

`tools/docx_renderer/` 负责：

1. 打开 docx 模板；
2. 按 outline 写入标题、段落、表格；
3. 写入基础元数据；
4. 写入 RDB 分析摘要；
5. 写入验证结果；
6. 写入不确定项；
7. 保存 docx 文件。

#### 8.1.5 禁止

`tools/docx_renderer/` 不得：

1. 判断 Redis 风险；
2. 计算 Redis 指标；
3. 读取 RDB 文件；
4. 生成无来源结论；
5. 决定用户是否需要 docx。

---

### 8.2 `tools/validation/`

#### 8.2.1 定位

`tools/validation/` 是通用验证能力，用于执行跨 Skill 可复用的机械验证和逻辑验证。

#### 8.2.2 最小验证项

Phase-01 至少实现：

| 验证项 | 类型 | 说明 |
|---|---|---|
| JSON 可解析 | mechanical | `result.json` 必须是合法 JSON |
| 必填字段存在 | mechanical | 必须包含 status、input、summary、validation |
| status 合法 | mechanical | 只能是 success / partial / failed |
| source 字段检查 | mechanical | 关键结论必须携带 source |
| key 加总一致性 | logical | 如存在类型分布，则 key 总数应等于类型分布加总 |
| 错误状态一致性 | logical | failed 状态必须有 errors |
| 不确定项一致性 | logical | insufficient 状态必须说明原因 |

#### 8.2.3 输入

```json
{
  "result_json": "/tmp/axe_rdb_assistant/<run_id>/result.json"
}
```

#### 8.2.4 输出

验证结果应写回或附加到 `result.json` 的 `validation` 字段。

#### 8.2.5 禁止

`tools/validation/` 不得：

1. 定义 Redis Big Key 阈值；
2. 定义 Redis 风险等级；
3. 判断业务建议是否合理；
4. 代替 LLM 做充分性表达；
5. 把失败验证强行改成成功。

---

## 九、References 要求

### 9.1 Redis Big Key 阈值

文件：

```text
skills/redis-rdb-analysis/references/redis_bigkey_thresholds.yaml
```

Phase-01 可采用最小内容：

```yaml
version: phase-01
enabled: false
note: "Phase-01 does not implement full Big Key analysis. Threshold definitions are placeholders for later phases."
```

如实现基础 Big Key 识别，必须明确字段来源和阈值来源。

### 9.2 Redis 风险等级

文件：

```text
skills/redis-rdb-analysis/references/redis_risk_levels.yaml
```

Phase-01 可采用最小内容：

```yaml
version: phase-01
levels:
  info:
    description: "Informational finding"
  warning:
    description: "Potential risk requiring review"
  critical:
    description: "High risk requiring action"
```

### 9.3 Redis 建议库

文件：

```text
skills/redis-rdb-analysis/references/redis_recommendations.yaml
```

Phase-01 可包含少量候选建议，但不得在无证据时输出确定性建议。

### 9.4 Profiles

目录：

```text
skills/redis-rdb-analysis/references/profiles/
```

最少包含：

```text
default.yaml
rcs.yaml
concise.yaml
```

#### `default.yaml`

```yaml
version: phase-01
language: zh
output:
  summary: true
  json: true
  docx: true
analysis:
  local_rdb_only: true
  top_n: 20
```

#### `rcs.yaml`

```yaml
version: phase-01
language: zh
output:
  summary: true
  json: true
  docx: true
analysis:
  local_rdb_only: true
  top_n: 100
style:
  formal: true
  include_evidence: true
```

#### `concise.yaml`

```yaml
version: phase-01
language: zh
output:
  summary: true
  json: true
  docx: true
analysis:
  local_rdb_only: true
  top_n: 10
style:
  concise: true
```

---

## 十、Assets 要求

### 10.1 报告模板

必须提供：

```text
skills/redis-rdb-analysis/assets/docx_templates/minimal_report_template.docx
```

Phase-01 模板只要求最小可用，不要求复杂版式。

### 10.2 报告大纲

必须提供：

```text
skills/redis-rdb-analysis/assets/report_outline.yaml
```

建议内容：

```yaml
version: phase-01
sections:
  - id: cover
    title: "Redis RDB 分析报告"
  - id: object
    title: "一、分析对象"
  - id: summary
    title: "二、基础统计"
  - id: findings
    title: "三、主要发现"
  - id: validation
    title: "四、验证结果"
  - id: uncertainties
    title: "五、不确定项与限制"
```

### 10.3 Phase-01 docx 最小内容

`report.docx` 至少包含：

1. 标题：Redis RDB 分析报告；
2. 分析时间；
3. RDB 文件路径；
4. RDB SHA256；
5. 分析状态；
6. DB 数量；
7. Key 总数；
8. 类型分布；
9. TTL 概况；
10. 验证结果；
11. 不确定项；
12. 本阶段限制。

---

## 十一、输出规范

### 11.1 归档目录

Phase-01 每次运行产物必须写入：

```text
/tmp/axe_rdb_assistant/<run_id>/
```

最小结构：

```text
/tmp/axe_rdb_assistant/<run_id>/
├── result.json
├── summary.txt
├── report.docx
└── input/
    ├── user_request.txt
    └── rdb.fingerprint
```

完整审计目录进入后续 Phase，不在 Phase-01 强制实现。

### 11.2 `result.json` 最小 schema

```json
{
  "status": "success | partial | failed",
  "run": {
    "run_id": "string",
    "started_at": "string",
    "finished_at": "string"
  },
  "input": {
    "rdb_path": "string",
    "sha256": "string",
    "source": "input.rdb_path"
  },
  "profile": {
    "name": "default",
    "source": "references.profiles.default"
  },
  "summary": {
    "db_count": 0,
    "total_keys": 0,
    "type_distribution": {},
    "ttl": {
      "keys_with_ttl": 0,
      "keys_without_ttl": 0
    },
    "source": "analysis.rdb_parser"
  },
  "findings": [],
  "validation": {
    "mechanical": {
      "status": "pass | fail",
      "details": []
    },
    "logical": {
      "status": "pass | fail | skipped",
      "details": []
    },
    "sufficiency": {
      "status": "sufficient | insufficient",
      "details": []
    }
  },
  "outputs": {
    "summary_txt": "string",
    "result_json": "string",
    "report_docx": "string"
  },
  "uncertainties": [],
  "errors": []
}
```

### 11.3 `summary.txt` 最小结构

```text
一、分析对象
- RDB 文件：
- SHA256：
- 分析状态：

二、基础统计
- DB 数量：
- Key 总数：
- 类型分布：
- TTL 概况：

三、验证结果
- 机械验证：
- 逻辑验证：
- 充分性验证：

四、输出文件
- JSON：
- DOCX：

五、不确定项与限制
- 不确定项：
- Phase-01 限制：
```

### 11.4 `report.docx` 最小结构

同第 10.3 节。

---

## 十二、验证要求

### 12.1 机械验证

由 `tools/validation/` 执行。

必须验证：

1. RDB 文件存在；
2. RDB 文件可读；
3. SHA256 成功生成；
4. RDB 解析命令成功执行或明确失败；
5. `result.json` 成功生成；
6. `summary.txt` 成功生成；
7. `report.docx` 成功生成；
8. 输出文件路径存在。

### 12.2 逻辑验证

由 `tools/validation/` 与 `analyze_local_rdb.py` 配合完成。

必须验证：

1. `total_keys` 与 `type_distribution` 加总一致；
2. TTL 统计不出现负数；
3. `status=failed` 时必须存在 `errors`；
4. `status=success` 时不应存在 fatal error；
5. 关键 findings 必须带 source。

### 12.3 充分性验证

由 LLM 基于 `SKILL.md` 和 `result.json` 完成。

Phase-01 的充分性判断标准：

| 状态 | 含义 |
|---|---|
| `sufficient` | 本地 RDB 文件已解析，基础统计、验证结果、三种输出均生成 |
| `insufficient` | RDB 缺失、解析失败、结果不完整、验证失败、输出缺失或用户问题超出 Phase-01 能力 |

LLM 必须明确说明：

1. 哪些问题已经回答；
2. 哪些问题只是基础判断；
3. 哪些问题本阶段不能回答；
4. 哪些信息不足。

---

## 十三、测试要求

### 13.1 最小测试文件

必须提供：

```text
tests/test_result_schema.py
tests/test_validation.py
tests/test_docx_renderer.py
```

### 13.2 测试内容

#### `test_result_schema.py`

至少验证：

1. `status` 字段存在；
2. `input.rdb_path` 字段存在；
3. `input.sha256` 字段存在；
4. `summary.total_keys` 字段存在；
5. `summary.type_distribution` 字段存在；
6. `validation` 字段存在；
7. `outputs.report_docx` 字段存在；
8. `errors` 字段存在；
9. `uncertainties` 字段存在。

#### `test_validation.py`

至少验证：

1. 合法 JSON 通过；
2. 缺必填字段失败；
3. 非法 status 失败；
4. source 缺失失败或 warning；
5. key 加总不一致失败；
6. failed 状态无 errors 失败。

#### `test_docx_renderer.py`

至少验证：

1. 输入 result.json 后能生成 docx；
2. docx 文件存在；
3. docx 文件大小大于 0；
4. 缺模板时返回失败；
5. 缺 result.json 时返回失败。

---

## 十四、README 最小要求

Phase-01 必须更新根目录 `README.md`，至少包含：

1. 项目简介；
2. Phase-01 支持范围；
3. 不支持范围；
4. 目录结构说明；
5. 环境准备；
6. 如何配置 axe agent；
7. 如何运行本地 RDB 分析；
8. 输出文件说明；
9. 常见失败原因；
10. 后续 phase 计划。

---

## 十五、示例请求

必须提供：

```text
examples/requests/local_rdb_default_zh.txt
```

内容示例：

```text
请分析本地 RDB 文件 /tmp/dump.rdb，按照默认 profile 输出摘要、JSON 和 docx 报告。
```

可选示例：

```text
请分析 /tmp/dump.rdb，按照 rcs profile 输出正式报告。
```

---

## 十六、验收标准

### 16.1 目录验收

- [ ] 存在 `agents/redis/redis-rdb-assistant.toml`
- [ ] 存在 `skills/redis-rdb-analysis/SKILL.md`
- [ ] 存在 `skills/redis-rdb-analysis/scripts/analyze_local_rdb.py`
- [ ] 存在 `skills/redis-rdb-analysis/references/redis_bigkey_thresholds.yaml`
- [ ] 存在 `skills/redis-rdb-analysis/references/redis_risk_levels.yaml`
- [ ] 存在 `skills/redis-rdb-analysis/references/redis_recommendations.yaml`
- [ ] 存在 `skills/redis-rdb-analysis/references/profiles/default.yaml`
- [ ] 存在 `skills/redis-rdb-analysis/assets/report_outline.yaml`
- [ ] 存在 `tools/docx_renderer/render_docx.py`
- [ ] 存在 `tools/validation/validate_result.py`
- [ ] 不存在 `src/`
- [ ] 不存在根目录 `scripts/`

### 16.2 Skill 验收

- [ ] SKILL.md 明确支持本地 RDB 分析；
- [ ] SKILL.md 明确不支持远程 Redis；
- [ ] SKILL.md 明确不支持 SSH 拉取；
- [ ] SKILL.md 明确不支持 MySQL staging；
- [ ] SKILL.md 明确 script 调用方式；
- [ ] SKILL.md 明确 references / profiles / assets 的使用方式；
- [ ] SKILL.md 明确 source 要求；
- [ ] SKILL.md 明确失败处理；
- [ ] SKILL.md 不包含可执行代码；
- [ ] SKILL.md 不硬编码阈值。

### 16.3 功能验收

- [ ] axe agent 能启动；
- [ ] LLM 能识别本地 RDB 分析请求；
- [ ] 能识别 RDB 文件路径；
- [ ] 能调用 `analyze_local_rdb.py`；
- [ ] 能生成 `result.json`；
- [ ] 能生成 `summary.txt`；
- [ ] 能生成 `report.docx`；
- [ ] `result.json` 包含最小 schema；
- [ ] `summary.txt` 可读；
- [ ] `report.docx` 可打开；
- [ ] 失败路径不会返回 success。

### 16.4 验证验收

- [ ] 机械验证结果写入 `result.json`；
- [ ] 逻辑验证结果写入 `result.json`；
- [ ] 充分性验证由 LLM 输出说明；
- [ ] key 加总不一致时能标识失败或 partial；
- [ ] 缺 source 时能标识 warning 或 failure；
- [ ] RDB 文件不存在时 status 为 failed；
- [ ] docx 渲染失败时 status 不得为 success。

### 16.5 边界验收

- [ ] 未 patch axe；
- [ ] 未封装 axe；
- [ ] 未引入 MCP；
- [ ] 未引入 sub-agent；
- [ ] 未引入 memory；
- [ ] 未引入远程 Redis；
- [ ] 未实现 SSH；
- [ ] 未实现 MySQL staging；
- [ ] 未引入 `src/`；
- [ ] 未创建根目录 `scripts/`；
- [ ] 未搬运旧 DBA Assistant 目录结构。

---

## 十七、建议实现顺序

### Step 1：创建目录结构

先创建目录，不写复杂逻辑。

### Step 2：编写 `SKILL.md`

优先写 Skill，确保 LLM 行为边界明确。

### Step 3：编写 references / profiles

创建最小阈值、风险等级、建议库和 profiles。

### Step 4：编写 assets

创建 `report_outline.yaml` 和最小 docx 模板。

### Step 5：编写 tools

先实现：

1. `tools/validation/validate_result.py`
2. `tools/docx_renderer/render_docx.py`

### Step 6：编写 Skill script

实现：

```text
skills/redis-rdb-analysis/scripts/analyze_local_rdb.py
```

该脚本内部调用 tools。

### Step 7：编写 agent TOML

配置：

```text
agents/redis/redis-rdb-assistant.toml
```

确保 agent 能使用 Redis RDB Analysis Skill 和 run_command。

### Step 8：编写测试

补充最小 tests。

### Step 9：本地跑通

使用一个本地 RDB 文件完成端到端测试。

### Step 10：生成 review / closeout

填写：

```text
docs/reviews/phase-01-review.md
docs/reviews/phase-01-closeout.md
```

---

## 十八、Phase-01 Review 模板

文件：

```text
docs/reviews/phase-01-review.md
```

内容：

```markdown
# Phase-01 Review

## 1. Review Summary

## 2. Delivered Artifacts

## 3. Skill First Assessment

## 4. Directory Boundary Assessment

## 5. Execution Flow Assessment

## 6. Output Assessment

## 7. Validation Assessment

## 8. Known Issues

## 9. Scope Creep Check

## 10. Recommendations for Phase-02
```

---

## 十九、Phase-01 Closeout 模板

文件：

```text
docs/reviews/phase-01-closeout.md
```

内容：

```markdown
# Phase-01 Closeout

## 1. Completion Summary

## 2. Final Status

## 3. Commands Executed

## 4. Sample Request

## 5. Sample Output Directory

## 6. Generated Artifacts

## 7. Validation Results

## 8. Failed / Partial Cases

## 9. Deferred Items

## 10. Risks for Phase-02

## 11. Decision Log Updates

## 12. Go / No-Go Recommendation
```

---

## 二十、进入 Phase-02 的条件

只有满足以下条件，才能进入 Phase-02：

1. 本地 RDB 文件端到端跑通；
2. `SKILL.md` 已完成并被 agent 使用；
3. `analyze_local_rdb.py` 能生成三种输出；
4. `tools/docx_renderer/` 能生成最小 docx；
5. `tools/validation/` 能写入验证结果；
6. `result.json` schema 稳定；
7. `summary.txt` 可读；
8. `report.docx` 可打开；
9. 失败路径不伪装成功；
10. `docs/reviews/phase-01-review.md` 已完成；
11. `docs/reviews/phase-01-closeout.md` 已完成。

---

## 二十一、Phase-02 Deferred Items

以下内容默认进入 Phase-02 或后续阶段，不得在 Phase-01 扩展：

1. 更完整 JSON schema；
2. 更完整 docx 正式报告；
3. 更复杂章节样式；
4. 更完整 Big Key 分析；
5. 更完整 TTL 分析；
6. 更完整风险等级体系；
7. 更完整建议库；
8. 完整审计目录；
9. axe `--verbose` / `--json` 轨迹归档；
10. 多次运行可复现性对比。

---

## 二十二、给 Codex 的执行提示词

```text
你现在在 axe-dba-assistant 项目中工作，请严格执行 Phase-01 SPEC：

docs/phases/phase-01-local-rdb-skill-first-mvp.md

目标：
基于 axe 实现 Redis RDB 本地文件分析的最小 MVP，重点是 Skill First。

必须遵守：

1. 先写 SKILL.md，再写执行脚本。
2. Redis RDB 专属动作放在 skills/redis-rdb-analysis/scripts/analyze_local_rdb.py。
3. 通用 docx 渲染放在 tools/docx_renderer/。
4. 通用验证放在 tools/validation/。
5. references、profiles、assets 都放在 redis-rdb-analysis Skill 能力包内。
6. Phase-01 不创建 src/。
7. Phase-01 不创建根目录 scripts/。
8. Phase-01 不引入 MCP。
9. Phase-01 不引入 sub-agent。
10. Phase-01 不 patch axe，不封装 axe。
11. Phase-01 不做远程 Redis、SSH、MySQL staging、多 RDB。
12. 必须生成 summary.txt、result.json、report.docx。
13. 失败时不得返回 success。
14. 所有结论性字段必须有 source 或明确标识为 uncertainty。
15. 完成后补充 tests、README、phase-01-review.md、phase-01-closeout.md。

建议执行顺序：

1. 创建目录结构；
2. 编写 SKILL.md；
3. 编写 references / profiles；
4. 编写 assets/report_outline.yaml；
5. 编写 tools/validation；
6. 编写 tools/docx_renderer；
7. 编写 analyze_local_rdb.py；
8. 编写 agent TOML；
9. 编写 tests；
10. 使用本地 RDB 文件跑通；
11. 修复失败路径；
12. 输出 phase review 和 closeout。
```
