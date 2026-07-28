"""
Orchestrate CSV import: map → clean → validate → write JSON.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import csv
import json

from data.importer.column_mapper import map_columns_with_llm, validate_mapping
from data.importer.cleaner import clean_row
from data.importer.validator import validate_dataset
from data.importer.report import build_import_report, format_report
from config import settings, get_logger

logger = get_logger(__name__)


def import_csv(
    file_path: str | Path,
    entity: str,
    company_id: str,
    write: bool = True,
    max_reject_ratio: float = 0.5,
) -> Dict[str, Any]:
    """
    Import a CSV file into Eleva normalized format.

    Args:
        file_path: path to CSV
        entity: customers | orders | campaigns
        company_id: target company folder
        write: if True, write JSON under data_dir/company_id/
        max_reject_ratio: fail if more than this fraction of rows rejected

    Returns:
        dict with report + accepted rows
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # ----- Read CSV -----
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")
        columns = list(reader.fieldnames)
        raw_rows = list(reader)

    logger.info(f"[Import] {path.name}: {len(columns)} columns, {len(raw_rows)} rows")

    # ----- Map columns (LLM + fallback) -----
    mapping_result = map_columns_with_llm(columns, entity)
    mapping = mapping_result["mapping"]

    mapping_errors = validate_mapping(mapping, entity)
    if mapping_errors:
        raise ValueError(
            "Column mapping incomplete: " + "; ".join(mapping_errors)
        )

    # ----- Apply mapping + clean -----
    mapped_rows = []
    for raw in raw_rows:
        eleva_row = {}
        for eleva_field, source_col in mapping.items():
            if source_col:
                eleva_row[eleva_field] = raw.get(source_col)
            else:
                eleva_row[eleva_field] = None
        mapped_rows.append(clean_row(eleva_row, entity))

    # ----- Validate -----
    validation = validate_dataset(mapped_rows, entity, max_reject_ratio)

    report = build_import_report(
        entity=entity,
        source_file=str(path),
        mapping_result=mapping_result,
        validation_result=validation,
    )
    logger.info("\n" + format_report(report))

    if validation["too_many_rejects"]:
        raise ValueError(
            f"Too many rejected rows ({validation['reject_ratio']:.0%}). "
            "Import aborted. Check mapping and data quality."
        )

    # ----- Write normalized JSON -----
    if write:
        out_dir = Path(settings.data_dir) / company_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{entity}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(validation["accepted"], f, ensure_ascii=False, indent=2)
        logger.info(f"[Import] Written {out_file} ({validation['accepted_count']} records)")
        report["output_file"] = str(out_file)

    return {
        "report": report,
        "accepted": validation["accepted"],
        "rejected": validation["rejected"],
    }