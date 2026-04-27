# Phase-01 SPEC: Local RDB Skill-First MVP

> Project: axe-dba-assistant  
> Phase: Phase-01  
> Status: planning  
> Scope: Local Redis RDB analysis MVP  
> Main SPEC: axe Redis RDB Assistant Main SPEC v2.1  
> Phase SPEC Path: `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-01-local-rdb-skill-first-mvp.md`

---

## 1. Phase Positioning

Phase-01 is the minimum viable phase for the axe-based Redis RDB analysis assistant.

The purpose of this phase is not to build a full DBA assistant. The purpose is to validate the smallest working loop:

1. axe can start the Redis RDB assistant agent;
2. the agent can load the Redis RDB analysis Skill;
3. the Skill can guide the LLM to recognize a local RDB analysis request;
4. the LLM can call the Skill-owned analysis script through axe runtime capabilities;
5. the script can analyze a local RDB file and generate minimal outputs;
6. the assistant can return a reliable summary to the user;
7. the repository structure remains Skill-first and does not regress into a traditional Python CLI project.

The primary focus of this phase is **Skill-first execution**.

---

## 2. Phase Goals

### 2.1 Functional Goals

Phase-01 must support one core scenario:

```bash
axe run --agents-dir agents/redis redis-rdb-assistant \
  -p "Please analyze the local Redis RDB file /tmp/dump.rdb and generate summary, JSON, and docx outputs."
```

The assistant must be able to:

1. recognize that the user is asking for Redis RDB analysis;
2. extract the local RDB file path from the natural-language request;
3. verify that the input file exists;
4. compute the file fingerprint;
5. run local RDB analysis;
6. generate a minimal terminal summary;
7. generate a structured `result.json`;
8. generate a minimal `report.docx`;
9. mark failed or partial analysis explicitly;
10. avoid unsupported behaviors such as remote Redis access, SSH fetching, MySQL staging, or multi-RDB aggregation.

### 2.2 Architecture Goals

Phase-01 must establish a clear boundary between Skill, Skill scripts, references, assets, and reusable tools.

| Area | Phase-01 Responsibility |
|---|---|
| `SKILL.md` | LLM-facing task guide, behavior rules, boundaries, script usage rules |
| `skills/redis-rdb-analysis/scripts/` | Redis RDB-specific deterministic execution actions |
| `skills/redis-rdb-analysis/references/` | Redis RDB thresholds, risk levels, recommendations, profiles |
| `skills/redis-rdb-analysis/assets/` | Redis RDB report templates and report-specific assets |
| `tools/docx_renderer/` | Reusable docx rendering capability |
| `tools/validation/` | Reusable validation capability |
| `agents/redis/` | axe agent configuration |

Phase-01 must not introduce `src/`.

---

## 3. Non-Goals

Phase-01 explicitly does not include:

1. remote Redis connection;
2. SSH-based RDB discovery or fetching;
3. triggering `BGSAVE` on a remote Redis instance;
4. MySQL-backed staging;
5. multi-RDB aggregation;
6. cross-run trend comparison;
7. Web UI or API;
8. MCP integration;
9. sub-agent orchestration;
10. patching or wrapping axe itself;
11. complex docx layout;
12. full Redis risk knowledge base;
13. automatic axe vs DeepAgents comparison;
14. a traditional `main.py`, `cli.py`, or standalone Python application entrypoint;
15. a project-level root `scripts/` directory.

Anything outside this list should be deferred unless it is required to complete the local RDB MVP.

---

## 4. Required Repository Structure

Phase-01 should use the following structure:

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
│   └── outputs/
├── tests/
└── docs/
    ├── phases/
    ├── reviews/
    └── decisions/
```

### 4.1 Prohibited Phase-01 Directories

The following directories should not be introduced in Phase-01:

```text
src/
scripts/
```

Rationale:

- `src/` is unnecessary for the MVP and may create ambiguity with Skill scripts;
- root-level `scripts/` may create a second workflow entrypoint;
- Phase-01 must keep the execution path simple and Skill-centered.

---

## 5. Execution Flow

Phase-01 execution flow must be:

```text
User request
  ↓
axe agent
  ↓
agents/redis/redis-rdb-assistant.toml
  ↓
skills/redis-rdb-analysis/SKILL.md
  ↓
LLM recognizes local RDB analysis intent
  ↓
LLM calls skills/redis-rdb-analysis/scripts/analyze_local_rdb.py
  ↓
analyze_local_rdb.py performs Redis RDB-specific deterministic actions
  ↓
analyze_local_rdb.py calls tools/validation when needed
  ↓
analyze_local_rdb.py calls tools/docx_renderer when needed
  ↓
Outputs are written to the run directory
  ↓
LLM reads result.json / summary.txt
  ↓
LLM responds to the user according to SKILL.md
```

The LLM should directly call only the Redis RDB Skill script in Phase-01. It should not directly orchestrate multiple tools such as validation and docx rendering.

---

## 6. Skill Requirements

The file below is mandatory:

```text
skills/redis-rdb-analysis/SKILL.md
```

The Skill must include at least the following sections:

1. Task Definition;
2. Supported Inputs;
3. Intent Recognition Rules;
4. Local RDB Analysis Flow;
5. Script Usage Rules;
6. Output Requirements;
7. Evidence and Source Requirements;
8. Validation Requirements;
9. Uncertainty Handling;
10. Forbidden Behaviors.

### 6.1 What the Skill Should Do

`SKILL.md` should guide the LLM to:

1. identify Redis RDB analysis requests;
2. identify local file paths;
3. ask for missing required input if no local RDB file path is provided;
4. call `skills/redis-rdb-analysis/scripts/analyze_local_rdb.py` when local analysis is possible;
5. interpret `result.json` and `summary.txt`;
6. distinguish verified facts, inferences, risks, and uncertainties;
7. avoid claiming unsupported capabilities;
8. avoid fabricating key names, statistics, or risks.

### 6.2 What the Skill Must Not Do

`SKILL.md` must not contain:

1. executable Python code;
2. shell scripts;
3. hard-coded threshold values;
4. docx rendering implementation;
5. RDB parsing implementation;
6. model-provider-specific assumptions;
7. remote Redis workflow details;
8. MySQL staging workflow details.

---

## 7. Skill Script Requirements

The main execution script is:

```text
skills/redis-rdb-analysis/scripts/analyze_local_rdb.py
```

It is the only direct executable entrypoint exposed by the Redis RDB analysis Skill in Phase-01.

### 7.1 Responsibilities

The script is responsible for:

1. parsing command-line arguments;
2. validating the local RDB file path;
3. computing SHA256 fingerprint;
4. invoking the local RDB parsing mechanism;
5. generating minimal Redis RDB statistics;
6. reading Redis RDB-specific references and profiles;
7. producing `result.json`;
8. producing `summary.txt`;
9. calling `tools/validation/` for reusable validation checks;
10. calling `tools/docx_renderer/` for minimal docx rendering;
11. writing all outputs to the run output directory;
12. returning clear success or failure exit codes.

### 7.2 Responsibilities That Must Stay Out of the Script

The script must not:

1. parse natural language user intent;
2. decide whether the request is a Redis RDB analysis request;
3. implement remote Redis collection;
4. implement SSH operations;
5. implement MySQL staging;
6. hide partial or failed analysis;
7. fabricate missing data;
8. become a general-purpose DBA workflow engine.

---

## 8. Tools Boundary

Phase-01 may include two reusable tool areas:

```text
tools/docx_renderer/
tools/validation/
```

### 8.1 `tools/docx_renderer/`

This tool area provides reusable docx rendering capability.

It may handle:

1. opening a docx template;
2. writing headings;
3. writing paragraphs;
4. writing tables;
5. applying basic style rules;
6. saving the final docx file.

It must not define Redis RDB business logic.

Redis RDB report structure, report sections, and templates must remain under:

```text
skills/redis-rdb-analysis/assets/
```

### 8.2 `tools/validation/`

This tool area provides reusable validation capability.

It may handle:

1. required-field validation;
2. JSON schema validation;
3. source-field validation;
4. status model validation;
5. generic sum-consistency validation;
6. generation of a standard validation block.

It must not define Redis-specific risk rules.

Redis-specific validation rules and thresholds must remain in:

```text
skills/redis-rdb-analysis/references/
skills/redis-rdb-analysis/scripts/analyze_local_rdb.py
skills/redis-rdb-analysis/SKILL.md
```

---

## 9. References, Profiles, and Assets

### 9.1 References

Required Redis RDB references:

```text
skills/redis-rdb-analysis/references/redis_bigkey_thresholds.yaml
skills/redis-rdb-analysis/references/redis_risk_levels.yaml
skills/redis-rdb-analysis/references/redis_recommendations.yaml
```

These files contain Redis RDB-specific rules and knowledge.

### 9.2 Profiles

Profiles are stored under references:

```text
skills/redis-rdb-analysis/references/profiles/default.yaml
skills/redis-rdb-analysis/references/profiles/rcs.yaml
skills/redis-rdb-analysis/references/profiles/concise.yaml
```

Profiles describe request-level preferences such as language, report detail level, and analysis scope.

### 9.3 Assets

Required asset location:

```text
skills/redis-rdb-analysis/assets/docx_templates/minimal_report_template.docx
```

Assets may define report templates, section layout, and style constraints.

The rendering engine must remain in `tools/docx_renderer/`.

---

## 10. Minimal Outputs

Each successful Phase-01 run must generate at least:

```text
summary.txt
result.json
report.docx
```

### 10.1 Minimal Run Directory

The output directory should follow this structure:

```text
/tmp/axe_rdb_assistant/<run_id>/
├── summary.txt
├── result.json
├── report.docx
└── input/
    ├── user_request.txt
    └── rdb.fingerprint
```

Full audit files such as `stdout.log`, `stderr.log`, and `trace.json` may be deferred to a later phase.

---

## 11. Minimal `result.json` Contract

`result.json` must contain at least:

```json
{
  "status": "success | partial | failed",
  "input": {
    "rdb_path": "/tmp/dump.rdb",
    "sha256": "...",
    "source": "input.rdb_path"
  },
  "summary": {
    "total_keys": 0,
    "db_count": 0,
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
  "uncertainties": [],
  "errors": []
}
```

Every conclusion-like field must either include a `source` or be explicitly marked as inference or uncertainty.

---

## 12. Minimal Summary Requirements

`summary.txt` must include:

```text
1. Analysis Target
- RDB file:
- SHA256:
- Analysis status:

2. Basic Statistics
- DB count:
- Total keys:
- Type distribution:
- TTL overview:

3. Validation Result
- Mechanical validation:
- Logical validation:
- Sufficiency validation:

4. Risks and Uncertainties
- Findings:
- Uncertainties:
- Deferred items:
```

The terminal response may summarize this file, but should not contradict it.

---

## 13. Minimal Docx Requirements

`report.docx` is required in Phase-01.

The docx report may be minimal. It does not need complex layout, but must contain:

1. report title;
2. analysis time;
3. RDB file path;
4. SHA256 fingerprint;
5. basic statistics;
6. validation results;
7. risks and uncertainties;
8. explicit statement of Phase-01 limitations.

Complex formatting, advanced tables, cover pages, and final delivery-grade styling are deferred to later phases.

---

## 14. Validation Requirements

Phase-01 must implement the three-layer validation model at a minimal level.

| Validation Layer | Phase-01 Requirement | Owner |
|---|---|---|
| Mechanical validation | File exists, parser runs, outputs are generated, exit code is captured | Skill script + tools/validation |
| Logical validation | Basic consistency checks such as key totals and type totals if available | Skill script + tools/validation |
| Sufficiency validation | Whether available data is enough to answer the user request | LLM guided by SKILL.md |

If any validation cannot be completed, the reason must be written to `result.json` and `summary.txt`.

---

## 15. axe Environment Requirement

The local machine must have axe installed before Phase-01 can be fully verified.

The following command must work:

```bash
axe version
```

Without axe, developers may still write files and unit tests, but they cannot validate the real agent → Skill → script execution path.

---

## 16. No `main.py` Rule

Phase-01 must not introduce a traditional Python entrypoint such as:

```text
main.py
cli.py
app.py
```

The project entrypoint is the axe agent:

```bash
axe run --agents-dir agents/redis redis-rdb-assistant -p "..."
```

The Skill execution entrypoint is:

```text
skills/redis-rdb-analysis/scripts/analyze_local_rdb.py
```

This rule prevents the project from becoming a traditional CLI project and keeps the architecture Skill-first.

---

## 17. Tests

Phase-01 should include minimal tests for:

1. required `result.json` fields;
2. status model validity;
3. source-field presence;
4. failed file path handling;
5. minimal docx generation;
6. validation block generation.

Tests should not require remote Redis, SSH, MySQL, MCP, or sub-agents.

---

## 18. Acceptance Criteria

Phase-01 is accepted only if all of the following are true:

### 18.1 Structure Acceptance

- [ ] `agents/redis/redis-rdb-assistant.toml` exists;
- [ ] `skills/redis-rdb-analysis/SKILL.md` exists;
- [ ] `skills/redis-rdb-analysis/scripts/analyze_local_rdb.py` exists;
- [ ] `skills/redis-rdb-analysis/references/` exists;
- [ ] `skills/redis-rdb-analysis/assets/` exists;
- [ ] `tools/docx_renderer/` exists;
- [ ] `tools/validation/` exists;
- [ ] `src/` does not exist;
- [ ] root-level `scripts/` does not exist.

### 18.2 Functional Acceptance

- [ ] axe can start the Redis RDB assistant agent;
- [ ] the Skill can be loaded;
- [ ] a natural-language local RDB request can be recognized;
- [ ] the local RDB file path can be extracted;
- [ ] `analyze_local_rdb.py` can be called;
- [ ] `summary.txt` is generated;
- [ ] `result.json` is generated;
- [ ] `report.docx` is generated;
- [ ] failure cases are not reported as success;
- [ ] unsupported scope is explicitly marked.

### 18.3 Boundary Acceptance

- [ ] no axe patch;
- [ ] no axe wrapper;
- [ ] no MCP;
- [ ] no sub-agent;
- [ ] no remote Redis workflow;
- [ ] no SSH workflow;
- [ ] no MySQL staging;
- [ ] no `main.py`;
- [ ] no `src/`;
- [ ] no root-level `scripts/`.

---

## 19. Phase-01 Deliverables

The phase must deliver:

1. axe agent configuration;
2. Redis RDB analysis Skill;
3. Redis RDB local analysis script;
4. Redis RDB references and profiles;
5. minimal docx template;
6. reusable docx renderer tool;
7. reusable validation tool;
8. minimal JSON output;
9. minimal summary output;
10. minimal docx report;
11. test cases;
12. Phase-01 review document;
13. Phase-01 closeout document.

---

## 20. Deferred Items

The following items are deferred to later phases:

1. full audit directory;
2. axe `--verbose` and `--json` trace archival;
3. complete docx styling;
4. richer Big Key analysis;
5. deeper TTL analysis;
6. multi-RDB support;
7. remote Redis support;
8. SSH RDB fetching;
9. MySQL staging;
10. cross-run comparison;
11. final axe vs DeepAgents comparison.

---

## 21. Phase-01 Closeout Requirements

Before marking Phase-01 as finished, create:

```text
docs/reviews/phase-01-review.md
docs/reviews/phase-01-closeout.md
```

The review must answer:

1. Did the Skill guide the execution path?
2. Did the project avoid `src/` and root-level `scripts/`?
3. Did the Skill script remain the only direct execution entrypoint?
4. Did reusable docx and validation capabilities stay under `tools/`?
5. Did Redis RDB-specific logic stay under the Redis RDB Skill?
6. Were the three required outputs generated?
7. Were failure and partial states handled correctly?
8. What must be fixed in Phase-02?
