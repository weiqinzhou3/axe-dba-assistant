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
        "status",
        "input",
        "summary",
        "findings",
        "validation",
        "uncertainties",
        "errors",
    ]
    for field in required_top_level:
        if field not in result:
            mechanical_details.append("missing required field: %s" % field)

    status = result.get("status")
    if status not in VALID_STATUSES:
        mechanical_details.append("status must be one of: failed, partial, success")

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
    if isinstance(type_distribution, dict) and isinstance(total_keys, int):
        distribution_total = sum(
            value for value in type_distribution.values() if isinstance(value, int)
        )
        if distribution_total != total_keys:
            logical_details.append(
                "type_distribution total %s does not match total_keys %s"
                % (distribution_total, total_keys)
            )

    ttl = summary.get("ttl", {})
    if isinstance(ttl, dict) and isinstance(total_keys, int):
        with_ttl = ttl.get("keys_with_ttl")
        without_ttl = ttl.get("keys_without_ttl")
        if isinstance(with_ttl, int) and isinstance(without_ttl, int):
            ttl_total = with_ttl + without_ttl
            if ttl_total != total_keys:
                logical_details.append(
                    "ttl total %s does not match total_keys %s" % (ttl_total, total_keys)
                )

    if status == "failed":
        sufficiency_details.append("analysis failed; data is insufficient for conclusions")

    return {
        "mechanical": {
            "status": "fail" if mechanical_details else "pass",
            "details": mechanical_details,
        },
        "logical": {
            "status": "fail" if logical_details else "pass",
            "details": logical_details,
        },
        "sufficiency": {
            "status": "insufficient" if status == "failed" else "sufficient",
            "details": sufficiency_details,
        },
    }
