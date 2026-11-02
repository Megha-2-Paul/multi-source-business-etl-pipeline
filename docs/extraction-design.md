# Extraction design

## Scope

Phase 3 implements readers for CSV, Excel, JSON, and the Frankfurter v2 rates endpoint. Extractors return raw or minimally normalized source structures with source-row metadata. They do not clean business values, join sources, validate retail rules, or write to PostgreSQL.

## Local file readers

| Reader | Contract | Source locator |
|---|---|---|
| `extract_csv(path)` | One `pandas.DataFrame`; identifiers are read as strings | `_source_file`, `_source_row_number` |
| `extract_excel(path)` | Dictionary of worksheet name to DataFrame; empty worksheets remain represented | `_source_file`, `_source_sheet`, `_source_row_number` |
| `extract_json(path)` | DataFrame from a non-empty top-level array of objects | `_source_file`, `_source_row_number` |

CSV rows are checked for consistent field counts before Pandas parsing. Blank lines are ignored. CSV and JSON identifiers represented as text retain leading zeroes. Excel values are read as stored cell values; if an identifier was stored numerically in the workbook, its original display formatting cannot be inferred reliably at extraction time. The canonical conversion policy belongs to a later transformation phase.

The `_source_*` columns are reserved for extractor metadata. An input using those names is rejected rather than overwritten. File errors are normalized to `SourceFileError` with source context. An empty CSV, empty JSON array, non-array JSON root, or malformed JSON is an extraction failure. An empty Excel worksheet is valid and remains in the returned mapping.

## Frankfurter v2

`extract_frankfurter_rates(start_date, end_date, base="GBP", quote="USD")` calls `GET https://api.frankfurter.dev/v2/rates` with `from`, `to`, `base`, and `quotes` query parameters. It returns `rate_date`, `base_currency`, `quote_currency`, and `exchange_rate` columns. Empty results return an empty DataFrame with that schema.

The reader validates the JSON array shape, required fields, date, positive finite rate, requested currency pair, requested date range, and duplicate dates. It uses finite connect/read timeouts (5 and 30 seconds by default). Connection/timeouts and HTTP 429/500/502/503/504 responses are retried at most three times by default. `Retry-After` is honored for retryable HTTP responses, capped at 30 seconds; otherwise bounded exponential backoff is used. Other HTTP errors are not retried. Tests inject a session and mock responses; unit tests do not depend on network availability.

The API reader does not invent missing daily rates or carry a prior rate forward. Rate coverage and transaction-date matching are later transformation/business-rule concerns.

## Workbook profiling status

The UCI workbook is intentionally not committed. Place the licensed source file at `data/raw/online_retail_II.xlsx` for local profiling. The official download could not be retrieved in the implementation environment, so the workbook's actual worksheet names, physical headers, row counts, empty sheets, null patterns, and duplicate patterns have **not** been profiled. The Excel reader is therefore generic and makes no assumptions about worksheet names or header aliases. Profile the downloaded workbook locally before defining those mappings or the subsequent transformation contract.

UCI attribution: Chen, D. (2012). *Online Retail II* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D. Licensed under CC BY 4.0.

Frankfurter documentation: https://frankfurter.dev/ (v2 API; no API key required for the public endpoint).
