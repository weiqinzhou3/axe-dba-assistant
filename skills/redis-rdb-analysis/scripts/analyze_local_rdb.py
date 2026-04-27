#!/usr/bin/env python3
"""Skill-owned local Redis RDB analysis entrypoint for Phase-01."""

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.docx_renderer.render_docx import render_docx  # noqa: E402
from tools.validation.validate_result import validate_result  # noqa: E402


VALUE_TYPES = {
    0: "string",
    1: "list",
    2: "set",
    3: "zset",
    4: "hash",
    9: "zipmap",
    10: "ziplist",
    11: "intset",
    12: "zset_ziplist",
    13: "hash_ziplist",
    14: "list_quicklist",
    15: "stream",
}

OPCODE_EXPIRETIME_MS = 0xFC
OPCODE_EXPIRETIME = 0xFD
OPCODE_SELECTDB = 0xFE
OPCODE_EOF = 0xFF
OPCODES_WITH_LENGTH_PAIR = {0xFB}
OPCODES_WITH_STRING = {0xFA}


class RdbReader:
    def __init__(self, data):
        self.data = data
        self.offset = 0

    def remaining(self):
        return len(self.data) - self.offset

    def read_byte(self):
        if self.offset >= len(self.data):
            raise ValueError("unexpected end of RDB")
        value = self.data[self.offset]
        self.offset += 1
        return value

    def read(self, size):
        if self.offset + size > len(self.data):
            raise ValueError("unexpected end of RDB")
        value = self.data[self.offset : self.offset + size]
        self.offset += size
        return value

    def read_length(self):
        first = self.read_byte()
        prefix = (first & 0xC0) >> 6
        if prefix == 0:
            return first & 0x3F, False
        if prefix == 1:
            second = self.read_byte()
            return ((first & 0x3F) << 8) | second, False
        if prefix == 2:
            return struct.unpack(">I", self.read(4))[0], False
        return first & 0x3F, True

    def read_string(self):
        length, encoded = self.read_length()
        if not encoded:
            self.read(length)
            return
        if length == 0:
            self.read(1)
            return
        if length == 1:
            self.read(2)
            return
        if length == 2:
            self.read(4)
            return
        if length == 3:
            compressed_length, _ = self.read_length()
            original_length, _ = self.read_length()
            if original_length < 0:
                raise ValueError("invalid LZF original length")
            self.read(compressed_length)
            return
        raise ValueError("unsupported encoded string type %s" % length)


def parse_rdb(path):
    try:
        return parse_rdb_with_hdt(path)
    except Exception as hdt_exc:  # noqa: BLE001
        parsed = parse_rdb_with_builtin(path)
        parsed.setdefault("parser_warnings", []).append(
            "HDT RDB parser unavailable or failed; used built-in fallback: %s" % hdt_exc
        )
        return parsed


def parse_rdb_with_builtin(path):
    data = path.read_bytes()
    if len(data) < 9 or not data.startswith(b"REDIS"):
        raise ValueError("file does not start with a Redis RDB header")

    reader = RdbReader(data)
    reader.read(9)
    dbs = set()
    type_distribution = Counter()
    keys_with_ttl = 0
    keys_without_ttl = 0
    pending_ttl = False
    warnings = []

    while reader.remaining() > 0:
        marker = reader.read_byte()
        if marker == OPCODE_EOF:
            break
        if marker == OPCODE_SELECTDB:
            db_index, _ = reader.read_length()
            dbs.add(db_index)
            continue
        if marker == OPCODE_EXPIRETIME_MS:
            reader.read(8)
            pending_ttl = True
            continue
        if marker == OPCODE_EXPIRETIME:
            reader.read(4)
            pending_ttl = True
            continue
        if marker in OPCODES_WITH_LENGTH_PAIR:
            reader.read_length()
            reader.read_length()
            continue
        if marker in OPCODES_WITH_STRING:
            reader.read_string()
            reader.read_string()
            continue

        value_type = VALUE_TYPES.get(marker, "unknown_%s" % marker)
        reader.read_string()
        skip_value(reader, marker)
        type_distribution[value_type] += 1
        if pending_ttl:
            keys_with_ttl += 1
        else:
            keys_without_ttl += 1
        pending_ttl = False

    total_keys = sum(type_distribution.values())
    return {
        "total_keys": total_keys,
        "db_count": len(dbs) if total_keys else 0,
        "type_distribution": dict(type_distribution),
        "ttl": {
            "keys_with_ttl": keys_with_ttl,
            "keys_without_ttl": keys_without_ttl,
        },
        "source": "analysis.rdb_parser",
        "parser_warnings": warnings,
    }


def parse_rdb_with_hdt(path):
    binary = resolve_hdt_rdb_binary()
    if binary is None:
        raise FileNotFoundError(
            "HDT3213/rdb binary not found. Set DBA_ASSISTANT_HDT_RDB_BIN or install the original rdb CLI."
        )

    with tempfile.TemporaryDirectory(prefix="axe-rdb-hdt-", dir="/tmp") as temp_dir:
        output_path = Path(temp_dir) / "dump.json"
        cmd = [str(binary), "-c", "json", "-o", str(output_path), str(path)]
        completed = subprocess.run(
            cmd,
            check=False,
            text=True,
            capture_output=True,
            timeout=float(os.getenv("AXE_RDB_HDT_TIMEOUT_SECONDS", "300")),
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise RuntimeError(
                "HDT rdb command failed with exit code %s%s"
                % (completed.returncode, ": " + detail if detail else "")
            )
        if not output_path.exists():
            raise RuntimeError("HDT rdb command did not create JSON output")

        dbs = set()
        type_distribution = Counter()
        keys_with_ttl = 0
        keys_without_ttl = 0
        warnings = []

        with output_path.open("r", encoding="utf-8") as handle:
            for obj in iter_json_array_objects(handle):
                normalized = normalize_hdt_json_object(obj)
                if normalized is None:
                    continue
                db_value = obj.get("db")
                if isinstance(db_value, int):
                    dbs.add(db_value)
                type_distribution[str(normalized["key_type"])] += 1
                if normalized["has_expiration"]:
                    keys_with_ttl += 1
                else:
                    keys_without_ttl += 1

    total_keys = sum(type_distribution.values())
    return {
        "total_keys": total_keys,
        "db_count": len(dbs) if total_keys else 0,
        "type_distribution": dict(type_distribution),
        "ttl": {
            "keys_with_ttl": keys_with_ttl,
            "keys_without_ttl": keys_without_ttl,
        },
        "source": "analysis.hdt_rdb_cli",
        "parser_strategy": "HdtRdbCli",
        "parser_binary": str(binary),
        "parser_warnings": warnings,
    }


def normalize_hdt_json_object(obj):
    if not isinstance(obj, dict):
        return None
    key_name = obj.get("key")
    key_type = str(obj.get("type", ""))
    if not key_name or key_type in {"aux", "functions"}:
        return None
    expiration = obj.get("expiration")
    return {
        "key_name": str(key_name),
        "key_type": key_type,
        "size_bytes": int(obj.get("size", 0)),
        "has_expiration": expiration is not None,
    }


def resolve_hdt_rdb_binary():
    candidates = []
    configured = os.getenv("DBA_ASSISTANT_HDT_RDB_BIN")
    if configured:
        candidates.append(Path(configured).expanduser())

    candidates.append(REPO_ROOT / ".tools/bin/rdb")
    candidates.append(Path("/Users/zqw/Desktop/Project/dba_assistant/.tools/bin/rdb"))

    path_candidate = shutil.which("rdb")
    if path_candidate:
        candidates.append(Path(path_candidate))

    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved.exists() and looks_like_hdt_rdb(resolved):
            return resolved
    return None


def looks_like_hdt_rdb(candidate):
    try:
        completed = subprocess.run(
            [str(candidate), "-h"],
            check=False,
            text=True,
            capture_output=True,
            timeout=10,
        )
    except OSError:
        return False
    except subprocess.TimeoutExpired:
        return False

    output = "\n".join(part for part in [completed.stdout, completed.stderr] if part)
    markers = (
        "Usage of",
        "command for rdb: json",
        "-show-global-meta",
        "-max-depth",
    )
    return all(marker in output for marker in markers)


def iter_json_array_objects(handle):
    decoder = json.JSONDecoder()
    buffer = ""
    in_array = False
    array_complete = False

    while True:
        chunk = handle.read(65536)
        if chunk:
            buffer += chunk
        elif not buffer.strip():
            break

        position = 0
        length = len(buffer)
        while position < length:
            while position < length and buffer[position].isspace():
                position += 1
            if position >= length:
                break
            token = buffer[position]
            if not in_array:
                if token != "[":
                    if chunk:
                        break
                    raise ValueError("Invalid HDT JSON payload: expected '[' at array start.")
                in_array = True
                position += 1
                continue
            if token == ",":
                position += 1
                continue
            if token == "]":
                array_complete = True
                position += 1
                while position < length and buffer[position].isspace():
                    position += 1
                buffer = buffer[position:]
                position = 0
                length = len(buffer)
                break
            try:
                obj, end = decoder.raw_decode(buffer, position)
            except json.JSONDecodeError:
                if chunk:
                    break
                raise
            if not isinstance(obj, dict):
                raise ValueError("Invalid HDT JSON payload: expected JSON objects in array.")
            yield obj
            position = end
        buffer = buffer[position:]
        if array_complete:
            break
        if not chunk and buffer.strip():
            raise ValueError("Invalid HDT JSON payload: unterminated JSON array.")


def skip_value(reader, value_type):
    if value_type == 0:
        reader.read_string()
        return
    if value_type in {1, 2}:
        length, _ = reader.read_length()
        for _ in range(length):
            reader.read_string()
        return
    if value_type == 3:
        length, _ = reader.read_length()
        for _ in range(length):
            reader.read_string()
            reader.read_string()
        return
    if value_type == 4:
        length, _ = reader.read_length()
        for _ in range(length):
            reader.read_string()
            reader.read_string()
        return
    if value_type in {9, 10, 11, 12, 13, 14, 15}:
        reader.read_string()
        return
    raise ValueError("unsupported RDB value type: %s" % value_type)


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def base_result(rdb_path, sha256_value, status):
    return {
        "status": status,
        "input": {
            "rdb_path": str(rdb_path),
            "sha256": sha256_value,
            "source": "input.rdb_path",
        },
        "summary": {
            "total_keys": 0,
            "db_count": 0,
            "type_distribution": {},
            "ttl": {
                "keys_with_ttl": 0,
                "keys_without_ttl": 0,
            },
            "source": "analysis.rdb_parser",
        },
        "findings": [],
        "validation": {
            "mechanical": {"status": "fail", "details": []},
            "logical": {"status": "skipped", "details": []},
            "sufficiency": {"status": "insufficient", "details": []},
        },
        "uncertainties": [],
        "errors": [],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_summary_text(result):
    summary = result["summary"]
    validation = result["validation"]
    findings = result.get("findings") or []
    uncertainties = result.get("uncertainties") or []
    errors = result.get("errors") or []

    return "\n".join(
        [
            "1. Analysis Target",
            "- RDB file: %s" % result["input"]["rdb_path"],
            "- SHA256: %s" % (result["input"]["sha256"] or "unavailable"),
            "- Analysis status: %s" % result["status"],
            "",
            "2. Basic Statistics",
            "- DB count: %s" % summary["db_count"],
            "- Total keys: %s" % summary["total_keys"],
            "- Type distribution: %s" % json.dumps(summary["type_distribution"], sort_keys=True),
            "- TTL overview: keys_with_ttl=%s, keys_without_ttl=%s"
            % (summary["ttl"]["keys_with_ttl"], summary["ttl"]["keys_without_ttl"]),
            "",
            "3. Validation Result",
            "- Mechanical validation: %s" % validation["mechanical"]["status"],
            "- Logical validation: %s" % validation["logical"]["status"],
            "- Sufficiency validation: %s" % validation["sufficiency"]["status"],
            "",
            "4. Risks and Uncertainties",
            "- Findings: %s" % (json.dumps(findings, ensure_ascii=False) if findings else "none"),
            "- Uncertainties: %s"
            % (json.dumps(uncertainties, ensure_ascii=False) if uncertainties else "none"),
            "- Deferred items: full audit trace, rich big-key rules, advanced docx layout",
            "- Errors: %s" % (json.dumps(errors, ensure_ascii=False) if errors else "none"),
            "",
        ]
    )


def build_docx_sections(result):
    summary = result["summary"]
    validation = result["validation"]
    return [
        {
            "heading": "Analysis Target",
            "lines": [
                "Analysis time: %s" % result.get("generated_at", ""),
                "RDB file path: %s" % result["input"]["rdb_path"],
                "SHA256 fingerprint: %s" % (result["input"]["sha256"] or "unavailable"),
                "Analysis status: %s" % result["status"],
            ],
        },
        {
            "heading": "Basic Statistics",
            "lines": [
                "DB count: %s" % summary["db_count"],
                "Total keys: %s" % summary["total_keys"],
                "Type distribution: %s" % json.dumps(summary["type_distribution"], sort_keys=True),
                "TTL: keys_with_ttl=%s, keys_without_ttl=%s"
                % (summary["ttl"]["keys_with_ttl"], summary["ttl"]["keys_without_ttl"]),
            ],
        },
        {
            "heading": "Validation Results",
            "lines": [
                "Mechanical validation: %s" % validation["mechanical"]["status"],
                "Logical validation: %s" % validation["logical"]["status"],
                "Sufficiency validation: %s" % validation["sufficiency"]["status"],
            ],
        },
        {
            "heading": "Risks, Uncertainties, and Phase-01 Limitations",
            "lines": [
                "Findings: %s"
                % (json.dumps(result.get("findings"), ensure_ascii=False) if result.get("findings") else "none"),
                "Uncertainties: %s"
                % (
                    json.dumps(result.get("uncertainties"), ensure_ascii=False)
                    if result.get("uncertainties")
                    else "none"
                ),
                "Phase-01 limitations: local RDB only; no remote Redis, SSH, MySQL staging, multi-RDB aggregation, or final delivery-grade docx styling.",
            ],
        },
    ]


def write_outputs(output_dir, result, user_request):
    output_dir.mkdir(parents=True, exist_ok=True)
    input_dir = output_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    (input_dir / "user_request.txt").write_text(user_request or "", encoding="utf-8")
    (input_dir / "rdb.fingerprint").write_text(
        result["input"]["sha256"] or "unavailable", encoding="utf-8"
    )

    (output_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "summary.txt").write_text(build_summary_text(result), encoding="utf-8")
    render_docx(
        output_dir / "report.docx",
        "Redis RDB Analysis Report",
        build_docx_sections(result),
    )


def default_output_dir():
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("/tmp/axe_rdb_assistant") / run_id


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Analyze a local Redis RDB file.")
    parser.add_argument("--rdb", required=True, help="Local Redis RDB file path.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory. Defaults to /tmp/axe_rdb_assistant/<run_id>/.",
    )
    parser.add_argument("--user-request", default="", help="Original user request text.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    rdb_path = Path(args.rdb).expanduser()
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else default_output_dir()

    if not rdb_path.exists() or not rdb_path.is_file():
        result = base_result(rdb_path, "", "failed")
        result["errors"].append("RDB file does not exist or is not a file: %s" % rdb_path)
        result["validation"] = validate_result(result)
        result["validation"]["mechanical"]["status"] = "fail"
        result["validation"]["mechanical"]["details"].append("input file is missing")
        write_outputs(output_dir, result, args.user_request)
        print(str(output_dir))
        return 1

    sha256_value = sha256_file(rdb_path)
    result = base_result(rdb_path, sha256_value, "success")

    try:
        parsed_summary = parse_rdb(rdb_path)
        warnings = parsed_summary.pop("parser_warnings", [])
        result["summary"] = parsed_summary
        result["uncertainties"].extend(warnings)
    except Exception as exc:
        result["status"] = "partial"
        result["errors"].append("RDB parser could not complete full parsing: %s" % exc)
        result["uncertainties"].append(
            "Only file existence and SHA256 fingerprint are verified; key statistics are unavailable."
        )

    result["validation"] = validate_result(result)
    if result["status"] == "partial":
        result["validation"]["sufficiency"]["status"] = "insufficient"
        result["validation"]["sufficiency"]["details"].append(
            "RDB parser did not provide enough data for complete statistics."
        )

    write_outputs(output_dir, result, args.user_request)
    print(str(output_dir))
    return 0 if result["status"] in {"success", "partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
