"""Tests for streaming Excel workbook profiling."""

import json
from datetime import datetime
from pathlib import Path

import pytest
from openpyxl import Workbook

from etl_pipeline.extractors.exceptions import SourceFileError
from etl_pipeline.utils.workbook_profile import profile_workbook, write_profile_report


def _make_workbook(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sales"
    sheet.append(["Invoice", "Date", "Amount", "Notes", ""])
    sheet.append([1, datetime(2024, 1, 2), 12.5, None, None])
    sheet["A2"].number_format = "00000"
    sheet.append(["002", datetime(2024, 1, 3), 18, "ok", None])
    sheet.append(["002", datetime(2024, 1, 3), 18, "ok", None])
    sheet.append([None, None, None, None, None])
    empty = workbook.create_sheet("Empty")
    empty.append([None, None])
    workbook.save(path)
    workbook.close()


def test_profile_reports_headers_types_nulls_and_samples(tmp_path: Path) -> None:
    source = tmp_path / "sample.xlsx"
    _make_workbook(source)

    profile = profile_workbook(source)

    sales = profile["worksheets"][0]
    assert sales["name"] == "Sales"
    assert sales["headers"][0] == {
        "position": 1,
        "value": "Invoice",
        "blank": False,
    }
    assert sales["columns"][0]["type_counts"] == {"numeric": 1, "text": 2}
    assert sales["columns"][0]["number_format_counts"] == {
        "00000": 1,
        "General": 2,
    }
    assert sales["columns"][2]["type_counts"] == {"numeric": 3}
    assert sales["columns"][3]["null_count"] == 1
    assert sales["non_empty_data_rows"] == 3
    assert sales["empty_data_rows"] == 1
    assert sales["sample_rows"][0]["source_row_number"] == 2
    assert sales["sample_rows"][0]["values"][0]["value"] == 1


def test_profile_identifies_duplicate_rows_with_bounded_scope(tmp_path: Path) -> None:
    source = tmp_path / "sample.xlsx"
    _make_workbook(source)

    profile = profile_workbook(source, duplicate_analysis_rows=2)

    duplicate_analysis = profile["worksheets"][0]["duplicate_analysis"]
    assert duplicate_analysis["rows_examined"] == 2
    assert duplicate_analysis["duplicate_full_rows"] == 0
    assert duplicate_analysis["row_limit"] == 2


def test_profile_counts_duplicate_rows_when_within_sample(tmp_path: Path) -> None:
    source = tmp_path / "sample.xlsx"
    _make_workbook(source)

    profile = profile_workbook(source, duplicate_analysis_rows=3)

    duplicate_analysis = profile["worksheets"][0]["duplicate_analysis"]
    assert duplicate_analysis["duplicate_full_rows"] == 1


def test_profile_handles_empty_worksheet(tmp_path: Path) -> None:
    source = tmp_path / "sample.xlsx"
    _make_workbook(source)

    empty = profile_workbook(source)["worksheets"][1]

    assert empty["name"] == "Empty"
    assert empty["non_empty_data_rows"] == 0
    assert empty["entirely_empty_columns"] == [1, 2]


def test_profile_rejects_missing_or_invalid_workbook(tmp_path: Path) -> None:
    with pytest.raises(SourceFileError, match="does not exist"):
        profile_workbook(tmp_path / "missing.xlsx")

    invalid = tmp_path / "invalid.xlsx"
    invalid.write_text("not an Excel workbook", encoding="utf-8")
    with pytest.raises(SourceFileError, match="Unable to open"):
        profile_workbook(invalid)


def test_profile_report_is_valid_json(tmp_path: Path) -> None:
    source = tmp_path / "sample.xlsx"
    _make_workbook(source)
    profile = profile_workbook(source)

    report = write_profile_report(profile, tmp_path / "reports" / "profile.json")

    loaded = json.loads(report.read_text(encoding="utf-8"))
    assert loaded["source_file"] == "sample.xlsx"
    assert report.is_file()


def test_profile_validates_limits(tmp_path: Path) -> None:
    source = tmp_path / "sample.xlsx"
    _make_workbook(source)

    with pytest.raises(ValueError, match="sample_rows"):
        profile_workbook(source, sample_rows=-1)
