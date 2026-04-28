# axe-Side Comparison Evidence

This document prepares evidence for manual axe vs DeepAgents comparison. It does not make the final technology decision.

## C1 Skill readability

Evidence:

- `skills/redis-rdb-analysis/SKILL.md` is the primary LLM behavior guide.
- Static domain content is externalized into `references/` and `assets/`.
- Tests validate required Skill sections and prohibit user-specific absolute paths.

Assessment:

The Skill-first model is readable when the Skill stays focused on execution rules, evidence rules, and forbidden behavior.

## C2 Run stability

Evidence:

- `docs/reviews/phase-04-repeatability.md` records three repeated runs against the same RDB file.
- Stable fields matched: SHA256, total keys, DB count, type distribution, TTL totals, and parser strategy.
- `tools/audit/compare_repeated_runs.py` automates stable-field comparison.

Assessment:

The deterministic script path is stable for local RDB input when HDT `rdb` is available.

## C3 LLM decision space

Evidence:

- The LLM chooses response wording based on `result.json`, `summary.txt`, validation status, findings, and uncertainties.
- The LLM does not choose parser path, compute totals, or fabricate source facts.
- The Skill preserves decision space for presentation while enforcing source-of-truth artifacts.

Assessment:

axe can support a useful boundary: Skill drives behavior, script supplies verified facts, LLM explains results.

## C4 token / latency

Evidence:

- Phase-04 captures direct script audit metadata such as duration and command.
- Direct `analyze_local_rdb.py` execution does not run through axe model execution.

Unavailable metric:

Real axe token usage, model latency, and tool-call traces are unavailable from direct script runs. `audit/axe_verbose.log` and `audit/trace.json` document this limitation instead of fabricating metrics.

Assessment:

Manual comparison should run a provider-backed axe session with native verbose/json trace enabled before comparing token or latency behavior with DeepAgents.

## C5 Debuggability

Evidence:

- Missing RDB, missing HDT, invalid PATH `rdb`, and HDT command failure all produce failed `result.json` outputs.
- Phase-04 archives failed runs with `audit/meta.json`, `stderr.log`, and `trace.json`.
- Tests cover success and failure paths.

Assessment:

Debuggability is strong for deterministic script failures and local parser setup issues.

## C6 Cross-scenario reuse

Evidence:

- `tools/validation/` can validate structured result contracts.
- `tools/docx_renderer/` is generic docx rendering.
- `tools/audit/` compares repeated result files.
- The Skill package pattern can be reused by future DBA assistants with different domain references and scripts.

Assessment:

The reusable boundary is viable: common tools stay under `tools/`, domain-specific assets stay under Skill packages.

## Readiness

The axe side is ready for manual axe vs DeepAgents comparison. The comparison should use the same local RDB fixture, same requested report, and same acceptance criteria for output contract, audit archive, and failure handling.
