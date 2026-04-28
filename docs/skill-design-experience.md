# Skill Design Experience

This document records axe-side Skill design lessons from the Redis RDB assistant implementation.

## What should a Skill own?

A Skill should own the LLM-facing operating manual: task scope, supported inputs, execution entrypoint, evidence rules, output reading rules, uncertainty handling, and forbidden behaviors. In this project, `skills/redis-rdb-analysis/SKILL.md` owns the instruction contract for local Redis RDB analysis while keeping deterministic work outside the LLM.

The Skill should also point to domain resources that shape interpretation, such as `references/redis_bigkey_thresholds.yaml`, `references/ttl_risk_rules.yaml`, profiles, and `assets/report_outline.yaml`.

## What should a Tool or custom function own?

Tools and custom functions should own deterministic, repeatable operations: parsing, hashing, arithmetic validation, output generation, docx rendering, audit metadata, and repeat-run comparison. The Redis RDB script owns local execution and HDT invocation; reusable tools own validation, docx rendering, and audit comparison.

The LLM should not compute Redis totals, TTL totals, SHA256 values, parser compatibility, output existence, or repeatability results.

## How can agent behavior be driven by Skill as much as possible?

The agent prompt stays short and points to the Skill. The Skill defines one execution path, one script entrypoint, where to read outputs, and how to treat failed or partial analysis. This prevents the agent prompt from becoming a second workflow definition.

The strongest pattern was: agent prompt routes to Skill; Skill routes to deterministic script; script writes source-of-truth artifacts.

## How can business flow avoid being over-hardcoded in code?

Code should enforce safety and reproducibility, not decide every narrative. The script validates local file access, HDT availability, parser execution, output metadata, and audit archive generation. Domain language, thresholds, report sections, and profile preferences live in `references/` and `assets/`.

This leaves future Redis risk wording and report style editable without changing parser execution.

## How can Skill become a core project asset?

The Skill becomes a core asset when it is versioned with tests, has clear boundaries, and is treated as the main product interface for LLM behavior. It should be readable enough for review and stable enough that scripts, references, and profiles can evolve around it.

In this project, tests assert that the Skill contains required sections, avoids user-specific absolute paths, and points to resource files instead of embedding large threshold tables.

## How should assets, scripts, references, and profiles be managed around a Skill?

Scripts should stay under the Skill when they are domain-specific. Generic helpers should stay under `tools/`. References should contain domain facts and recommendation candidates. Profiles should describe request-level preferences, not parser logic. Assets should contain report outline and examples, not execution flow.

The resulting boundary is:

- `SKILL.md`: operating manual and evidence rules.
- `scripts/`: Redis RDB-specific deterministic execution.
- `references/`: Redis domain material and thresholds.
- `references/profiles/`: presentation preferences.
- `assets/`: report outline, templates, and examples.
- `tools/`: reusable validation, docx, and audit helpers.

## How can the project preserve LLM decision capability while keeping results reliable and auditable?

The LLM can decide how to present verified facts, uncertainties, and supported recommendations. It cannot invent deterministic facts. Reliability comes from `result.json`, `summary.txt`, `report.docx`, validation blocks, output metadata, audit metadata, and repeatability comparison.

The practical rule is: deterministic facts come from generated artifacts; LLM judgment is allowed only after those artifacts establish status, source, and validation quality.
