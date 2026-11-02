"""Stream structural and data-quality metadata from an Excel workbook."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from openpyxl.cell.cell import Cell

from etl_pipeline.extractors.exceptions import SourceFileError

_DEFAULT_SAMPLE_ROWS = 5
_DEFAULT_DUPLICATE_ANALYSIS_ROWS = 100_000


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _value_type(cell: Cell) -> str:
    value = cell.value
    if value is None:
        return "blank"
    if cell.data_type == "f":
        return "formula"
    if cell.is_date:
        return "date_or_datetime"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "numeric"
    if isinstance(value, str):
        return "text"
    return type(value).__name__


def _fingerprint(values: list[Any]) -> str:
    serialized = json.dumps(
        [_json_value(value) for value in values],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def profile_workbook(
    path: str | Path,
    *,
    sample_rows: int = _DEFAULT_SAMPLE_ROWS,
    duplicate_analysis_rows: int = _DEFAULT_DUPLICATE_ANALYSIS_ROWS,
) -> dict[str, Any]:
    """Profile workbook structure and column quality without loading it into pandas.

    Duplicate analysis is bounded to the first configured number of non-empty
    data rows. Row counts, blank counts, and type counts cover all scanned rows.
    """
    source = Path(path)
    if not source.is_file():
        raise SourceFileError(f"Excel source file does not exist: {source}")
    if sample_rows < 0 or duplicate_analysis_rows < 1:
        raise ValueError(
            "sample_rows must be non-negative and duplicate_analysis_rows positive"
        )

    try:
        workbook = load_workbook(source, read_only=True, data_only=False)
    except Exception as exc:
        raise SourceFileError(
            f"Unable to open Excel workbook '{source.name}': {exc}"
        ) from exc

    try:
        worksheets: list[dict[str, Any]] = []
        for worksheet in workbook.worksheets:
            max_row = worksheet.max_row or 0
            max_column = worksheet.max_column or 0
            rows = worksheet.iter_rows(
                min_row=1,
                max_row=max_row,
                min_col=1,
                max_col=max_column,
            )
            header_cells = next(rows, ())
            headers = [
                {
                    "position": index,
                    "value": _json_value(cell.value),
                    "blank": _is_empty(cell.value),
                }
                for index, cell in enumerate(header_cells, start=1)
            ]

            column_stats = [
                {
                    "position": index,
                    "header": _json_value(cell.value),
                    "blank_header": _is_empty(cell.value),
                    "non_empty_count": 0,
                    "null_count": 0,
                    "type_counts": Counter(),
                    "sample_distinct": set(),
                    "sample_non_empty_count": 0,
                }
                for index, cell in enumerate(header_cells, start=1)
            ]
            sample_data: list[dict[str, Any]] = []
            empty_rows = 0
            non_empty_rows = 0
            duplicate_rows = 0
            row_fingerprints: set[str] = set()
            duplicate_scope_rows = 0
            physical_data_rows = 0

            for row in rows:
                physical_data_rows += 1
                values = [cell.value for cell in row]
                if all(_is_empty(value) for value in values):
                    empty_rows += 1
                    continue

                non_empty_rows += 1
                if len(sample_data) < sample_rows:
                    sample_data.append(
                        {
                            "source_row_number": physical_data_rows + 1,
                            "values": [
                                {
                                    "position": index,
                                    "header": _json_value(header_cells[index - 1].value),
                                    "value": _json_value(value),
                                }
                                for index, value in enumerate(values, start=1)
                            ],
                        }
                    )

                for index, cell in enumerate(row):
                    stats = column_stats[index]
                    if _is_empty(cell.value):
                        stats["null_count"] += 1
                    else:
                        stats["non_empty_count"] += 1
                        stats["type_counts"][_value_type(cell)] += 1

                if duplicate_scope_rows < duplicate_analysis_rows:
                    duplicate_scope_rows += 1
                    fingerprint = _fingerprint(values)
                    if fingerprint in row_fingerprints:
                        duplicate_rows += 1
                    else:
                        row_fingerprints.add(fingerprint)
                    for index, value in enumerate(values):
                        if not _is_empty(value):
                            column_stats[index]["sample_non_empty_count"] += 1
                            column_stats[index]["sample_distinct"].add(
                                _fingerprint([value])
                            )

            finalized_columns = []
            for stats in column_stats:
                distinct_count = len(stats["sample_distinct"])
                finalized_columns.append(
                    {
                        "position": stats["position"],
                        "header": stats["header"],
                        "blank_header": stats["blank_header"],
                        "non_empty_count": stats["non_empty_count"],
                        "null_count": stats["null_count"],
                        "type_counts": dict(sorted(stats["type_counts"].items())),
                        "distinct_non_empty_values_in_duplicate_sample": distinct_count,
                        "repeated_non_empty_values_in_duplicate_sample": (
                            stats["sample_non_empty_count"] - distinct_count
                        ),
                        "entirely_empty": stats["non_empty_count"] == 0,
                    }
                )

            worksheets.append(
                {
                    "name": worksheet.title,
                    "reported_dimensions": {
                        "max_row": max_row,
                        "max_column": max_column,
                    },
                    "physical_data_rows_scanned": physical_data_rows,
                    "non_empty_data_rows": non_empty_rows,
                    "empty_data_rows": empty_rows,
                    "headers": headers,
                    "columns": finalized_columns,
                    "entirely_empty_columns": [
                        column["position"]
                        for column in finalized_columns
                        if column["entirely_empty"]
                    ],
                    "sample_rows": sample_data,
                    "duplicate_analysis": {
                        "scope": "first non-empty data rows in worksheet",
                        "rows_examined": duplicate_scope_rows,
                        "row_limit": duplicate_analysis_rows,
                        "duplicate_full_rows": duplicate_rows,
                        "column_repetition_counts_are_sampled": True,
                    },
                }
            )

        return {
            "profile_version": 1,
            "source_file": source.name,
            "profiling_method": "openpyxl read-only row iteration",
            "sample_row_limit": sample_rows,
            "worksheets": worksheets,
        }
    except Exception as exc:
        raise SourceFileError(
            f"Unable to profile Excel workbook '{source.name}': {exc}"
        ) from exc
    finally:
        workbook.close()


def write_profile_report(profile: dict[str, Any], output_path: str | Path) -> Path:
    """Write a UTF-8 JSON profile report, creating its parent directory."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        destination.write_text(
            json.dumps(profile, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise SourceFileError(
            f"Unable to write workbook profile report '{destination}': {exc}"
        ) from exc
    return destination


def main() -> None:
    """Run workbook profiling from the command line."""
    parser = argparse.ArgumentParser(
        description="Profile an Excel workbook and write a JSON report."
    )
    parser.add_argument("workbook", type=Path, help="Path to the source .xlsx workbook")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/workbook_profile.json"),
        help="JSON report path (default: data/processed/workbook_profile.json)",
    )
    parser.add_argument("--sample-rows", type=int, default=_DEFAULT_SAMPLE_ROWS)
    parser.add_argument(
        "--duplicate-analysis-rows",
        type=int,
        default=_DEFAULT_DUPLICATE_ANALYSIS_ROWS,
    )
    args = parser.parse_args()

    profile = profile_workbook(
        args.workbook,
        sample_rows=args.sample_rows,
        duplicate_analysis_rows=args.duplicate_analysis_rows,
    )
    report_path = write_profile_report(profile, args.output)
    print(f"Workbook profile written to: {report_path}")
    for worksheet in profile["worksheets"]:
        print(
            f"{worksheet['name']}: {worksheet['non_empty_data_rows']:,} "
            f"non-empty data rows, {len(worksheet['headers'])} columns, "
            f"{worksheet['duplicate_analysis']['duplicate_full_rows']:,} "
            "duplicate full rows in the bounded analysis sample"
        )


if __name__ == "__main__":
    main()
