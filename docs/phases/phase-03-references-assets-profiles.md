# Phase-03 SPEC: References, Assets, and Profiles Systematization

> Project: axe-dba-assistant  
> Phase: Phase-03  
> Status: finished  
> Scope: Redis RDB references, profiles, report assets, and Skill thinning  
> Main SPEC: axe Redis RDB Assistant Main SPEC v2.1  
> Depends On: Phase-02 Output Contract and Validation Hardening  
> Phase SPEC Path: `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-03-references-assets-profiles.md`

---

## 1. Phase Positioning

Phase-03 organizes the non-code assets that make the Redis RDB Skill maintainable.

By the end of Phase-02, execution and output contracts should be stable. Phase-03 moves domain rules, report layout decisions, thresholds, profiles, and reusable wording into well-defined Skill resources.

The purpose is to keep `SKILL.md` as an LLM-facing operating manual, not a storage location for thresholds, report templates, or long knowledge tables.

---

## 2. Phase Goals

Phase-03 must establish:

1. a complete Redis RDB references structure;
2. reusable profile definitions;
3. docx template and report outline assets;
4. a clean relationship between `SKILL.md`, `references/`, `assets/`, and `scripts/`;
5. clearer boundaries for future Redis-related Skills.

---

## 3. Non-Goals

Phase-03 does not include:

1. remote Redis collection;
2. SSH RDB fetching;
3. MySQL staging;
4. multi-RDB aggregation;
5. full audit trace archival;
6. final axe vs DeepAgents comparison;
7. web UI or API;
8. MCP or sub-agent introduction.

---

## 4. Target Skill Package Structure

Phase-03 should converge on:

```text
skills/redis-rdb-analysis/
├── SKILL.md
├── scripts/
│   └── analyze_local_rdb.py
├── references/
│   ├── redis_bigkey_thresholds.yaml
│   ├── redis_risk_levels.yaml
│   ├── redis_recommendations.yaml
│   ├── redis_type_notes.yaml
│   ├── ttl_risk_rules.yaml
│   └── profiles/
│       ├── default.yaml
│       ├── rcs.yaml
│       └── concise.yaml
└── assets/
    ├── report_outline.yaml
    ├── docx_templates/
    │   └── minimal_report_template.docx
    └── examples/
        ├── summary_example.txt
        └── result_example.json
```

---

## 5. References Requirements

### 5.1 Big Key Thresholds

`redis_bigkey_thresholds.yaml` must define threshold rules by data type where possible.

It should include:

1. string size threshold;
2. hash field count threshold;
3. list element count threshold;
4. set member count threshold;
5. zset member count threshold;
6. stream length threshold;
7. severity levels;
8. rationale comments.

Phase-03 does not need perfect thresholds, but must establish a clean editable structure.

### 5.2 Risk Levels

`redis_risk_levels.yaml` must define risk severity semantics:

```yaml
levels:
  info:
    meaning: "Informational finding"
  low:
    meaning: "Low operational risk"
  medium:
    meaning: "Requires attention"
  high:
    meaning: "Likely operational impact"
  critical:
    meaning: "Immediate action recommended"
```

### 5.3 Recommendations

`redis_recommendations.yaml` must provide reusable recommendation candidates.

Recommendations must not be blindly emitted. They are candidates that the LLM may use when findings support them.

### 5.4 TTL Rules

`ttl_risk_rules.yaml` must define how to describe TTL-related risks, such as:

1. many keys without TTL;
2. many keys expiring at the same time;
3. TTL analysis unavailable;
4. persistent cache-like keys.

### 5.5 Redis Type Notes

`redis_type_notes.yaml` should contain concise Redis data type explanations for report wording.

---

## 6. Profiles Requirements

Profiles describe request-level preferences, not domain truth.

Required profiles:

| Profile | Purpose |
|---|---|
| `default.yaml` | default Chinese report behavior |
| `rcs.yaml` | richer client-facing analysis style |
| `concise.yaml` | short terminal-oriented analysis |

Each profile should define:

```yaml
language: zh
detail_level: normal
include_docx: true
include_json: true
include_summary: true
report_style: minimal
max_findings: 20
```

Profiles must not contain parser logic or business execution flow.

---

## 7. Assets Requirements

### 7.1 Report Outline

`assets/report_outline.yaml` must define the Redis RDB report structure:

1. analysis target;
2. parser metadata;
3. basic statistics;
4. TTL overview;
5. type distribution;
6. findings;
7. validation results;
8. uncertainties and limitations;
9. generated outputs.

### 7.2 Docx Template

The docx template may remain minimal, but the asset boundary must be clear:

| Concern | Location |
|---|---|
| Generic rendering | `tools/docx_renderer/` |
| Redis report outline | `skills/redis-rdb-analysis/assets/report_outline.yaml` |
| Redis docx template | `skills/redis-rdb-analysis/assets/docx_templates/` |
| Redis content decisions | `SKILL.md` + result data |

---

## 8. Skill Thinning Requirements

`SKILL.md` should be reviewed and shortened where appropriate.

It should keep:

1. task definition;
2. execution rule;
3. supported inputs;
4. parser requirement;
5. script usage;
6. output reading rule;
7. evidence rule;
8. forbidden behaviors.

It should move long static knowledge into `references/` or `assets/`.

---

## 9. Script Integration Requirements

`analyze_local_rdb.py` may read references and profiles when needed, but must keep deterministic execution behavior.

It may:

1. load selected profile;
2. include profile metadata in `result.json`;
3. load thresholds for future findings;
4. load report outline for docx rendering.

It must not let references override execution safety rules.

---

## 10. Testing Requirements

Add tests for:

1. all required reference files exist;
2. all required profile files exist;
3. YAML files are parseable;
4. required profile fields exist;
5. report outline has required sections;
6. `SKILL.md` does not hard-code thresholds that belong in references;
7. `SKILL.md` does not contain user-specific absolute paths;
8. missing optional reference files produce clear errors or warnings.

---

## 11. Acceptance Criteria

Phase-03 is accepted only if:

- [x] required references exist;
- [x] required profiles exist;
- [x] required assets exist;
- [x] profile structure is documented;
- [x] report outline is externalized;
- [x] Skill is thinner and does not embed long threshold tables;
- [x] tests validate references, profiles, and assets;
- [x] no execution scope expansion occurs.

---

## 12. Deliverables

Phase-03 must deliver:

1. complete references directory;
2. complete profiles directory;
3. report outline asset;
4. minimal docx template asset;
5. updated `SKILL.md`;
6. updated script/profile integration if needed;
7. tests for references/assets/profiles;
8. `docs/reviews/phase-03-review.md`;
9. `docs/reviews/phase-03-closeout.md`.

---

## 13. Exit Criteria

Phase-03 can be closed when:

1. all reference/profile/asset tests pass;
2. local RDB analysis still works;
3. output contract from Phase-02 remains stable;
4. Skill remains the main LLM guide;
5. phase review and closeout documents are complete.
