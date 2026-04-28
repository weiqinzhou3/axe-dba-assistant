# Phase-02 SPEC: Output Contract and Three-Layer Validation Hardening

> Project: axe-dba-assistant  
> Phase: Phase-02  
> Status: finished  
> Scope: Output contract, validation semantics, and failure-state hardening  
> Main SPEC: axe Redis RDB Assistant Main SPEC v2.1  
> Previous Phase: Phase-01 Local RDB Skill-First MVP  
> Phase SPEC Path: `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-02-output-validation-hardening.md`

---

## 1. Phase Positioning

Phase-02 starts after Phase-01 has proven the local RDB Skill-first execution loop.

Phase-01 proved that:

1. the axe agent can load the Redis RDB Skill;
2. the LLM can call the Skill-owned local RDB analysis script;
3. the script can invoke the required HDT `rdb` parser from `PATH`;
4. the system can generate `summary.txt`, `result.json`, and `report.docx`;
5. the project can keep Redis-specific execution under the Skill package while keeping reusable docx and validation utilities under `tools/`.

Phase-02 does not expand runtime scope. It hardens output quality and validation correctness.

The goal is to make outputs stable, reviewable, and suitable as the baseline for later audit, reporting, and comparison phases.

---

## 2. Phase Goals

### 2.1 Functional Goals

Phase-02 must harden:

1. `result.json` schema and field semantics;
2. `summary.txt` structure and consistency with `result.json`;
3. minimal `report.docx` content completeness;
4. success / partial / failed status semantics;
5. three-layer validation behavior;
6. source traceability for conclusion-like fields;
7. parser metadata fields;
8. failure output behavior.

### 2.2 Architecture Goals

Phase-02 must preserve the Phase-01 architecture:

| Area | Responsibility |
|---|---|
| `SKILL.md` | LLM-facing execution and interpretation rules |
| `skills/redis-rdb-analysis/scripts/analyze_local_rdb.py` | Redis RDB-specific deterministic execution |
| `tools/validation/` | Reusable validation helpers |
| `tools/docx_renderer/` | Reusable docx rendering helper |
| `skills/redis-rdb-analysis/references/` | Redis-specific thresholds, profiles, and recommendation references |
| `skills/redis-rdb-analysis/assets/` | Redis-specific report templates and report assets |

Phase-02 must not introduce `src/`, root-level `scripts/`, MCP, sub-agents, remote Redis, SSH fetching, or MySQL staging.

---

## 3. Non-Goals

Phase-02 explicitly does not include:

1. remote Redis access;
2. SSH RDB discovery or fetching;
3. triggering `BGSAVE`;
4. MySQL-backed staging;
5. multi-RDB aggregation;
6. cross-run comparison;
7. full audit trace archival;
8. production-grade docx styling;
9. advanced Big Key analysis;
10. full Redis risk knowledge base;
11. automatic axe vs DeepAgents comparison;
12. web UI or API.

Those items remain deferred to later phases.

---

## 4. Output Contract Hardening

### 4.1 Required `result.json` Top-Level Fields

`result.json` must include at least the following stable top-level fields:

```json
{
  "schema_version": "phase-02.v1",
  "status": "success | partial | failed",
  "generated_at": "...",
  "parser_required": true,
  "parser_strategy": "HdtRdbCli",
  "parser_binary": "...",
  "parser_warnings": [],
  "input": {},
  "summary": {},
  "findings": [],
  "validation": {},
  "uncertainties": [],
  "errors": [],
  "outputs": {}
}
```

### 4.2 Status Semantics

The status field must be interpreted strictly:

| Status | Meaning |
|---|---|
| `success` | HDT parser ran successfully and enough data exists to answer the request |
| `partial` | Some data exists, but required coverage is incomplete or validation is not fully sufficient |
| `failed` | Analysis could not be completed and must not be presented as successful |

Phase-02 must ensure that `failed` and `partial` are not hidden behind successful-looking terminal or docx outputs.

### 4.3 Parser Metadata

The following fields must always be present:

```json
{
  "parser_required": true,
  "parser_strategy": "HdtRdbCli",
  "parser_binary": "/path/to/rdb or unavailable",
  "parser_warnings": []
}
```

If `rdb` is missing or invalid, the analysis must fail explicitly.

### 4.4 Output Metadata

`outputs` must include generated file paths and existence status:

```json
{
  "outputs": {
    "output_dir": "/tmp/axe_rdb_assistant/<run_id>",
    "summary_txt": {
      "path": "...",
      "exists": true
    },
    "result_json": {
      "path": "...",
      "exists": true
    },
    "report_docx": {
      "path": "...",
      "exists": true
    }
  }
}
```

---

## 5. Three-Layer Validation Hardening

### 5.1 Mechanical Validation

Mechanical validation must check:

1. input file path is present;
2. input RDB file exists;
3. SHA256 was computed if the file exists;
4. HDT `rdb` is available in `PATH`;
5. HDT command execution completed successfully;
6. parser output file was produced;
7. `summary.txt` was written;
8. `result.json` was written;
9. `report.docx` was written.

Failure in any required mechanical step must produce `status = failed`.

### 5.2 Logical Validation

Logical validation must check:

1. `sum(type_distribution.values()) == total_keys`;
2. `ttl.keys_with_ttl + ttl.keys_without_ttl == total_keys`;
3. `db_count >= 0`;
4. numeric fields are integers;
5. no negative key counts;
6. required summary fields exist.

If logical validation fails, the result must be `partial` or `failed`, depending on severity.

### 5.3 Sufficiency Validation

Sufficiency validation must answer whether the available data is enough to answer the user request.

For Phase-02:

| User Request | Sufficient Condition |
|---|---|
| Basic RDB analysis | basic stats and validation pass |
| Big Key risk analysis | Big Key data or explicit deferred/insufficient state |
| TTL analysis | TTL summary exists and passes logical validation |
| Formal report | report.docx exists and contains required minimal sections |

The Skill must guide the LLM not to overstate sufficiency when data is missing.

---

## 6. Source Traceability Requirements

Every conclusion-like object should include or reference a source.

Required source-bearing fields:

1. `input.source`;
2. `summary.source`;
3. each `finding.source`;
4. each `uncertainty.source`, when applicable;
5. each validation detail where possible.

Examples:

```json
{
  "finding": "All keys are persistent.",
  "severity": "info",
  "source": "summary.ttl"
}
```

A conclusion without a source must be treated as an inference and labeled as such.

---

## 7. Summary Output Hardening

`summary.txt` must be consistent with `result.json`.

It must include:

1. analysis target;
2. parser metadata;
3. basic statistics;
4. TTL overview;
5. type distribution;
6. validation results;
7. findings;
8. uncertainties;
9. errors;
10. generated outputs.

It must not include statistics that are absent from `result.json`.

---

## 8. Docx Output Hardening

`report.docx` must remain minimal, but must include:

1. title;
2. analysis time;
3. RDB file path;
4. SHA256;
5. parser strategy;
6. parser binary;
7. analysis status;
8. basic statistics;
9. validation results;
10. findings and uncertainties;
11. Phase-01 / Phase-02 limitations.

Advanced styling is deferred.

---

## 9. Skill Update Requirements

`SKILL.md` must be updated to reflect Phase-02 semantics:

1. `result.json` is the source of truth;
2. status semantics are strict;
3. failed analysis must not be summarized as success;
4. partial analysis must be labeled partial;
5. `/tmp` outputs must be read through `run_command cat`, not `read_file`;
6. source traceability must be respected;
7. the LLM must not compute deterministic totals.

---

## 10. Testing Requirements

Phase-02 must add or harden tests for:

1. success schema validation;
2. missing RDB file;
3. missing HDT `rdb`;
4. invalid HDT `rdb`;
5. HDT command failure;
6. output file existence metadata;
7. logical total mismatch;
8. TTL total mismatch;
9. source field requirements;
10. docx generation presence;
11. summary and JSON consistency.

Tests must not require remote Redis, SSH, MySQL, MCP, or sub-agents.

---

## 11. Acceptance Criteria

Phase-02 is accepted only if:

- [x] `result.json` has a stable schema version;
- [x] success / partial / failed semantics are enforced;
- [x] parser metadata is always present;
- [x] output file metadata is present;
- [x] mechanical validation is stricter than Phase-01;
- [x] logical validation covers type and TTL totals;
- [x] sufficiency validation is request-aware at a minimal level;
- [x] summary and JSON do not contradict each other;
- [x] docx contains required minimal sections;
- [x] failed cases still produce reviewable outputs;
- [x] tests cover success and failure paths;
- [x] no `src/`, root-level `scripts/`, MCP, sub-agents, remote Redis, SSH, or MySQL staging are introduced.

---

## 12. Deliverables

Phase-02 must deliver:

1. hardened `result.json` contract;
2. updated validation logic;
3. updated summary generation;
4. updated minimal docx content;
5. updated `SKILL.md`;
6. added or updated tests;
7. `docs/reviews/phase-02-review.md`;
8. `docs/reviews/phase-02-closeout.md`.

---

## 13. Exit Criteria

Phase-02 can be closed when:

1. all tests pass;
2. direct script smoke test succeeds;
3. axe dry-run still loads the agent and Skill;
4. at least one real local RDB run produces all required outputs;
5. failed-path tests generate failed outputs correctly;
6. Phase-02 review and closeout documents are completed.
