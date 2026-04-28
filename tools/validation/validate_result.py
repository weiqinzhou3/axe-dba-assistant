"""Reusable validation helpers for assistant result contracts."""

VALID_STATUSES = {"success", "partial", "failed"}
VALID_MECHANICAL_STATUSES = {"pass", "fail"}
VALID_LOGICAL_STATUSES = {"pass", "fail", "skipped"}
VALID_SUFFICIENCY_STATUSES = {"sufficient", "insufficient"}


def validate_result(result):
    """Return a standard three-layer validation block for a result dict."""
    mechanical_details = []
    logical_details = []
    sufficiency_details = []

    required_top_level = [
        "schema_version",
        "status",
        "generated_at",
        "parser_required",
        "parser_strategy",
        "parser_binary",
        "parser_warnings",
        "input",
        "summary",
        "findings",
        "validation",
        "uncertainties",
        "errors",
        "outputs",
    ]
    for field in required_top_level:
        if field not in result:
            mechanical_details.append("missing required field: %s" % field)

    status = result.get("status")
    if status not in VALID_STATUSES:
        mechanical_details.append("status must be one of: failed, partial, success")
    if status == "failed":
        mechanical_details.append("status is failed")

    if result.get("schema_version") != "phase-02.v1":
        mechanical_details.append("schema_version must be phase-02.v1")
    if result.get("parser_required") is not True:
        mechanical_details.append("parser_required must be true")
    if not result.get("parser_strategy"):
        mechanical_details.append("parser_strategy is required")
    if not result.get("parser_binary"):
        mechanical_details.append("parser_binary is required")
    if not isinstance(result.get("parser_warnings"), list):
        mechanical_details.append("parser_warnings must be a list")

    input_block = result.get("input") if isinstance(result.get("input"), dict) else {}
    for field in ["rdb_path", "sha256", "source"]:
        if field not in input_block:
            mechanical_details.append("input.%s is required" % field)

    summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    for field in ["total_keys", "db_count", "type_distribution", "ttl", "source"]:
        if field not in summary:
            mechanical_details.append("summary.%s is required" % field)

    if "source" in input_block and not input_block.get("source"):
        mechanical_details.append("input.source must not be empty")
    if "source" in summary and not summary.get("source"):
        mechanical_details.append("summary.source must not be empty")

    type_distribution = summary.get("type_distribution", {})
    total_keys = summary.get("total_keys")
    db_count = summary.get("db_count")
    for field_name, value in [
        ("summary.total_keys", total_keys),
        ("summary.db_count", db_count),
    ]:
        if not isinstance(value, int):
            logical_details.append("%s must be an integer" % field_name)
        elif value < 0:
            logical_details.append("%s must be non-negative" % field_name)

    if isinstance(type_distribution, dict) and isinstance(total_keys, int):
        distribution_total = sum(
            value for value in type_distribution.values() if isinstance(value, int)
        )
        for key_type, count in type_distribution.items():
            if not isinstance(count, int):
                logical_details.append("type_distribution.%s must be an integer" % key_type)
            elif count < 0:
                logical_details.append("type_distribution.%s must be non-negative" % key_type)
        if distribution_total != total_keys:
            logical_details.append(
                "type_distribution total %s does not match total_keys %s"
                % (distribution_total, total_keys)
            )

    ttl = summary.get("ttl", {})
    if isinstance(ttl, dict) and isinstance(total_keys, int):
        with_ttl = ttl.get("keys_with_ttl")
        without_ttl = ttl.get("keys_without_ttl")
        for field_name, value in [
            ("summary.ttl.keys_with_ttl", with_ttl),
            ("summary.ttl.keys_without_ttl", without_ttl),
        ]:
            if not isinstance(value, int):
                logical_details.append("%s must be an integer" % field_name)
            elif value < 0:
                logical_details.append("%s must be non-negative" % field_name)
        if isinstance(with_ttl, int) and isinstance(without_ttl, int):
            ttl_total = with_ttl + without_ttl
            if ttl_total != total_keys:
                logical_details.append(
                    "ttl total %s does not match total_keys %s" % (ttl_total, total_keys)
                )

    findings = result.get("findings", [])
    if isinstance(findings, list):
        for index, finding in enumerate(findings):
            if isinstance(finding, dict) and not finding.get("source"):
                mechanical_details.append("findings[%s].source is required" % index)

    uncertainties = result.get("uncertainties", [])
    if isinstance(uncertainties, list):
        for index, uncertainty in enumerate(uncertainties):
            if isinstance(uncertainty, dict) and not uncertainty.get("source"):
                mechanical_details.append("uncertainties[%s].source is required" % index)

    outputs_value = result.get("outputs")
    outputs = outputs_value if isinstance(outputs_value, dict) else {}
    if not isinstance(outputs_value, dict):
        mechanical_details.append("outputs must be an object")
    if not outputs.get("output_dir"):
        mechanical_details.append("outputs.output_dir is required")
    for output_id in ["summary_txt", "result_json", "report_docx"]:
        output_block = outputs.get(output_id)
        if not isinstance(output_block, dict):
            mechanical_details.append("outputs.%s is required" % output_id)
            continue
        if not output_block.get("path"):
            mechanical_details.append("outputs.%s.path is required" % output_id)
        if output_block.get("exists") is not True:
            mechanical_details.append("outputs.%s.exists must be true" % output_id)

    if status == "failed":
        sufficiency_details.append("analysis failed; data is insufficient for conclusions")
    elif logical_details:
        sufficiency_details.append("logical validation failed; data is insufficient for full conclusions")

    if logical_details:
        logical_status = "fail"
    elif status == "failed":
        logical_status = "skipped"
    else:
        logical_status = "pass"

    return {
        "mechanical": {
            "status": "fail" if mechanical_details else "pass",
            "details": mechanical_details,
        },
        "logical": {
            "status": logical_status,
            "details": logical_details,
        },
        "sufficiency": {
            "status": "insufficient" if status == "failed" or logical_details else "sufficient",
            "details": sufficiency_details,
        },
    }
