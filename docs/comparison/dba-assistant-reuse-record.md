# DBA Assistant Reuse Record

## Logic Reused

- The high-version HDT `rdb` parser capability from the old DBA Assistant environment was reused as the required external parser.
- The practical need to handle newer Redis RDB formats was retained.
- The concept of producing a formal report and structured analysis artifacts was retained.

## Logic Intentionally Discarded

- Legacy Python `rdbtools` parsing was discarded because it failed newer RDB value types.
- Built-in fallback parsing was discarded because it could hide parser compatibility differences.
- Environment-variable parser path selection was discarded to keep Phase-01 through Phase-05 behavior explicit and testable.
- Full-filesystem discovery for parser binaries was discarded.

## Directory Structure Not Reused

The old DBA Assistant directory shape was not copied. This project uses an axe Skill-first structure:

- `agents/redis/` for axe agent configuration.
- `skills/redis-rdb-analysis/` for Redis RDB Skill package.
- `tools/` for reusable validation, docx, and audit helpers.
- `docs/phases/` and `docs/reviews/` for phase governance and evidence.

## Parser Strategy Changes

The parser strategy is now explicit:

- HDT3213 `rdb` must be available in `PATH`.
- The project does not install HDT.
- The script validates that PATH `rdb` looks like HDT.
- If parser setup fails, analysis status is `failed`.

## Skill vs Script vs Tools Boundary Changes

- Skill owns LLM behavior, evidence rules, and forbidden behavior.
- Script owns local Redis RDB deterministic execution.
- Tools own reusable validation, docx rendering, and repeatability comparison.
- References and assets own Redis thresholds, wording candidates, profiles, and report outline.

## Why the axe Structure Is Different

axe benefits from an explicit Skill package that the agent can load as its behavior contract. The structure is optimized for LLM guidance, reproducible deterministic outputs, audit evidence, and phase-by-phase review rather than a single monolithic application package.

The old repository was a useful source for parser capability, not a structure to duplicate.
