from datetime import date

import pytest
import requests

from etl_pipeline.extractors.exceptions import APIExtractionError
from etl_pipeline.extractors.frankfurter_extractor import extract_frankfurter_rates


class FakeResponse:
    def __init__(self, status=200, payload=None, headers=None):
        self.status_code = status
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def test_successful_response_is_normalized():
    session = FakeSession(
        [FakeResponse(payload=[{
            "date": "2010-12-01", "base": "GBP", "quote": "USD", "rate": 1.56
        }])]
    )
    frame = extract_frankfurter_rates(
        date(2010, 12, 1), date(2010, 12, 2), session=session
    )
    assert frame.loc[0, "rate_date"] == date(2010, 12, 1)
    assert frame.loc[0, "exchange_rate"] == 1.56
    assert session.calls == 1


def test_empty_response_returns_empty_frame():
    frame = extract_frankfurter_rates(
        "2010-12-01", "2010-12-02",
        session=FakeSession([FakeResponse(payload=[])]),
    )
    assert frame.empty
    assert list(frame.columns) == [
        "rate_date", "base_currency", "quote_currency", "exchange_rate"
    ]


@pytest.mark.parametrize("status", [400, 401, 404])
def test_permanent_http_error_is_not_retried(status):
    session = FakeSession([FakeResponse(status=status)])
    with pytest.raises(APIExtractionError, match=f"HTTP {status}"):
        extract_frankfurter_rates(
            "2010-12-01", "2010-12-02", session=session
        )
    assert session.calls == 1


@pytest.mark.parametrize("status", [429, 500])
def test_retryable_http_error_retries_and_is_bounded(monkeypatch, status):
    monkeypatch.setattr(
        "etl_pipeline.extractors.frankfurter_extractor.time.sleep",
        lambda _: None,
    )
    session = FakeSession([
        FakeResponse(status=status),
        FakeResponse(status=status),
        FakeResponse(status=status),
    ])
    with pytest.raises(APIExtractionError, match="after 3 attempts"):
        extract_frankfurter_rates(
            "2010-12-01", "2010-12-02", session=session
        )
    assert session.calls == 3


def test_retry_after_header_is_used(monkeypatch):
    delays = []
    monkeypatch.setattr(
        "etl_pipeline.extractors.frankfurter_extractor.time.sleep",
        delays.append,
    )
    session = FakeSession([
        FakeResponse(status=429, headers={"Retry-After": "2.5"}),
        FakeResponse(payload=[]),
    ])
    extract_frankfurter_rates("2010-12-01", "2010-12-02", session=session)
    assert delays == [2.5]
    assert session.calls == 2


def test_timeout_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr(
        "etl_pipeline.extractors.frankfurter_extractor.time.sleep",
        lambda _: None,
    )
    session = FakeSession([requests.Timeout(), FakeResponse(payload=[])])
    frame = extract_frankfurter_rates(
        "2010-12-01", "2010-12-02", session=session
    )
    assert frame.empty
    assert session.calls == 2


def test_invalid_date_range_is_rejected_before_request():
    session = FakeSession([])
    with pytest.raises(ValueError, match="start_date"):
        extract_frankfurter_rates(
            "2010-12-02", "2010-12-01", session=session
        )
    assert session.calls == 0


def test_malformed_and_unexpected_payloads_raise():
    payloads = [
        ValueError("bad json"),
        {"date": "2010-12-01"},
        [{"date": "2010-12-01"}],
    ]
    for payload in payloads:
        with pytest.raises(APIExtractionError):
            extract_frankfurter_rates(
                "2010-12-01", "2010-12-02",
                session=FakeSession([FakeResponse(payload=payload)]),
            )


def test_rejects_invalid_rate_and_currency_pair():
    items = [
        {"date": "2010-12-01", "base": "GBP", "quote": "USD", "rate": 0},
        {"date": "2010-12-01", "base": "EUR", "quote": "USD", "rate": 1.2},
    ]
    for item in items:
        with pytest.raises(APIExtractionError):
            extract_frankfurter_rates(
                "2010-12-01", "2010-12-02",
                session=FakeSession([FakeResponse(payload=[item])]),
            )
