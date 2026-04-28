# Main SPEC for the axe-based Redis RDB Analysis Assistant

> **Version**: 2.1  
> **Language**: English  
> **Status**: Draft for Review  
> **Assumed Repo Root**: `/Users/zqw/Desktop/Project/axe-dba-assistant`

---

## 1. Document Purpose

This document is the main specification for the axe-based Redis RDB Analysis Assistant. It defines project-level stable requirements: project goals, phase plan, responsibility boundaries, Skill vs Tool boundaries, behavioral constraints, documentation structure, and acceptance criteria.

The main SPEC must remain stable. It must not contain detailed implementation tasks, per-phase execution details, or the full Redis RDB analysis field list. Those details belong to phase SPECs, Skill documents, references, assets, and tool documentation.

---

## 2. Background and Real End State

A Redis RDB analysis capability already exists in a DeepAgents SDK-based DBA Assistant project. However, that project exposed several issues:

1. Business flow can become hardcoded in the controller layer;
2. Skill responsibility is not sufficiently clear;
3. The repository structure is messy, mixing experiments, temporary code, and formal capabilities;
4. The boundary between LLM decisions, Tool execution, and Skill guidance is unstable.

This project reimplements the Redis RDB analysis assistant on top of axe. The real end state is not to simply replace the DBA Assistant. The purpose is to gather evidence for a future technical route decision: whether operational assistants should be built with axe or continue with the DeepAgents SDK.

Reference project, for analysis logic only, not for repository structure:

```text
Local: /Users/zqw/Desktop/Project/dba_assistant
GitHub: https://github.com/weiqinzhou3/dba_assistant
```

---

## 3. Phase Plan and Status

### 3.1 Phase Status Values

| Status | Meaning |
|---|---|
| `planning` | Planned, not yet started |
| `starting` | Started, bootstrapping or initial implementation |
| `in_progress` | Main development is ongoing |
| `blocked` | Blocked by an external dependency or critical issue |
| `reviewing` | Implementation completed, under review |
| `finished` | Completed, reviewed, and closed |

### 3.2 Current Phase Index

> This table is the phase index in the main SPEC. Detailed phase scope is defined by each phase SPEC.

| Phase | Name | Current Status | Absolute Local Phase SPEC Path | Goal |
|---|---|---|---|---|
| Phase-01 | Skill First Local RDB MVP | `finished` | `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-01-local-rdb-skill-first-mvp.md` | Build the axe agent, Redis RDB Skill, local RDB analysis script, minimal summary / JSON / docx outputs, and validate the Skill-driven loop |
| Phase-02 | Output Contract and Three-layer Validation Hardening | `finished` | `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-02-output-validation-hardening.md` | Stabilize JSON schema, report structure, mechanical validation, logical validation, sufficiency validation, source requirements, and partial/failed/uncertainty states |
| Phase-03 | References / Assets / Profiles Completion | `planning` | `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-03-skill-assets-references-profiles.md` | Complete Big Key thresholds, risk levels, recommendation library, profiles, docx templates, and report assets; keep the Skill thinner and more stable |
| Phase-04 | Audit and Repeatability | `planning` | `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-04-audit-repeatability.md` | Implement full run archival, stdout/stderr, axe verbose/json trace, token/latency/tool-call records, and repeated run evidence |
| Phase-05 | Skill Experience and Route Comparison Preparation | `planning` | `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-05-skill-experience-comparison-prep.md` | Produce Skill design lessons, anti-patterns, and axe-side evidence for a later manual comparison with DeepAgents SDK |

### 3.3 Phase Boundary Rules

1. The main SPEC only maintains the phase index, phase status, and high-level goals;
2. Phase tasks, non-goals, and acceptance checklists belong to separate phase SPECs;
3. Phase SPECs may evolve frequently; the main SPEC should not change for ordinary task-level adjustments;
4. A phase closeout is required before moving to the next phase;
5. If a phase changes the responsibility model, axe usage constitution, or behavioral boundaries in this SPEC, the main SPEC must be revised first.

---

## 4. Validation Goals and Comparison Dimensions

### 4.1 Questions to Answer About Skill / Tool Boundaries

The project must answer these questions through implementation:

1. What should a Skill own?
2. What should a Tool or custom capability own?
3. Where are the boundaries between scripts, tools, references, assets, and profiles?
4. How can Agent behavior be driven by Skills as much as possible?
5. How can business flow avoid being over-hardcoded in code?
6. How can Skills become the core project asset?
7. How should assets, scripts, references, and profiles be organized around Skills?
8. How can the project preserve LLM decision-making while keeping results reliable, reviewable, and deliverable?

### 4.2 Evidence Required During Stage One

| Dimension | Meaning | Evidence to Collect |
|---|---|---|
| C1. Skill readability | Whether a third party can quickly understand what the assistant does | Skill document, referenced assets, boundary documentation |
| C2. Runtime stability | Consistency across repeated runs with the same input | Multiple outputs from the same RDB file |
| C3. LLM decision space | LLM decisions vs code/framework constraints | Decision traces and call paths |
| C4. Token / latency | Cost and latency of one complete analysis | token/latency data from axe verbose/json |
| C5. Debuggability | Difficulty of diagnosing failures | Failure records, stdout/stderr, trace logs |
| C6. Cross-scenario reuse | Whether the design can move to inspection, CVE, slow SQL, and other analysis scenarios | Reusability of tools, assets, and references |

The final axe vs DeepAgents SDK comparison is manual. Stage one only collects axe-side evidence.

---

## 5. Responsibility Model

### 5.1 Responsibility Layers

| Layer | Decision Question | Typical Content |
|---|---|---|
| Code / Script | Does the same input always produce the same output? Does it require no natural-language understanding? | Local RDB parsing, statistics, file checks, SHA256, structured result generation |
| Tool | Is it reusable across multiple Skills? Is it a stable deterministic capability? | docx rendering, generic validation, archival, file fingerprinting, format conversion |
| References | Is it a value table, standard, threshold, risk level, or recommendation library? | Big Key thresholds, risk levels, Redis recommendation library, profiles |
| Assets | Is it a template, style, example, or static deliverable asset? | docx templates, report outline templates, style files |
| Skill | Is it a stable domain rule that the LLM must read and follow at runtime? | Intent rules, flow principles, invocation rules, evidence requirements, forbidden behaviors |
| LLM Runtime | Does it require natural-language understanding or generation? Does it require multi-signal synthesis? | User intent understanding, synthesized risk judgment, sufficiency judgment, final response wording |

### 5.2 One-sentence Rule

**Redis RDB-specific execution belongs to Skill scripts; deterministic capabilities reused across Skills belong to tools; thresholds, risk levels, recommendation libraries, and profiles belong to references; templates and static report assets belong to assets; the Skill tells the LLM how to use all of them.**

### 5.3 Project Constraints for scripts, tools, and src

The project does not introduce `src/` as a default implementation layer in early phases, to avoid premature abstraction.

Phase-01 constraints:

1. Redis RDB-specific actions go under `skills/redis-rdb-analysis/scripts/`;
2. Generic docx rendering goes under `tools/docx_renderer/`;
3. Generic validation goes under `tools/validation/`;
4. `skills/scripts` may internally call `tools`;
5. In Phase-01, the LLM should directly call only the RDB Skill script, not orchestrate multiple tools itself;
6. Do not create `src/` unless a later phase explicitly identifies script bloat or shared-library needs across multiple Skills.

### 5.4 Three-layer Validation

| Layer | Content | Owner |
|---|---|---|
| Mechanical validation | Does the RDB file exist? Did parsing succeed? Is the exit code 0? Were output files generated? | Skill script + tools/validation |
| Logical validation | Are key counts, type distribution, TTL stats, source fields, and schema consistent? | Skill script + tools/validation + references |
| Sufficiency validation | Is the data enough to answer the user request? Which conclusions are uncertain? | LLM + SKILL.md |

---

## 6. axe Native Capability Constitution

| axe Capability | Project Rule |
|---|---|
| built-in tools | Allowed, especially read_file / write_file / list_directory / run_command |
| run_command | The main Phase-01 mechanism for invoking Skill scripts |
| Skill scripts | Allowed and treated as an important part of the Skill package |
| `--verbose` / `--json` | Required for audit and comparison evidence |
| memory | Disabled by default unless a later phase explicitly needs cross-run comparison |
| sub-agent | Not used; keep a single-agent shape |
| MCP server | Not used; out of scope |
| patching axe | Forbidden |
| wrapping axe itself | Forbidden |

Capability priority:

```text
Skill scripts → run_command local CLI → generic tools → custom agent tool later if justified
```

---

## 7. Core Capability Overview

The assistant should eventually support:

1. Understanding Chinese and English natural-language RDB analysis requests;
2. Recognizing RDB file paths, analysis goals, output forms, and profile;
3. Asking for missing input when needed;
4. Performing local Redis RDB baseline analysis, Big Key analysis, type distribution, and TTL analysis;
5. Producing risk identification and recommendations based on data;
6. Performing mechanical, logical, and sufficiency validation;
7. Producing three output forms: terminal summary, JSON structured result, and docx formal report;
8. Explicitly marking success, partial, failed, and uncertainty states;
9. Producing audit records for each run;
10. Collecting evidence for a later manual axe vs DeepAgents SDK comparison.

---

## 8. Input and Output Constraints

### 8.1 Input

Natural-language input is supported. Phase-01 supports local RDB files only.

### 8.2 Output

| Output Form | Purpose | Constraint |
|---|---|---|
| Terminal summary | Quick inspection | Concise; includes key findings, status, and uncertainties |
| JSON structured result | Review and downstream processing | Stable fields, complete source, tool-validatable |
| docx formal report | Delivery and archival | Phase-01 may produce a minimal docx; later phases harden layout and sections |

### 8.3 docx Responsibility Boundary

1. Generic docx rendering engine belongs to `tools/docx_renderer/`;
2. Redis RDB report templates, section configurations, and style assets belong to `skills/redis-rdb-analysis/assets/`;
3. The Skill describes the business content required in the report;
4. The script maps RDB analysis results into renderer inputs;
5. The LLM does not directly manipulate docx layout.

---

## 9. Recommended Repository Structure

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

Repository constraints:

1. Do not create `src/` in Phase-01;
2. Do not create a root-level `scripts/` directory, to avoid confusion with Skill scripts;
3. Keep Redis RDB-specific actions inside the Skill package;
4. Put deterministic capabilities reusable across Skills into `tools/`;
5. Keep phase documents under `docs/phases/`.

---

## 10. Run Archive and Audit Directory

Run artifacts are archived to:

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

Phase-01 may implement a minimal archive first, but the final stage-one result must satisfy the full structure.

---

## 11. Skill Requirements and Anti-patterns

### 11.1 Skill Positioning

A Skill is a domain operation manual consumed by the LLM at runtime. It is not an engineer-facing product manual and not a repository directory guide.

### 11.2 What the Skill Should Describe

1. Task goal;
2. When to use the Skill;
3. User input recognition rules;
4. Local RDB analysis flow principles;
5. Which Skill script to call;
6. How to use references, assets, and tools;
7. Evidence and source requirements;
8. Output requirements;
9. Failure and uncertainty handling;
10. Forbidden behaviors.

### 11.3 Anti-patterns

Forbidden:

1. Embedding executable code in SKILL.md;
2. Hardcoding thresholds in SKILL.md;
3. Embedding docx layout details in SKILL.md;
4. Letting tools replace the Skill as the process brain;
5. Letting scripts bypass the Skill and become a black box;
6. Letting the LLM perform deterministic statistics, filtering, or arithmetic;
7. Presenting partial analysis as full success;
8. Reusing the messy structure of the old DBA Assistant project.

---

## 12. Behavioral Boundaries

### 12.1 Allowed

1. Analyze a user-specified local RDB file;
2. Generate summary, JSON, and docx outputs;
3. Produce risk judgments based on references;
4. Use tools for generic validation and docx rendering;
5. Clearly state uncertainty and insufficient information;
6. Collect runtime evidence through axe verbose/json.

### 12.2 Forbidden

1. Making unsupported definitive claims;
2. Fabricating keys, statistics, or risks;
3. Hiding failures;
4. Presenting partial analysis as full analysis;
5. Patching axe;
6. Wrapping axe itself;
7. Introducing MCP;
8. Introducing sub-agents;
9. Letting Tools replace Skills as the process brain;
10. Introducing remote Redis, SSH fetch, or MySQL staging in Phase-01.

---

## 13. Stage-one Acceptance Criteria

By the end of stage one, the project must have:

1. A runnable axe agent;
2. A loadable Redis RDB Analysis Skill;
3. End-to-end local RDB file analysis;
4. summary, result.json, and report.docx outputs;
5. Three-layer validation;
6. Source traceability for every conclusive output;
7. Full run archive generation;
8. Clear boundaries among Skill, scripts, tools, references, and assets;
9. No MCP, no sub-agent, no axe patch;
10. Skill design lessons, anti-patterns, and axe-side comparison evidence.

---

## 14. Documentation Structure

```text
Main SPEC
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

## 15. SPEC Evolution Rules

The main SPEC should only change when:

1. Project goals change;
2. Phase planning changes;
3. The responsibility model changes;
4. The axe usage constitution changes;
5. Behavioral boundaries change;
6. Repository organization principles change;
7. Phase status needs to be updated.

Ordinary implementation details, task splits, script parameters, and field extensions belong to phase SPECs, Skill documents, or tool documents, not the main SPEC.
