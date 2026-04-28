# Redis RDB Analysis Skill

## Task Definition

Use this Skill when the user asks to analyze a local Redis RDB file and produce:

- a concise terminal answer;
- a structured JSON result;
- a minimal docx report.

Phase-01 through Phase-04 support **local Redis RDB file analysis only**.

The Skill guides the LLM. Deterministic parsing, arithmetic, file checks, SHA256 calculation, HDT availability checks, validation, and output generation must be delegated to the Skill script. `result.json` is the source of truth for every status, statistic, file path, and validation conclusion.

The Skill script is:

```text
skills/redis-rdb-analysis/scripts/analyze_local_rdb.py
```

Do not hard-code user-specific absolute repository paths in this Skill.

The RDB file path supplied by the user may be an absolute path, for example:

```text
/tmp/dump.rdb
```

Absolute RDB input paths are allowed and should be passed to the script unchanged.

---

## Core Execution Rule

For Phase-01 through Phase-04, the LLM should directly call only one execution entrypoint:

```bash
python3 skills/redis-rdb-analysis/scripts/analyze_local_rdb.py \
  --rdb "<rdb_path>" \
  --user-request "<original user request>"
```

Do not run extra pre-check commands before calling the script.

Do not run:

```bash
pwd
test -f skills/redis-rdb-analysis/scripts/analyze_local_rdb.py
which rdb
rdb -h
```

The Skill script is responsible for checking:

- whether the RDB file exists;
- whether HDT `rdb` is available in PATH;
- whether HDT execution succeeds;
- whether outputs can be generated;
- whether the result is success, partial, or failed.

---

## Parser Requirement

Phase-01 through Phase-04 require the HDT3213 `rdb` CLI.

The runtime environment must have `rdb` available in PATH before analysis can succeed.

The project does **not** install HDT.

The LLM must not attempt to install HDT, download HDT, search for HDT, or run offline installation logic.

The Skill script must use the `rdb` command from PATH.

Do not use:

- legacy Python `rdbtools`;
- a built-in fallback parser;
- `.tools/bin/rdb`;
- old DBA Assistant project paths;
- environment-variable-provided absolute parser paths;
- full-filesystem discovery to find `rdb`.

If `rdb` is missing, the script must report failure in `result.json` and `summary.txt`. The assistant should then tell the user to install HDT3213 `rdb` manually and ensure `rdb` is available in PATH.

---

## Supported Inputs

Supported:

- A local Redis RDB file path supplied by the user.
- A request for summary, JSON, and docx outputs.
- Optional natural-language context in Chinese or English.

Required input:

- One local RDB file path.

Examples:

```text
请分析 /tmp/dump.rdb
请分析本地 RDB 文件 /data/redis/dump.rdb
Please analyze /tmp/dump.rdb
```

The RDB path may be absolute or relative.

If the path starts with `/`, treat it as an absolute local filesystem path and pass it unchanged.

If no local RDB path is present, ask the user for the path before running analysis.

---

## Intent Recognition Rules

Treat the request as Redis RDB analysis when it mentions any of the following:

- Redis RDB;
- dump.rdb;
- `.rdb` file;
- Redis key analysis;
- Redis memory analysis;
- Redis RDB report;
- Redis RDB summary.

Extract only local filesystem paths.

Do not infer or use:

- remote Redis hosts;
- SSH paths;
- object storage URLs;
- MySQL staging inputs;
- Kubernetes paths;
- container paths unless the user explicitly says the file is already available locally.

Phase-01 through Phase-04 only support analyzing a local file that is directly accessible to the current machine.

---

## Local RDB Analysis Flow

Follow this flow:

1. Identify the local RDB path from the user request.
2. If the path is missing, ask the user for it.
3. Call the Skill script directly:

   ```bash
   python3 skills/redis-rdb-analysis/scripts/analyze_local_rdb.py \
     --rdb "<rdb_path>" \
     --user-request "<original user request>"
   ```

4. The script prints the output directory, normally:

   ```text
   /tmp/axe_rdb_assistant/<run_id>
   ```

5. Read `summary.txt` and `result.json` from that output directory using `run_command cat`, not `read_file`.

6. Respond using only verified facts, explicit inferences, listed findings, listed uncertainties, and listed errors from those output files.

Do not perform repository-root checks, HDT checks, or RDB existence checks in the LLM. The script owns those checks.

---

## Script Usage Rules

Run the Skill script through the axe runtime command capability.

Use this command pattern:

```bash
python3 skills/redis-rdb-analysis/scripts/analyze_local_rdb.py \
  --rdb "<local-rdb-path>" \
  --user-request "<original user request>"
```

Examples:

```bash
python3 skills/redis-rdb-analysis/scripts/analyze_local_rdb.py \
  --rdb "/tmp/dump.rdb" \
  --user-request "请分析/tmp/dump.rdb"
```

```bash
python3 skills/redis-rdb-analysis/scripts/analyze_local_rdb.py \
  --rdb "/data/redis/dump.rdb" \
  --user-request "请分析本地 RDB 文件 /data/redis/dump.rdb"
```

The LLM should directly call only this Skill script in Phase-01 through Phase-04.

The script may internally call reusable tools under:

```text
tools/validation/
tools/docx_renderer/
```

The LLM must not directly call those reusable tools in Phase-01 through Phase-04.

Do not ask the LLM to compute, repair, or infer deterministic totals:

- Redis key totals;
- type totals;
- TTL totals;
- SHA256 fingerprints;
- parser statistics;
- docx layout;
- validation arithmetic.

These are deterministic actions and must be done by the script.

---

## Phase-03 Resource Boundaries

Static Redis domain material belongs in Skill resources, not in this operating manual.

Use these files as references when their data is present in generated outputs:

- `references/redis_bigkey_thresholds.yaml`
- `references/redis_risk_levels.yaml`
- `references/redis_recommendations.yaml`
- `references/redis_type_notes.yaml`
- `references/ttl_risk_rules.yaml`
- `references/profiles/default.yaml`
- `references/profiles/rcs.yaml`
- `references/profiles/concise.yaml`
- `assets/report_outline.yaml`

Profiles describe response preferences only. They must not change parser selection, file access rules, HDT requirements, validation rules, or execution safety boundaries.

Recommendations and thresholds are candidates. Emit them only when `result.json` findings, validation, and sources support the conclusion.

---

## Output Requirements

The script writes outputs under:

```text
/tmp/axe_rdb_assistant/<run_id>/
```

The required outputs are:

```text
summary.txt
result.json
report.docx
input/user_request.txt
input/rdb.fingerprint
audit/meta.json
audit/stdout.log
audit/stderr.log
audit/axe_verbose.log
audit/trace.json
```

Important axe tool rule:

Do not use `read_file` for files under `/tmp/axe_rdb_assistant/<run_id>/`.

Some axe runtimes reject absolute paths for `read_file`.

Use `run_command cat` instead:

```bash
cat /tmp/axe_rdb_assistant/<run_id>/summary.txt 2>&1
```

```bash
cat /tmp/axe_rdb_assistant/<run_id>/result.json 2>&1
```

If `cat` fails, report the failure and include the output directory.

---

## Audit and Repeatability

Phase-04 writes an audit archive under the same output directory:

```text
/tmp/axe_rdb_assistant/<run_id>/audit/
```

Use `audit/meta.json` for run metadata such as run id, command, workdir, status, exit code, parser strategy, parser binary, and RDB SHA256.

Use `tools/audit/compare_repeated_runs.py` only for repeatability checks across generated `result.json` files. It compares stable fields and allows timestamps, duration, run id, and output directory to differ.

The direct Skill script does not fabricate axe model traces. If axe verbose/json trace is unavailable, `audit/axe_verbose.log` and `audit/trace.json` record that limitation.

---

## Required Result Fields

The `result.json` file must be treated as the source of truth.

Phase-02 requires this stable top-level contract:

```json
{
  "schema_version": "phase-02.v1",
  "status": "success | partial | failed",
  "generated_at": "...",
  "parser_required": true,
  "parser_strategy": "HdtRdbCli",
  "parser_binary": "/path/to/rdb or unavailable",
  "parser_warnings": [],
  "input": {
    "rdb_path": "/tmp/dump.rdb",
    "sha256": "...",
    "source": "input.rdb_path"
  },
  "summary": {
    "total_keys": 0,
    "db_count": 0,
    "type_distribution": {},
    "ttl": {
      "keys_with_ttl": 0,
      "keys_without_ttl": 0
    },
    "source": "analysis.hdt_rdb_cli"
  },
  "findings": [],
  "validation": {
    "mechanical": {
      "status": "pass | fail",
      "details": []
    },
    "logical": {
      "status": "pass | fail | skipped",
      "details": []
    },
    "sufficiency": {
      "status": "sufficient | insufficient",
      "details": []
    }
  },
  "uncertainties": [],
  "errors": [],
  "outputs": {
    "output_dir": "/tmp/axe_rdb_assistant/<run_id>",
    "summary_txt": {
      "path": "/tmp/axe_rdb_assistant/<run_id>/summary.txt",
      "exists": true
    },
    "result_json": {
      "path": "/tmp/axe_rdb_assistant/<run_id>/result.json",
      "exists": true
    },
    "report_docx": {
      "path": "/tmp/axe_rdb_assistant/<run_id>/report.docx",
      "exists": true
    }
  }
}
```

Strict status semantics:

| Status | Interpretation |
|---|---|
| `success` | HDT parser ran successfully, mechanical/logical validation passed, and available data is sufficient for the request. |
| `partial` | Some data exists, but coverage or validation is incomplete; label the response as partial. |
| `failed` | Analysis did not complete; never summarize it as success. |

If `rdb` is missing, expected result state is:

```text
status = failed
parser_required = true
parser_strategy = HdtRdbCli
parser_binary = unavailable or null
validation.mechanical.status = fail
validation.logical.status = skipped
validation.sufficiency.status = insufficient
```

If `status` is `failed`, the response must start from the failure state and only mention verified artifacts such as the RDB path, SHA256 if available, errors, validation details, and generated output paths.

If `status` is `partial`, the response must explicitly say the analysis is partial and must not present missing statistics or unsupported conclusions as verified.

---

## Assistant Response Requirements

The assistant response should include:

- analysis status;
- output directory;
- RDB file path;
- SHA256;
- parser strategy;
- parser binary;
- key statistics from `summary.txt` or `result.json`;
- validation status;
- findings;
- uncertainties;
- errors;
- generated files.

When the analysis succeeds, say it succeeded.

When the analysis fails, say it failed.

When the analysis is partial, say it is partial.

Do not present partial or failed analysis as full success.

---

## Evidence and Source Requirements

Every conclusive statement must be grounded in:

```text
result.json
summary.txt
```

Use these categories:

- Verified fact: directly present in output files.
- Inference: derived by the LLM from output files and explicitly labeled; do not use inferences to replace deterministic totals.
- Risk: present in `findings` or clearly derived from references.
- Uncertainty: present in `uncertainties`, `errors`, or validation details.

Respect source traceability:

- `input.source` and `summary.source` identify the source for core facts.
- Each object in `findings` should carry `source`.
- Each object in `uncertainties` should carry `source` when applicable.
- If a conclusion-like statement has no source, label it as an inference or omit it.

Do not fabricate:

- key names;
- key counts;
- DB counts;
- TTL counts;
- risk levels;
- parser details;
- output file paths;
- recommendations.

If the output file does not contain a fact, do not claim it as verified.

---

## Validation Requirements

Check the validation block in `result.json` before responding.

The three validation layers are:

| Layer | Meaning |
|---|---|
| mechanical | file existence, parser availability, parser execution, output generation |
| logical | arithmetic consistency such as type totals and TTL totals |
| sufficiency | whether the available data is enough to answer the user request |

If any layer fails or is insufficient, report the status clearly.

If `rdb` is missing, the analysis is failed, not partial success.

If HDT execution fails, the analysis is failed, and no fallback parser should be used.

When the user asks for a formal report, verify `outputs.report_docx.exists` before saying the report was generated.

When the user asks for TTL analysis, use only `summary.ttl` and validation details. Do not recompute TTL totals in the LLM.

When the user asks for Big Key risk analysis, use `references/redis_bigkey_thresholds.yaml` only as reference material. Only report Big Key data if it appears in `result.json`; otherwise label it as deferred or insufficient.

---

## Uncertainty Handling

If parsing is incomplete, unsupported, or failed:

1. Report the status as `failed` or `partial`.
2. State what was verified.
3. State what was not verified.
4. Keep recommendations conservative.
5. Do not invent Redis risks.

If the script returns non-zero but output files exist, read them using `run_command cat` and summarize the failure.

If the script returns non-zero and output files do not exist, report the command failure and ask the user to inspect the local environment.

---

## Forbidden Behaviors

Do not:

- run `pwd` unless the user explicitly asks for debugging;
- run `test -f` repository-root checks before analysis;
- run `which rdb` or `rdb -h` before analysis;
- install HDT;
- download HDT;
- search the whole filesystem for HDT;
- use legacy Python `rdbtools`;
- use a built-in fallback parser;
- use `.tools/bin/rdb`;
- use old DBA Assistant project paths;
- use environment-variable-provided absolute parser paths;
- hard-code user-specific repository paths;
- run full-filesystem discovery commands such as `find /`;
- connect to remote Redis;
- use SSH to fetch RDB files;
- trigger `BGSAVE`;
- use MySQL staging;
- aggregate multiple RDB files;
- introduce MCP;
- introduce sub-agents;
- patch or wrap axe;
- call `tools/validation/` or `tools/docx_renderer/` directly from the LLM in Phase-01 through Phase-04;
- compute Redis statistics inside the LLM;
- fabricate statistics, keys, risks, parser details, or output files;
- hide failures or uncertainties;
- use `read_file` to read `/tmp/axe_rdb_assistant/<run_id>/...` absolute paths.
