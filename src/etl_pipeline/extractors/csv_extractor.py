"""CSV source reader."""

import csv
from pathlib import Path

import pandas as pd

from etl_pipeline.extractors.exceptions import SourceFileError


def extract_csv(path: str | Path, *, encoding: str = "utf-8") -> pd.DataFrame:
    """Read a CSV file, retaining identifiers as strings and source row numbers.

    The returned frame includes _source_file and _source_row_number metadata.
    Row numbers count the header as row 1; blank lines are ignored.
    """
    source = Path(path)
    if not source.is_file():
        raise SourceFileError(f"CSV source file does not exist: {source}")
    try:
        with source.open("r", encoding=encoding, newline="") as stream:
            rows = csv.reader(stream, strict=True)
            expected_width = None
            for line_number, row in enumerate(rows, start=1):
                if not row:
                    continue
                if expected_width is None:
                    expected_width = len(row)
                elif len(row) != expected_width:
                    raise SourceFileError(
                        f"Malformed CSV source '{source}': line {line_number} "
                        f"has {len(row)} fields; expected {expected_width}"
                    )
        if expected_width is None:
            raise SourceFileError(f"CSV source contains no records: {source}")
        frame = pd.read_csv(source, dtype=str, encoding=encoding, on_bad_lines="error")
    except SourceFileError:
        raise
    except (
        csv.Error,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeError,
        OSError,
        ValueError,
    ) as exc:
        raise SourceFileError(f"Unable to read CSV source '{source}': {exc}") from exc
    if len(frame.columns) == 0:
        raise SourceFileError(f"CSV source has no columns: {source}")
    if frame.empty:
        raise SourceFileError(f"CSV source contains a header but no data records: {source}")
    reserved = {"_source_file", "_source_row_number"}.intersection(frame.columns)
    if reserved:
        raise SourceFileError(
            f"CSV source uses reserved extraction columns: {sorted(reserved)}"
        )
    frame["_source_file"] = source.name
    frame["_source_row_number"] = range(2, len(frame) + 2)
    return frame
