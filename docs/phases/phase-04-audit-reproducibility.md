# Phase-04 SPEC: Audit, Reproducibility, and Run Archive

> Project: axe-dba-assistant  
> Phase: Phase-04  
> Status: planning  
> Scope: Run archive, audit capture, repeatability evidence  
> Main SPEC: axe Redis RDB Assistant Main SPEC v2.1  
> Depends On: Phase-02 and Phase-03  
> Phase SPEC Path: `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-04-audit-reproducibility.md`

---

## 1. Phase Positioning

Phase-04 focuses on auditability and reproducibility.

Earlier phases produce usable local Redis RDB analysis outputs. Phase-04 makes each run reviewable after the fact and prepares evidence for later axe vs DeepAgents comparison.

This phase must not patch or wrap axe itself. Audit capture should use lightweight scripts, shell redirection, axe native verbose/json output, and generated run metadata.

---

## 2. Phase Goals

Phase-04 must implement or formalize:

1. run ID generation;
2. stable run archive layout;
3. user request preservation;
4. RDB fingerprint preservation;
5. stdout/stderr capture;
6. axe verbose trace capture where available;
7. axe json output capture where available;
8. environment metadata capture;
9. model/provider metadata capture;
10. repeat-run evidence for the same RDB file.

---

## 3. Non-Goals

Phase-04 does not include:

1. web UI for archives;
2. long-term archive indexing service;
3. external database for run history;
4. automatic axe vs DeepAgents decision;
5. remote Redis;
6. SSH;
7. MySQL staging;
8. MCP;
9. sub-agents;
10. patching axe.

---

## 4. Target Run Archive Layout

Each run should produce:

```text
/tmp/axe_rdb_assistant/<run_id>/
├── report.docx
├── result.json
├── summary.txt
├── audit/
│   ├── meta.json
│   ├── stdout.log
│   ├── stderr.log
│   ├── axe_verbose.log
│   └── trace.json
└── input/
    ├── user_request.txt
    └── rdb.fingerprint
```

The project repository must not store generated run archives.

---

## 5. Audit Metadata Requirements

`audit/meta.json` should include:

```json
{
  "run_id": "...",
  "started_at": "...",
  "finished_at": "...",
  "duration_ms": 0,
  "command": "...",
  "workdir": "...",
  "agent": "redis-rdb-assistant",
  "skill": "skills/redis-rdb-analysis/SKILL.md",
  "model": "...",
  "provider": "...",
  "rdb_path": "...",
  "rdb_sha256": "...",
  "exit_code": 0,
  "status": "success | partial | failed",
  "parser_strategy": "HdtRdbCli",
  "parser_binary": "..."
}
```

---

## 6. Wrapper Script Boundary

A lightweight audit wrapper may be introduced if needed.

It must:

1. call axe normally;
2. not patch axe;
3. not reimplement assistant logic;
4. not parse natural language;
5. not decide business flow;
6. remain small and auditable.

Preferred location:

```text
tools/audit/
```

or, if strictly tied to this Skill:

```text
skills/redis-rdb-analysis/scripts/
```

The wrapper should not become a second assistant entrypoint.

---

## 7. Reproducibility Requirements

Phase-04 must include a repeatability procedure:

1. run the same RDB analysis at least three times;
2. compare key fields in `result.json`;
3. confirm stable fields remain stable:
   - SHA256;
   - total_keys;
   - db_count;
   - type_distribution;
   - TTL totals;
   - parser strategy;
4. allow volatile fields to differ:
   - run_id;
   - timestamps;
   - duration;
   - output_dir.

A repeatability summary should be stored under:

```text
docs/reviews/phase-04-repeatability.md
```

---

## 8. axe Trace Capture Requirements

Where axe supports it, Phase-04 should capture:

1. verbose output;
2. json trace output;
3. tool-call trace;
4. model latency;
5. token usage.

If the runtime does not provide a required field, document the limitation instead of fabricating it.

---

## 9. Privacy and Storage Rules

Phase-04 does not implement redaction.

Generated outputs may contain Redis key names.

Run archives are stored under `/tmp/axe_rdb_assistant/<run_id>/` and should not be committed to Git.

If long-term retention is needed, the user must copy selected archives to a controlled storage location.

---

## 10. Testing Requirements

Add tests or smoke checks for:

1. archive directory creation;
2. required archive files;
3. `audit/meta.json` required fields;
4. command exit code capture;
5. failed run archive creation;
6. repeat-run comparison script behavior;
7. generated archive is not placed under repository root.

---

## 11. Acceptance Criteria

Phase-04 is accepted only if:

- [ ] run archive layout matches the spec;
- [ ] `audit/meta.json` is generated;
- [ ] stdout/stderr or equivalent logs are captured;
- [ ] axe verbose/json traces are captured or limitation is documented;
- [ ] failed runs are archived;
- [ ] repeatability check is documented;
- [ ] no axe patching or wrapping beyond a lightweight wrapper occurs;
- [ ] no generated archive files are committed to the repository.

---

## 12. Deliverables

Phase-04 must deliver:

1. archive/audit implementation;
2. audit metadata schema;
3. repeatability procedure;
4. repeatability review document;
5. updated README or usage documentation;
6. tests or smoke checks;
7. `docs/reviews/phase-04-review.md`;
8. `docs/reviews/phase-04-closeout.md`.

---

## 13. Exit Criteria

Phase-04 can be closed when:

1. successful and failed runs both produce archives;
2. at least three repeated runs are compared;
3. trace capture behavior is documented;
4. generated artifacts remain outside the repository;
5. phase review and closeout documents are complete.
