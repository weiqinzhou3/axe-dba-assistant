# Phase-05 SPEC: Skill Design Experience and Route Comparison Preparation

> Project: axe-dba-assistant  
> Phase: Phase-05  
> Status: finished  
> Scope: Skill design experience, anti-patterns, and axe-side comparison evidence  
> Main SPEC: axe Redis RDB Assistant Main SPEC v2.1  
> Depends On: Phase-01 to Phase-04  
> Phase SPEC Path: `/Users/zqw/Desktop/Project/axe-dba-assistant/docs/phases/phase-05-skill-experience-comparison-prep.md`

---

## 1. Phase Positioning

Phase-05 closes the implementation-oriented part of the axe Redis RDB assistant project.

The project goal is not only to build a Redis RDB analysis assistant. It is also to provide evidence for deciding whether future DBA assistants should be built on axe or DeepAgents SDK.

Phase-05 does not make the final technology decision automatically. It prepares the axe-side evidence and lessons.

---

## 2. Phase Goals

Phase-05 must produce:

1. Skill design experience document;
2. anti-pattern case collection;
3. comparison evidence for the axe side;
4. summary of what was reused from the old DBA Assistant and what was discarded;
5. final Phase-01 to Phase-04 closeout summary;
6. recommendation on readiness for manual axe vs DeepAgents comparison.

---

## 3. Non-Goals

Phase-05 does not include:

1. final automatic technology selection;
2. building an automatic benchmark platform;
3. expanding Redis RDB features;
4. remote Redis support;
5. MySQL staging;
6. MCP or sub-agent architecture;
7. web UI or API.

---

## 4. Required Experience Document

Create:

```text
docs/skill-design-experience.md
```

It must answer the seven questions from the main SPEC:

1. What should a Skill own?
2. What should a Tool or custom function own?
3. How can agent behavior be driven by Skill as much as possible?
4. How can business flow avoid being over-hardcoded in code?
5. How can Skill become a core project asset?
6. How should assets, scripts, references, and profiles be managed around a Skill?
7. How can the project preserve LLM decision capability while keeping results reliable and auditable?

---

## 5. Anti-Pattern Collection

Create:

```text
docs/anti-patterns.md
```

Include examples such as:

1. hard-coding local absolute paths in `SKILL.md`;
2. making LLM perform deterministic arithmetic;
3. hiding parser failures behind success output;
4. using fallback parsers without exposing uncertainty;
5. letting scripts become the workflow brain;
6. putting thresholds inside `SKILL.md`;
7. putting report layout inside `SKILL.md`;
8. using `read_file` for `/tmp` absolute paths when the runtime rejects it;
9. introducing `src/` too early;
10. creating multiple execution entrypoints.

Each anti-pattern should include:

```text
Problem
Why it is harmful
Observed or possible example
Preferred pattern
```

---

## 6. axe-Side Comparison Evidence

Create:

```text
docs/comparison/axe-side-evidence.md
```

Cover the six comparison dimensions:

| Dimension | Evidence Needed |
|---|---|
| C1 Skill readability | SKILL.md and supporting resources |
| C2 Run stability | repeated local RDB runs |
| C3 LLM decision space | trace examples and Skill-driven behavior |
| C4 token / latency | verbose/json trace data when available |
| C5 Debuggability | failure cases and how they were diagnosed |
| C6 Cross-scenario reuse | docx/validation/tools and Skill package pattern |

If a metric is unavailable, state the limitation clearly.

---

## 7. DBA Assistant Reuse / Discard Record

Create:

```text
docs/comparison/dba-assistant-reuse-record.md
```

Document:

1. logic reused from the old DBA Assistant;
2. logic intentionally discarded;
3. directory structure intentionally not reused;
4. parser strategy changes;
5. Skill vs script vs tools boundary changes;
6. why axe-specific structure is different.

---

## 8. Final Project Summary

Create:

```text
docs/reviews/project-phase-01-to-05-summary.md
```

It should include:

1. phase summary;
2. delivered artifacts;
3. known limitations;
4. deferred capabilities;
5. risks;
6. whether the project is ready for manual comparison;
7. recommended next step.

---

## 9. Testing and Evidence Requirements

Phase-05 does not require major new code, but must verify:

1. Phase-01 to Phase-04 closeout documents exist;
2. all generated evidence documents exist;
3. links and paths in docs are valid;
4. no generated run archives are committed;
5. no known blocking issue remains undocumented.

---

## 10. Acceptance Criteria

Phase-05 is accepted only if:

- [x] `docs/skill-design-experience.md` exists;
- [x] `docs/anti-patterns.md` exists;
- [x] `docs/comparison/axe-side-evidence.md` exists;
- [x] `docs/comparison/dba-assistant-reuse-record.md` exists;
- [x] final project summary exists;
- [x] six comparison dimensions are covered;
- [x] seven Skill boundary questions are answered;
- [x] known limitations are documented;
- [x] project is ready for manual axe vs DeepAgents comparison.

---

## 11. Deliverables

Phase-05 must deliver:

1. Skill design experience document;
2. anti-pattern collection;
3. axe-side evidence document;
4. DBA Assistant reuse/discard record;
5. final project summary;
6. `docs/reviews/phase-05-review.md`;
7. `docs/reviews/phase-05-closeout.md`.

---

## 12. Exit Criteria

Phase-05 can be closed when:

1. all required documents are present;
2. all comparison dimensions are covered;
3. all open limitations are documented;
4. manual comparison can start without additional implementation work;
5. Phase-05 review and closeout documents are complete.
