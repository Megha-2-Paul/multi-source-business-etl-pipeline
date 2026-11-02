"""Frankfurter v2 historical exchange-rate reader."""

import math
import time
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime

import pandas as pd
import requests

from etl_pipeline.extractors.exceptions import APIExtractionError

API_URL = "https://api.frankfurter.dev/v2/rates"
REQUIRED_FIELDS = {"date", "base", "quote", "rate"}
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


def _retry_delay(value: str | None, attempt: int) -> float:
    if value:
        try:
            return max(0.0, min(float(value), 30.0))
        except ValueError:
            try:
                parsed = parsedate_to_datetime(value)
                return max(
                    0.0,
                    min((parsed - datetime.now(timezone.utc)).total_seconds(), 30.0),
                )
            except (TypeError, ValueError, OverflowError):
                pass
    return min(0.5 * (2 ** attempt), 8.0)


def extract_frankfurter_rates(
    start_date: date | str,
    end_date: date | str,
    *,
    base: str = "GBP",
    quote: str = "USD",
    session: requests.Session | None = None,
    timeout: tuple[float, float] = (5.0, 30.0),
    max_attempts: int = 3,
) -> pd.DataFrame:
    """Fetch and validate Frankfurter v2 rates for an inclusive date range.

    Retries connection/timeouts and HTTP 429/selected 5xx responses at most
    max_attempts times. A caller-supplied session supports testing and reuse.
    """
    start = (
        date.fromisoformat(start_date)
        if isinstance(start_date, str)
        else start_date
    )
    end = date.fromisoformat(end_date) if isinstance(end_date, str) else end_date
    if start > end:
        raise ValueError("start_date must be on or before end_date")
    if not base or not quote or len(base) != 3 or len(quote) != 3:
        raise ValueError("base and quote must be three-character currency codes")
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    http_get = session.get if session is not None else requests.get
    params = {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "base": base.upper(),
        "quotes": quote.upper(),
    }
    response = None
    for attempt in range(max_attempts):
        try:
            response = http_get(API_URL, params=params, timeout=timeout)
        except (requests.Timeout, requests.ConnectionError) as exc:
            if attempt + 1 == max_attempts:
                raise APIExtractionError(
                    f"Frankfurter request failed after {max_attempts} attempts: "
                    f"{type(exc).__name__}"
                ) from exc
            time.sleep(min(0.5 * (2 ** attempt), 8.0))
            continue
        except requests.RequestException as exc:
            raise APIExtractionError(
                f"Frankfurter request failed: {type(exc).__name__}"
            ) from exc
        if response.status_code in RETRYABLE_STATUSES:
            if attempt + 1 == max_attempts:
                raise APIExtractionError(
                    f"Frankfurter returned HTTP {response.status_code} "
                    f"after {max_attempts} attempts"
                )
            time.sleep(_retry_delay(response.headers.get("Retry-After"), attempt))
            continue
        if response.status_code >= 400:
            raise APIExtractionError(
                f"Frankfurter returned HTTP {response.status_code}"
            )
        break

    try:
        payload = response.json()
    except ValueError as exc:
        raise APIExtractionError("Frankfurter response was not valid JSON") from exc
    if not isinstance(payload, list):
        raise APIExtractionError("Frankfurter v2 response must be a JSON array")
    columns = [
        "rate_date",
        "base_currency",
        "quote_currency",
        "exchange_rate",
    ]
    if not payload:
        return pd.DataFrame(columns=columns)

    normalized = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict) or not REQUIRED_FIELDS.issubset(item):
            raise APIExtractionError(
                f"Frankfurter record {index} is missing required fields "
                "or is not an object"
            )
        try:
            rate_date = date.fromisoformat(str(item["date"]))
            rate = float(item["rate"])
        except (TypeError, ValueError) as exc:
            raise APIExtractionError(
                f"Frankfurter record {index} has an invalid date or rate"
            ) from exc
        if not math.isfinite(rate) or rate <= 0:
            raise APIExtractionError(
                f"Frankfurter record {index} has a non-positive or non-finite rate"
            )
        if not start <= rate_date <= end:
            raise APIExtractionError(
                f"Frankfurter record {index} date is outside the requested range"
            )
        if item["base"] != base.upper() or item["quote"] != quote.upper():
            raise APIExtractionError(
                f"Frankfurter record {index} currency pair does not match the request"
            )
        normalized.append(
            {
                "rate_date": rate_date,
                "base_currency": item["base"],
                "quote_currency": item["quote"],
                "exchange_rate": rate,
            }
        )
    frame = pd.DataFrame.from_records(normalized, columns=columns)
    if frame["rate_date"].duplicated().any():
        raise APIExtractionError("Frankfurter response contains duplicate rate dates")
    return frame
