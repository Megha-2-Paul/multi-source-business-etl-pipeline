import pytest

from etl_pipeline.extractors.csv_extractor import extract_csv
from etl_pipeline.extractors.exceptions import SourceFileError


def test_reads_csv_and_preserves_identifier(tmp_path):
    path = tmp_path / "input.csv"
    path.write_text("invoice_no,amount\n000123,10.5\n", encoding="utf-8")
    frame = extract_csv(path)
    assert frame.loc[0, "invoice_no"] == "000123"
    assert frame.loc[0, "_source_row_number"] == 2
    assert frame.loc[0, "_source_file"] == "input.csv"


@pytest.mark.parametrize("content", ["", "a,b\n", "a,b\n1,2,3\n"])
def test_rejects_empty_or_malformed_csv(tmp_path, content):
    path = tmp_path / "bad.csv"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(SourceFileError):
        extract_csv(path)


def test_source_row_number_tracks_blank_lines(tmp_path):
    path = tmp_path / "with-gap.csv"
    path.write_text("id,value\\n001,a\\n\\n002,b\\n", encoding="utf-8")
    frame = extract_csv(path)
    assert frame["_source_row_number"].tolist() == [2, 4]


def test_missing_csv_raises(tmp_path):
    with pytest.raises(SourceFileError):
        extract_csv(tmp_path / "missing.csv")
