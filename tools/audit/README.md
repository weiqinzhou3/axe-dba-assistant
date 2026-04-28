# Audit Tools

`compare_repeated_runs.py` compares stable fields across at least three generated `result.json` files.

Usage:

```bash
python3 tools/audit/compare_repeated_runs.py \
  --result /tmp/axe_rdb_assistant/run-1/result.json \
  --result /tmp/axe_rdb_assistant/run-2/result.json \
  --result /tmp/axe_rdb_assistant/run-3/result.json \
  --output /tmp/axe_rdb_assistant/repeatability.json
```

The Redis RDB Skill script writes per-run audit files under:

```text
/tmp/axe_rdb_assistant/<run_id>/audit/
```

Required files:

- `meta.json`
- `stdout.log`
- `stderr.log`
- `axe_verbose.log`
- `trace.json`

Stable fields:

- `input.sha256`
- `summary.total_keys`
- `summary.db_count`
- `summary.type_distribution`
- `summary.ttl.keys_with_ttl`
- `summary.ttl.keys_without_ttl`
- `parser_strategy`

Volatile fields such as timestamps, duration, run id, and output directories are allowed to differ.

`axe_verbose.log` and `trace.json` document trace capture limitations when the Skill script is run directly outside axe model execution.
