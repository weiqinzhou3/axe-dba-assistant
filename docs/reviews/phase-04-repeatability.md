# Phase-04 Repeatability

## Procedure

The same high-version Redis RDB fixture was analyzed three times with the same command shape and `default` profile.

Run outputs:

- `/tmp/axe_rdb_assistant/phase04-repeat-1/result.json`
- `/tmp/axe_rdb_assistant/phase04-repeat-2/result.json`
- `/tmp/axe_rdb_assistant/phase04-repeat-3/result.json`

Comparison command:

```bash
python3 tools/audit/compare_repeated_runs.py \
  --result /tmp/axe_rdb_assistant/phase04-repeat-1/result.json \
  --result /tmp/axe_rdb_assistant/phase04-repeat-2/result.json \
  --result /tmp/axe_rdb_assistant/phase04-repeat-3/result.json \
  --output /tmp/axe_rdb_assistant/phase04-repeatability.json
```

## Result

`/tmp/axe_rdb_assistant/phase04-repeatability.json` returned `status: pass` for three compared runs.

Stable fields confirmed:

- `input.sha256`: `cb3dff9205feccd3adccabebad65fdae345d055ad5cff594ff5925352333053c`
- `summary.total_keys`: `1`
- `summary.db_count`: `1`
- `summary.type_distribution`: `{"hash": 1}`
- `summary.ttl.keys_with_ttl`: `0`
- `summary.ttl.keys_without_ttl`: `1`
- `parser_strategy`: `HdtRdbCli`

Volatile fields allowed to differ:

- `run_id`
- `generated_at`
- `duration_ms`
- `outputs.output_dir`
- `audit.meta.started_at`
- `audit.meta.finished_at`

## Trace Limitation

Direct `analyze_local_rdb.py` execution does not run through axe model execution, so it cannot produce real axe token, latency, or tool-call trace data. The run archive records this limitation in `audit/axe_verbose.log` and `audit/trace.json` instead of fabricating trace fields.
