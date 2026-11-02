import pytest

from etl_pipeline.extractors.exceptions import SourceFileError
from etl_pipeline.extractors.json_extractor import extract_json


@pytest.mark.parametrize(
    "content", ["", "{bad json", "{}", "[]", '[{"id": 1}, 2]']
)
def test_rejects_invalid_json_shapes(tmp_path, content):
    path = tmp_path / "input.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(SourceFileError):
        extract_json(path)


def test_reads_array_of_objects(tmp_path):
    path = tmp_path / "input.json"
    path.write_text(
        '[{"customer_id": "0012"}, {"customer_id": "0013"}]',
        encoding="utf-8",
    )
    frame = extract_json(path)
    assert frame["customer_id"].tolist() == ["0012", "0013"]
    assert frame["_source_row_number"].tolist() == [1, 2]


def test_missing_json_raises(tmp_path):
    with pytest.raises(SourceFileError):
        extract_json(tmp_path / "missing.json")
