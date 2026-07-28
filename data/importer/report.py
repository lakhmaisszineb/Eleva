"""
Build a human-readable import report.
"""

from typing import Any, Dict


def build_import_report(
    entity: str,
    source_file: str,
    mapping_result: Dict[str, Any],
    validation_result: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "entity": entity,
        "source_file": source_file,
        "mapping_source": mapping_result.get("source"),
        "mapping": mapping_result.get("mapping"),
        "ignored_columns": mapping_result.get("ignored", []),
        "total_read": validation_result["total_read"],
        "accepted_count": validation_result["accepted_count"],
        "rejected_count": validation_result["rejected_count"],
        "reject_ratio": validation_result["reject_ratio"],
        "too_many_rejects": validation_result["too_many_rejects"],
        "sample_reject_reasons": [
            r["reason"] for r in validation_result["rejected"][:5]
        ],
    }


def format_report(report: Dict[str, Any]) -> str:
    lines = [
        f"=== Import report: {report['entity']} ===",
        f"File           : {report['source_file']}",
        f"Mapping source : {report['mapping_source']}",
        f"Rows read      : {report['total_read']}",
        f"Accepted       : {report['accepted_count']}",
        f"Rejected       : {report['rejected_count']} ({report['reject_ratio']:.0%})",
        f"Mapping        : {report['mapping']}",
        f"Ignored cols   : {report['ignored_columns']}",
    ]
    if report["sample_reject_reasons"]:
        lines.append(f"Reject samples : {report['sample_reject_reasons']}")
    if report["too_many_rejects"]:
        lines.append("WARNING: too many rejected rows – import should be reviewed.")
    return "\n".join(lines)