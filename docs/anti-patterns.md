# Anti-Patterns

## Hard-Coding Local Absolute Paths

Problem

Putting user-specific paths such as a local repository path directly into `SKILL.md`.

Why it is harmful

It makes the Skill non-portable and can break when the project is moved or run by another user.

Observed or possible example

Embedding a local script path inside the Skill instead of using a relative Skill package path.

Preferred pattern

Use relative Skill paths in `SKILL.md`. Keep the agent config responsible for the installed absolute Skill path when axe requires one.

## LLM Performs Deterministic Arithmetic

Problem

Asking the LLM to compute Redis key totals, TTL totals, type totals, or SHA256 values.

Why it is harmful

Arithmetic drift can create false confidence and contradict parser output.

Observed or possible example

The LLM totals `type_distribution` by reading prose instead of using `result.json`.

Preferred pattern

The script computes deterministic values and writes them to `result.json`; the LLM only reports verified facts.

## Parser Failures Hidden Behind Success

Problem

Returning success-looking summaries when the parser did not complete.

Why it is harmful

Users may act on incomplete or invalid analysis.

Observed or possible example

Unsupported RDB type code is caught, but the final response still says analysis succeeded.

Preferred pattern

Set `status: failed`, include errors and uncertainties, and still generate reviewable outputs.

## Silent Fallback Parsers

Problem

Falling back to a secondary parser without exposing the parser change.

Why it is harmful

Different parsers can support different RDB formats and produce different semantics.

Observed or possible example

Using a built-in parser after HDT fails.

Preferred pattern

Require PATH HDT `rdb`; if it is missing or invalid, fail explicitly.

## Scripts Become the Workflow Brain

Problem

Putting all user-intent decisions and narrative policy into scripts.

Why it is harmful

The code becomes rigid, and the Skill stops being the main LLM behavior asset.

Observed or possible example

Script deciding final business recommendations unrelated to generated evidence.

Preferred pattern

Scripts enforce deterministic execution and validation; Skill and references guide interpretation.

## Thresholds Inside SKILL.md

Problem

Embedding large Big Key or TTL threshold tables directly inside the Skill.

Why it is harmful

The Skill becomes hard to read, review, and update.

Observed or possible example

Adding Redis type thresholds into the operating manual.

Preferred pattern

Keep thresholds in `references/redis_bigkey_thresholds.yaml` and reference them from the Skill.

## Report Layout Inside SKILL.md

Problem

Hard-coding report section order and template details inside the Skill.

Why it is harmful

Layout updates require changing the LLM operating manual.

Observed or possible example

Describing every docx section in prose inside `SKILL.md`.

Preferred pattern

Use `assets/report_outline.yaml` for report structure and `tools/docx_renderer/` for generic rendering.

## read_file for /tmp Outputs

Problem

Using `read_file` on `/tmp/axe_rdb_assistant/<run_id>/...` files when the runtime rejects absolute paths.

Why it is harmful

The LLM may fail to read generated output even though the script completed.

Observed or possible example

Trying to read `/tmp/.../result.json` through a restricted file reader.

Preferred pattern

Use `run_command cat /tmp/axe_rdb_assistant/<run_id>/result.json`.

## Introducing src Too Early

Problem

Creating a root `src/` package before the Skill boundary is proven.

Why it is harmful

It encourages generic application architecture before the product shape is clear.

Observed or possible example

Moving Redis-specific execution into `src/` instead of the Skill package.

Preferred pattern

Keep Redis-specific execution inside `skills/redis-rdb-analysis/scripts/`; keep only reusable helpers in `tools/`.

## Multiple Execution Entrypoints

Problem

Providing multiple scripts or commands that can each run the same analysis.

Why it is harmful

Users and agents cannot tell which path is authoritative, and audit behavior diverges.

Observed or possible example

One script generates reports while another computes validation differently.

Preferred pattern

Use one Skill-owned analysis script and small supporting tools for bounded tasks such as repeatability comparison.
