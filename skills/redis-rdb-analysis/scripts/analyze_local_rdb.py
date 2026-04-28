#!/usr/bin/env python3
"""Skill-owned local Redis RDB analysis entrypoint for Phase-01 through Phase-04."""

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = Path(__file__).resolve().parents[1]
REFERENCES_DIR = SKILL_ROOT / "references"
ASSETS_DIR = SKILL_ROOT / "assets"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.docx_renderer.render_docx import render_docx  # noqa: E402
from tools.validation.validate_result import validate_result  # noqa: E402


def resource_path_label(path):
    return str(path.relative_to(SKILL_ROOT))


def load_yaml_resource(path):
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise RuntimeError("resource is not a YAML object: %s" % resource_path_label(path))
    return data


def load_profile(profile_name):
    profile_path = REFERENCES_DIR / "profiles" / ("%s.yaml" % profile_name)
    if not profile_path.exists():
        raise FileNotFoundError("profile not found: %s" % profile_name)
    profile = load_yaml_resource(profile_path)
    profile["name"] = profile.get("name") or profile_name
    profile["source"] = resource_path_label(profile_path)
    return profile


def load_report_outline():
    outline_path = ASSETS_DIR / "report_outline.yaml"
    if not outline_path.exists():
        raise FileNotFoundError("report outline not found: %s" % resource_path_label(outline_path))
    outline = load_yaml_resource(outline_path)
    sections = outline.get("sections")
    if not isinstance(sections, list) or not sections:
        raise RuntimeError("report outline has no sections: %s" % resource_path_label(outline_path))
    return outline


def collect_resource_metadata(report_outline, warnings):
    required_references = [
        REFERENCES_DIR / "redis_bigkey_thresholds.yaml",
        REFERENCES_DIR / "redis_risk_levels.yaml",
        REFERENCES_DIR / "redis_recommendations.yaml",
        REFERENCES_DIR / "redis_type_notes.yaml",
        REFERENCES_DIR / "ttl_risk_rules.yaml",
    ]
    missing_required = [resource_path_label(path) for path in required_references if not path.exists()]
    if missing_required:
        raise FileNotFoundError("required reference files are missing: %s" % ", ".join(missing_required))

    optional_assets = [
        ASSETS_DIR / "examples" / "summary_example.txt",
        ASSETS_DIR / "examples" / "result_example.json",
    ]
    for path in optional_assets:
        if not path.exists():
            warnings.append("optional resource missing: %s" % resource_path_label(path))

    return {
        "report_outline": "assets/report_outline.yaml",
        "report_outline_version": report_outline.get("version"),
        "references": [resource_path_label(path) for path in required_references],
        "references_status": "available_with_warnings" if warnings else "available",
        "warnings": warnings,
    }


def parse_rdb(path):
    binary = resolve_hdt_rdb_binary()
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
    binary = shutil.which("rdb")
    if not binary:
        raise FileNotFoundError(
            "HDT3213 rdb CLI is required on PATH. Install it before running Phase-01 analysis."
        )

    binary_path = Path(binary)
    if not looks_like_hdt_rdb(binary_path):
        raise RuntimeError(
            "PATH rdb is not the required HDT3213 rdb CLI: %s" % binary_path
        )
    return binary_path


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


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def base_result(rdb_path, sha256_value, status):
    return {
        "schema_version": "phase-02.v1",
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "parser_required": True,
        "parser_strategy": "HdtRdbCli",
        "parser_binary": "unavailable",
        "parser_warnings": [],
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
        "outputs": {},
        "profile": {
            "name": "unavailable",
            "source": "unavailable",
        },
        "resources": {
            "report_outline": "unavailable",
            "references_status": "unavailable",
            "warnings": [],
        },
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
            "2. Parser Metadata",
            "- Parser required: %s" % json.dumps(result.get("parser_required", False)),
            "- Parser strategy: %s" % result.get("parser_strategy", "unavailable"),
            "- Parser binary: %s" % result.get("parser_binary", "unavailable"),
            "- Parser warnings: %s"
            % (
                json.dumps(result.get("parser_warnings"), ensure_ascii=False)
                if result.get("parser_warnings")
                else "none"
            ),
            "",
            "3. Basic Statistics",
            "- DB count: %s" % summary["db_count"],
            "- Total keys: %s" % summary["total_keys"],
            "- Type distribution: %s" % json.dumps(summary["type_distribution"], sort_keys=True),
            "- TTL overview: keys_with_ttl=%s, keys_without_ttl=%s"
            % (summary["ttl"]["keys_with_ttl"], summary["ttl"]["keys_without_ttl"]),
            "",
            "4. Validation Result",
            "- Mechanical validation: %s" % validation["mechanical"]["status"],
            "- Logical validation: %s" % validation["logical"]["status"],
            "- Sufficiency validation: %s" % validation["sufficiency"]["status"],
            "",
            "5. Generated Outputs",
            "- Output directory: %s" % result.get("outputs", {}).get("output_dir", "unavailable"),
            "- summary.txt: %s"
            % result.get("outputs", {}).get("summary_txt", {}).get("path", "unavailable"),
            "- result.json: %s"
            % result.get("outputs", {}).get("result_json", {}).get("path", "unavailable"),
            "- report.docx: %s"
            % result.get("outputs", {}).get("report_docx", {}).get("path", "unavailable"),
            "",
            "6. Risks and Uncertainties",
            "- Findings: %s" % (json.dumps(findings, ensure_ascii=False) if findings else "none"),
            "- Uncertainties: %s"
            % (json.dumps(uncertainties, ensure_ascii=False) if uncertainties else "none"),
            "- Deferred items: full audit trace, rich big-key rules, advanced docx layout",
            "- Errors: %s" % (json.dumps(errors, ensure_ascii=False) if errors else "none"),
            "",
        ]
    )


def section_heading(outline_by_id, section_id, fallback):
    section = outline_by_id.get(section_id, {})
    return section.get("heading") or fallback


def build_docx_sections(result, report_outline=None):
    summary = result["summary"]
    validation = result["validation"]
    outline_by_id = {}
    if report_outline:
        outline_by_id = {
            section.get("id"): section
            for section in report_outline.get("sections", [])
            if isinstance(section, dict) and section.get("id")
        }
    return [
        {
            "heading": section_heading(outline_by_id, "analysis_target", "Analysis Target"),
            "lines": [
                "Analysis time: %s" % result.get("generated_at", ""),
                "RDB file path: %s" % result["input"]["rdb_path"],
                "SHA256 fingerprint: %s" % (result["input"]["sha256"] or "unavailable"),
                "Analysis status: %s" % result["status"],
                "Profile: %s" % result.get("profile", {}).get("name", "unavailable"),
            ],
        },
        {
            "heading": section_heading(outline_by_id, "parser_metadata", "Parser Metadata"),
            "lines": [
                "Parser required: %s" % json.dumps(result.get("parser_required", False)),
                "Parser strategy: %s" % result.get("parser_strategy", "unavailable"),
                "Parser binary: %s" % result.get("parser_binary", "unavailable"),
                "Parser warnings: %s"
                % (
                    json.dumps(result.get("parser_warnings"), ensure_ascii=False)
                    if result.get("parser_warnings")
                    else "none"
                ),
            ],
        },
        {
            "heading": section_heading(outline_by_id, "basic_statistics", "Basic Statistics"),
            "lines": [
                "DB count: %s" % summary["db_count"],
                "Total keys: %s" % summary["total_keys"],
            ],
        },
        {
            "heading": section_heading(outline_by_id, "ttl_overview", "TTL Overview"),
            "lines": [
                "TTL: keys_with_ttl=%s, keys_without_ttl=%s"
                % (summary["ttl"]["keys_with_ttl"], summary["ttl"]["keys_without_ttl"]),
            ],
        },
        {
            "heading": section_heading(outline_by_id, "type_distribution", "Type Distribution"),
            "lines": [
                "Type distribution: %s" % json.dumps(summary["type_distribution"], sort_keys=True),
            ],
        },
        {
            "heading": section_heading(outline_by_id, "findings", "Findings"),
            "lines": [
                "Findings: %s"
                % (json.dumps(result.get("findings"), ensure_ascii=False) if result.get("findings") else "none"),
            ],
        },
        {
            "heading": section_heading(outline_by_id, "validation_results", "Validation Results"),
            "lines": [
                "Mechanical validation: %s" % validation["mechanical"]["status"],
                "Logical validation: %s" % validation["logical"]["status"],
                "Sufficiency validation: %s" % validation["sufficiency"]["status"],
            ],
        },
        {
            "heading": section_heading(
                outline_by_id,
                "uncertainties_and_limitations",
                "Uncertainties and Limitations",
            ),
            "lines": [
                "Uncertainties: %s"
                % (
                    json.dumps(result.get("uncertainties"), ensure_ascii=False)
                    if result.get("uncertainties")
                    else "none"
                ),
                "Phase-01 / Phase-02 limitations: local RDB only; no remote Redis, SSH, MySQL staging, multi-RDB aggregation, full audit trace, advanced risk knowledge base, or final delivery-grade docx styling.",
            ],
        },
        {
            "heading": section_heading(outline_by_id, "generated_outputs", "Generated Outputs"),
            "lines": [
                "Output directory: %s" % result.get("outputs", {}).get("output_dir", "unavailable"),
                "summary.txt: %s"
                % result.get("outputs", {}).get("summary_txt", {}).get("path", "unavailable"),
                "result.json: %s"
                % result.get("outputs", {}).get("result_json", {}).get("path", "unavailable"),
                "report.docx: %s"
                % result.get("outputs", {}).get("report_docx", {}).get("path", "unavailable"),
            ],
        },
    ]


def build_outputs_metadata(output_dir):
    return {
        "output_dir": str(output_dir),
        "summary_txt": {
            "path": str(output_dir / "summary.txt"),
            "exists": (output_dir / "summary.txt").exists(),
        },
        "result_json": {
            "path": str(output_dir / "result.json"),
            "exists": (output_dir / "result.json").exists(),
        },
        "report_docx": {
            "path": str(output_dir / "report.docx"),
            "exists": (output_dir / "report.docx").exists(),
        },
    }


def build_audit_metadata(
    output_dir,
    result,
    raw_argv,
    started_at,
    finished_at,
    duration_ms,
    exit_code,
):
    return {
        "run_id": output_dir.name,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_ms": duration_ms,
        "command": " ".join(
            shlex.quote(part)
            for part in [sys.executable, str(Path(__file__).resolve())] + list(raw_argv)
        ),
        "workdir": os.getcwd(),
        "agent": "redis-rdb-assistant",
        "skill": "skills/redis-rdb-analysis/SKILL.md",
        "model": os.getenv("AXE_MODEL", "unavailable"),
        "provider": os.getenv("AXE_PROVIDER", "unavailable"),
        "rdb_path": result.get("input", {}).get("rdb_path", ""),
        "rdb_sha256": result.get("input", {}).get("sha256", ""),
        "exit_code": exit_code,
        "status": result.get("status", "failed"),
        "parser_strategy": result.get("parser_strategy", "unavailable"),
        "parser_binary": result.get("parser_binary", "unavailable"),
    }


def build_trace_payload(output_dir, result, meta):
    return {
        "run_id": output_dir.name,
        "schema_version": "phase-04.audit.v1",
        "analysis_status": result.get("status"),
        "result_json": str(output_dir / "result.json"),
        "summary_txt": str(output_dir / "summary.txt"),
        "report_docx": str(output_dir / "report.docx"),
        "stable_fields": {
            "input.sha256": result.get("input", {}).get("sha256"),
            "summary.total_keys": result.get("summary", {}).get("total_keys"),
            "summary.db_count": result.get("summary", {}).get("db_count"),
            "summary.type_distribution": result.get("summary", {}).get("type_distribution"),
            "summary.ttl": result.get("summary", {}).get("ttl"),
            "parser_strategy": result.get("parser_strategy"),
        },
        "axe_trace_capture": {
            "status": "not_captured_by_direct_script",
            "reason": "Phase-04 direct Skill script runs outside axe model execution. Use axe native verbose/json options when invoking the agent; this file records the limitation instead of fabricating trace data.",
        },
        "meta": meta,
    }


def write_audit_archive(output_dir, result, raw_argv, started_at, started_monotonic, exit_code):
    audit_dir = output_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    finished_at = datetime.now(timezone.utc)
    duration_ms = max(0, int((time.monotonic() - started_monotonic) * 1000))
    meta = build_audit_metadata(
        output_dir,
        result,
        raw_argv,
        started_at,
        finished_at,
        duration_ms,
        exit_code,
    )
    (audit_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (audit_dir / "stdout.log").write_text(
        "output_dir=%s\nstatus=%s\n" % (output_dir, result.get("status")),
        encoding="utf-8",
    )
    (audit_dir / "stderr.log").write_text(
        "\n".join(result.get("errors") or []) + ("\n" if result.get("errors") else ""),
        encoding="utf-8",
    )
    (audit_dir / "axe_verbose.log").write_text(
        "Axe verbose output is not captured by analyze_local_rdb.py direct execution.\n"
        "Use axe native verbose/json trace options when invoking the agent; Phase-04 records this limitation.\n",
        encoding="utf-8",
    )
    (audit_dir / "trace.json").write_text(
        json.dumps(build_trace_payload(output_dir, result, meta), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def apply_validation(result, mechanical_details=None, sufficiency_details=None):
    validation = validate_result(result)
    for detail in mechanical_details or []:
        if detail not in validation["mechanical"]["details"]:
            validation["mechanical"]["details"].append(detail)
        validation["mechanical"]["status"] = "fail"
    for detail in sufficiency_details or []:
        if detail not in validation["sufficiency"]["details"]:
            validation["sufficiency"]["details"].append(detail)
        validation["sufficiency"]["status"] = "insufficient"
    result["validation"] = validation


def write_outputs(
    output_dir,
    result,
    user_request,
    mechanical_details=None,
    sufficiency_details=None,
    report_outline=None,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    input_dir = output_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    result["outputs"] = build_outputs_metadata(output_dir)

    (input_dir / "user_request.txt").write_text(user_request or "", encoding="utf-8")
    (input_dir / "rdb.fingerprint").write_text(
        result["input"]["sha256"] or "unavailable", encoding="utf-8"
    )

    (output_dir / "summary.txt").write_text(build_summary_text(result), encoding="utf-8")
    render_docx(
        output_dir / "report.docx",
        "Redis RDB Analysis Report",
        build_docx_sections(result, report_outline),
    )
    result["outputs"] = build_outputs_metadata(output_dir)
    apply_validation(result, mechanical_details, sufficiency_details)
    (output_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    result["outputs"] = build_outputs_metadata(output_dir)
    apply_validation(result, mechanical_details, sufficiency_details)
    (output_dir / "summary.txt").write_text(build_summary_text(result), encoding="utf-8")
    render_docx(
        output_dir / "report.docx",
        "Redis RDB Analysis Report",
        build_docx_sections(result, report_outline),
    )
    result["outputs"] = build_outputs_metadata(output_dir)
    apply_validation(result, mechanical_details, sufficiency_details)
    (output_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def default_output_dir():
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
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
    parser.add_argument(
        "--profile",
        default="default",
        help="Analysis response profile name under references/profiles/. Defaults to default.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    started_at = datetime.now(timezone.utc)
    started_monotonic = time.monotonic()
    args = parse_args(raw_argv)
    rdb_path = Path(args.rdb).expanduser()
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else default_output_dir()

    if not rdb_path.exists() or not rdb_path.is_file():
        result = base_result(rdb_path, "", "failed")
        result["errors"].append("RDB file does not exist or is not a file: %s" % rdb_path)
        write_outputs(output_dir, result, args.user_request, mechanical_details=["input file is missing"])
        write_audit_archive(output_dir, result, raw_argv, started_at, started_monotonic, 1)
        print(str(output_dir))
        return 1

    sha256_value = sha256_file(rdb_path)
    result = base_result(rdb_path, sha256_value, "success")
    report_outline = None

    try:
        resource_warnings = []
        profile = load_profile(args.profile)
        report_outline = load_report_outline()
        result["profile"] = profile
        result["resources"] = collect_resource_metadata(report_outline, resource_warnings)
        result["parser_warnings"].extend(resource_warnings)
        result["uncertainties"].extend(resource_warnings)
    except Exception as exc:
        result["status"] = "failed"
        result["errors"].append("Phase-03 resource loading failed: %s" % exc)
        write_outputs(
            output_dir,
            result,
            args.user_request,
            mechanical_details=["Phase-03 resource loading failed"],
            sufficiency_details=["RDB analysis resources were unavailable."],
            report_outline=report_outline,
        )
        write_audit_archive(output_dir, result, raw_argv, started_at, started_monotonic, 1)
        print(str(output_dir))
        return 1

    try:
        parsed_summary = parse_rdb(rdb_path)
        warnings = parsed_summary.pop("parser_warnings", [])
        result["parser_strategy"] = parsed_summary.get("parser_strategy", "HdtRdbCli")
        result["parser_binary"] = parsed_summary.get("parser_binary", "unavailable")
        result["parser_warnings"].extend(warnings)
        result["summary"] = parsed_summary
        result["uncertainties"].extend(warnings)
    except Exception as exc:
        result["status"] = "failed"
        result["errors"].append("RDB parser failed: %s" % exc)
        result["uncertainties"].append(
            "Only file existence and SHA256 fingerprint are verified; HDT parsing did not complete."
        )

    mechanical_details = []
    sufficiency_details = []
    if result["status"] == "failed":
        mechanical_details.append("HDT RDB parser failed")
    if result["status"] != "success":
        sufficiency_details.append(
            "RDB parser did not provide enough data for complete statistics."
        )

    exit_code = 0 if result["status"] == "success" else 1
    write_outputs(
        output_dir,
        result,
        args.user_request,
        mechanical_details,
        sufficiency_details,
        report_outline=report_outline,
    )
    write_audit_archive(output_dir, result, raw_argv, started_at, started_monotonic, exit_code)
    print(str(output_dir))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
