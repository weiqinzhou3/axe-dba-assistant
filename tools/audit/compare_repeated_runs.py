#!/usr/bin/env python3
"""Compare stable fields across repeated Redis RDB analysis runs."""

import argparse
import json
import sys
from pathlib import Path


STABLE_FIELD_PATHS = [
    ("input.sha256", ["input", "sha256"]),
    ("summary.total_keys", ["summary", "total_keys"]),
    ("summary.db_count", ["summary", "db_count"]),
    ("summary.type_distribution", ["summary", "type_distribution"]),
    ("summary.ttl.keys_with_ttl", ["summary", "ttl", "keys_with_ttl"]),
    ("summary.ttl.keys_without_ttl", ["summary", "ttl", "keys_without_ttl"]),
    ("parser_strategy", ["parser_strategy"]),
]


VOLATILE_FIELDS = [
    "run_id",
    "generated_at",
    "duration_ms",
    "outputs.output_dir",
    "audit.meta.started_at",
    "audit.meta.finished_at",
]


def read_result(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def nested_get(data, path):
    current = data
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def compare_results(paths):
    results = [read_result(path) for path in paths]
    stable_fields = {}
    mismatches = []
    for label, path in STABLE_FIELD_PATHS:
        values = [nested_get(result, path) for result in results]
        first_value = values[0] if values else None
        is_stable = all(value == first_value for value in values)
        stable_fields[label] = {
            "status": "stable" if is_stable else "mismatch",
            "values": values,
        }
        if not is_stable:
            mismatches.append(label)

    return {
        "schema_version": "phase-04.repeatability.v1",
        "status": "pass" if not mismatches else "fail",
        "compared_runs": len(paths),
        "result_paths": [str(Path(path)) for path in paths],
        "stable_fields": stable_fields,
        "mismatches": mismatches,
        "volatile_fields_allowed_to_differ": VOLATILE_FIELDS,
    }


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Compare repeated Redis RDB analysis result.json files.")
    parser.add_argument(
        "--result",
        action="append",
        required=True,
        help="Path to a result.json file. Provide at least three.",
    )
    parser.add_argument("--output", default=None, help="Optional JSON output path.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    if len(args.result) < 3:
        print("at least three --result paths are required", file=sys.stderr)
        return 2

    comparison = compare_results(args.result)
    payload = json.dumps(comparison, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if comparison["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
