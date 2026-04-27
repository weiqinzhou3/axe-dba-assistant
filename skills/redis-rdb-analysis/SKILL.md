# Redis RDB Analysis Skill

## Task Definition

Use this Skill when the user asks to analyze a local Redis RDB file and produce a concise terminal answer, structured JSON result, and docx report.

Phase-01 is local-file only. The Skill guides the LLM. Deterministic parsing, arithmetic, file checks, SHA256 calculation, validation, and output generation must be delegated to the Skill script.

The Skill script uses the original DBA Assistant RDB analysis toolchain when available: HDT3213 `rdb` CLI first, then a built-in fallback only if HDT is unavailable or fails. This avoids relying on legacy Python `rdbtools` for high-version Redis RDB files.

## Supported Inputs

Supported:

- A local Redis RDB file path supplied by the user.
- A request for summary, JSON, and docx outputs.
- Optional natural-language context in Chinese or English.

Required input:

- One local RDB file path.

If no local RDB path is present, ask the user for the path before running analysis.

## Intent Recognition Rules

Treat the request as Redis RDB analysis when it mentions Redis RDB, dump.rdb, an `.rdb` file, Redis memory/key analysis, or asks for RDB summary/report output.

Extract only local filesystem paths. Do not infer remote hosts, SSH paths, object storage URLs, or MySQL staging inputs as supported Phase-01 inputs.

## Local RDB Analysis Flow

1. Identify the local RDB path from the user request.
2. If the path is missing, ask for it.
3. Call `/Users/zqw/Desktop/Project/axe-dba-assistant/skills/redis-rdb-analysis/scripts/analyze_local_rdb.py`.
4. Read `summary.txt` and `result.json` from the output directory reported by the script.
5. Respond using only verified facts, explicit inferences, and listed uncertainties from those files.

## Script Usage Rules

Run the Skill script through the axe runtime command capability:

```bash
python3 /Users/zqw/Desktop/Project/axe-dba-assistant/skills/redis-rdb-analysis/scripts/analyze_local_rdb.py \
  --rdb "/absolute/or/relative/path/to/dump.rdb" \
  --user-request "<original user request>"
```

The LLM should directly call only this Skill script in Phase-01. The script may call reusable tools under `tools/validation/` and `tools/docx_renderer/`.

Do not ask the LLM to compute Redis statistics, SHA256 fingerprints, TTL totals, type totals, or docx layout directly.

For high-version RDB formats, do not reinterpret parser errors as business risk. Report parser strategy and uncertainties from `result.json`.

## Output Requirements

The script writes outputs under `/tmp/axe_rdb_assistant/<run_id>/` by default, or a caller-specified output directory:

- `summary.txt`
- `result.json`
- `report.docx`
- `input/user_request.txt`
- `input/rdb.fingerprint`

The assistant response should include:

- analysis status;
- output directory;
- RDB file path and SHA256;
- key statistics available in `summary.txt`;
- validation status;
- findings, uncertainties, and deferred Phase-01 items.

## Evidence and Source Requirements

Every conclusive statement must be grounded in `result.json` or `summary.txt`.

Use these categories:

- Verified fact: directly present in output files.
- Inference: derived by the LLM from output files and explicitly labeled.
- Risk: present in `findings` or clearly derived from references.
- Uncertainty: present in `uncertainties`, `errors`, or validation details.

Do not fabricate key names, key counts, DB counts, TTL counts, risk levels, or recommendations.

## Validation Requirements

Check the validation block in `result.json` before responding:

- `mechanical`: file existence, parsing attempt, generated outputs, and exit status.
- `logical`: basic consistency such as type totals and TTL totals.
- `sufficiency`: whether the available data is enough to answer the request.

If any layer fails or is insufficient, state that the analysis is failed or partial. Do not present partial analysis as full success.

## Uncertainty Handling

If parsing is partial, unsupported, or incomplete:

- Report the status as `partial` or `failed`.
- State what was verified.
- State what was not verified.
- Keep recommendations conservative.

If the script returns non-zero, read `result.json` and `summary.txt` when present, then report the failure and the output directory.

## Forbidden Behaviors

Do not:

- run full-filesystem discovery commands such as `find /`;
- connect to remote Redis;
- use SSH to fetch RDB files;
- trigger `BGSAVE`;
- use MySQL staging;
- aggregate multiple RDB files;
- introduce MCP or sub-agents;
- patch or wrap axe;
- call `tools/validation/` or `tools/docx_renderer/` directly from the LLM in Phase-01;
- fabricate statistics, keys, risks, or output files;
- hide failures or uncertainties.
