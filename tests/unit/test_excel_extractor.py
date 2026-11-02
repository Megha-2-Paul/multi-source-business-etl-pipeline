import pandas as pd
import pytest
from openpyxl import Workbook

from etl_pipeline.extractors.exceptions import SourceFileError
from etl_pipeline.extractors.excel_extractor import extract_excel


def test_reads_all_sheets_and_source_rows(tmp_path):
    path = tmp_path / "workbook.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({"Invoice No": ["0001"]}).to_excel(
            writer, sheet_name="Retail 2009", index=False
        )
        pd.DataFrame({"Other": [1]}).to_excel(
            writer, sheet_name="Retail 2010", index=False
        )
    sheets = extract_excel(path)
    assert set(sheets) == {"Retail 2009", "Retail 2010"}
    assert sheets["Retail 2009"].loc[0, "Invoice No"] == "0001"
    assert sheets["Retail 2009"].loc[0, "_source_row_number"] == 2
    assert sheets["Retail 2009"].loc[0, "_source_sheet"] == "Retail 2009"
    assert sheets["Retail 2010"].loc[2, "_source_row_number"] == 4


def test_empty_worksheet_is_preserved(tmp_path):
    path = tmp_path / "empty-sheet.xlsx"
    workbook = Workbook()
    workbook.active.title = "Empty"
    workbook.save(path)
    sheets = extract_excel(path)
    assert "Empty" in sheets
    assert sheets["Empty"].empty
    assert "_source_row_number" in sheets["Empty"].columns


def test_missing_and_corrupt_workbooks_raise(tmp_path):
    with pytest.raises(SourceFileError):
        extract_excel(tmp_path / "missing.xlsx")
    corrupt = tmp_path / "corrupt.xlsx"
    corrupt.write_text("not an excel workbook", encoding="utf-8")
    with pytest.raises(SourceFileError):
        extract_excel(corrupt)
