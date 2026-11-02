"""JSON source reader for arrays of objects."""

import json
from pathlib import Path

import pandas as pd

from etl_pipeline.extractors.exceptions import SourceFileError


def extract_json(path: str | Path, *, encoding: str = "utf-8") -> pd.DataFrame:
    """Read a top-level JSON array of objects into a DataFrame.

    _source_row_number is the 1-based record position in the JSON array.
    """
    source = Path(path)
    if not source.is_file():
        raise SourceFileError(f"JSON source file does not exist: {source}")
    try:
        with source.open("r", encoding=encoding) as stream:
            payload = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SourceFileError(f"Unable to read JSON source '{source}': {exc}") from exc
    if not isinstance(payload, list):
        raise SourceFileError("JSON source must contain a top-level array of objects")
    if not payload:
        raise SourceFileError(f"JSON source contains no records: {source}")
    if any(not isinstance(record, dict) for record in payload):
        raise SourceFileError("Every JSON array item must be an object")
    reserved = {"_source_file", "_source_row_number"}.intersection(
        {key for record in payload for key in record}
    )
    if reserved:
        raise SourceFileError(
            f"JSON source uses reserved extraction fields: {sorted(reserved)}"
        )
    frame = pd.DataFrame.from_records(payload)
    frame["_source_file"] = source.name
    frame["_source_row_number"] = range(1, len(frame) + 1)
    return frame
