"""Excel workbook reader."""

from pathlib import Path

import pandas as pd

from etl_pipeline.extractors.exceptions import SourceFileError


def extract_excel(path: str | Path) -> dict[str, pd.DataFrame]:
    """Read every worksheet into a DataFrame, preserving sheet names.

    Empty worksheets are returned as empty DataFrames. _source_row_number
    counts the header as row 1.
    """
    source = Path(path)
    if not source.is_file():
        raise SourceFileError(f"Excel source file does not exist: {source}")
    try:
        sheets = pd.read_excel(source, sheet_name=None, dtype=object, engine="openpyxl")
    except Exception as exc:
        raise SourceFileError(f"Unable to read Excel source '{source}': {exc}") from exc
    if not sheets:
        raise SourceFileError(f"Excel workbook contains no worksheets: {source}")
    result: dict[str, pd.DataFrame] = {}
    for sheet_name, frame in sheets.items():
        frame = frame.copy()
        reserved = {
            "_source_file",
            "_source_sheet",
            "_source_row_number",
        }.intersection(frame.columns)
        if reserved:
            raise SourceFileError(
                f"Excel worksheet '{sheet_name}' uses reserved extraction "
                f"columns: {sorted(reserved)}"
            )
        frame["_source_file"] = source.name
        frame["_source_sheet"] = sheet_name
        frame["_source_row_number"] = range(2, len(frame) + 2)
        result[sheet_name] = frame
    return result
