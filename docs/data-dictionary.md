# Data dictionary and join design

This document defines the source fields currently known and the proposed normalized names for the first pipeline iteration. Exact Excel header names, types, null rates, and duplicate patterns must be profiled from the downloaded workbook before implementation.

## 1. Transaction source — UCI Online Retail II

| Source field | Proposed normalized field | Proposed type | Nullable | Notes |
|---|---|---|---|---|
| InvoiceNo | invoice_no | text | No, subject to source profiling | Keep as text; leading C marks cancellation. |
| StockCode | stock_code | text | No, subject to source profiling | Product reference join key. |
| Description | product_description | text | Yes | Source product description; preserve raw value. |
| Quantity | quantity | integer | No, subject to source profiling | Preserve negative and zero values for classification. |
| InvoiceDate | invoice_at | timestamp | No, subject to source profiling | Parse using an explicit format/time-zone policy after profiling. |
| UnitPrice | unit_price_gbp | decimal | No, subject to source profiling | Unit price in GBP; avoid binary floating-point for stored money. |
| CustomerID | customer_id | text | Yes | Nullable source customer key; do not invent missing IDs. |
| Country | customer_country | text | Yes | Country name as supplied by source. |

UCI's additional variable descriptions use `UnitPrice` and `CustomerID`. The physical workbook may use display headers with spaces or alternate labels. The extraction layer must inspect and explicitly map the workbook's real headers to this canonical representation.

### Derived transaction fields

| Derived field | Proposed type | Rule |
|---|---|---|
| is_cancellation | boolean | True when normalized invoice number begins with C, case-insensitive. |
| line_amount_gbp | decimal | quantity × unit_price_gbp; retain signed values. |
| source_row_number | integer | Original worksheet row number or equivalent stable source locator. |
| source_file | text | Input file name or configured source identifier. |

A stable row identity must be designed after examining duplicates and workbook structure. Do not assume invoice number plus stock code is unique: an invoice may contain repeated product lines.

## 2. Product reference — CSV

File: `data/samples/products.csv`

| Field | Proposed type | Nullable | Meaning |
|---|---|---|---|
| stock_code | text | No | Join key to transaction StockCode. |
| product_category | text | No | Synthetic demonstration category. |
| supplier_code | text | No | Synthetic supplier reference. |
| supplier_name | text | No | Synthetic supplier name; not an actual retailer supplier. |
| metadata_is_synthetic | boolean | No | Must be true for all rows in this sample. |

The product description remains sourced from the transaction workbook. The CSV adds synthetic category and supplier attributes. Use a left join so transactions remain present when no product reference matches.

## 3. Customer reference — JSON

File: `data/samples/customers.json`

| Field | Proposed type | Nullable | Meaning |
|---|---|---|---|
| customer_id | text | No | Join key to transaction CustomerID. |
| display_name | text | No | Synthetic display label, not a real identity. |
| customer_segment | text | No | Synthetic demonstration segment. |
| customer_country | text | No | Synthetic reference attribute; compare with transaction country rather than overwrite it. |
| metadata_is_synthetic | boolean | No | Must be true for all records in this sample. |

The customer reference is a left join. Keep transaction CustomerID nulls as null and classify them as unassigned; do not join null keys to each other.

## 4. Exchange-rate source — Frankfurter v2

Proposed normalized rate fields:

| API field / source concept | Proposed normalized field | Proposed type | Notes |
|---|---|---|---|
| Observation date | rate_date | date | Date associated with returned rate. |
| Base currency | base_currency | char(3) | GBP for the planned conversion. |
| Quote currency | quote_currency | char(3) | USD for the planned conversion. |
| Rate value | exchange_rate | decimal | Quote currency units per one base currency unit. |
| Provider attribution, when requested | provider_metadata | JSON | Preserve attribution metadata if requested from API. |
| Retrieval time | retrieved_at | timestamp with time zone | Pipeline retrieval timestamp. |

The Frankfurter v2 extractor maps the response fields `date`, `base`, `quote`, and `rate` to the normalized fields shown above. Returned observations are checked against the requested date range and currency pair. Proposed natural key: rate_date + base_currency + quote_currency + provider selection. If multiple provider selections are supported, include the provider selection in the key or record metadata.

Convert only when the matching date/pair rate is available:

`amount_usd = line_amount_gbp × exchange_rate`

Keep `line_amount_gbp` unchanged. Document the fallback when a rate is unavailable; never silently substitute the previous day's rate unless an explicit, tested business rule is approved.

## 5. Proposed relational join keys

| Left side | Right side | Join | Expected relationship |
|---|---|---|---|
| Transaction stock_code | Product stock_code | LEFT | Many transaction lines to one product reference row where matched |
| Transaction customer_id | Customer customer_id | LEFT | Many transaction lines to one customer reference row where matched |
| Transaction invoice date | Rate rate_date, GBP, USD | LEFT | Many transaction lines to one daily currency pair observation where available |

Do not drop transactions because reference data or a rate is missing. Surface unmatched keys and missing rate observations in quality results.

## 6. Type and data-quality conventions

- Identifiers are text even when they look numeric.
- Monetary values use decimal arithmetic in transformations and PostgreSQL.
- Dates and timestamps are parsed explicitly; invalid values are recorded as validation failures.
- Raw source columns are retained in staging or traceable raw records.
- Nullability is based on source behavior and business meaning, not blanket removal.
- Duplicate detection uses a stable source-row identity after workbook profiling.
- Rejected rows retain a source locator and one or more reason codes.
- Normalized names use lowercase snake_case.

This dictionary is a design baseline, not a claim that the source workbook has already been downloaded or profiled.

## 7. Extraction metadata

File extractors attach `_source_file` and `_source_row_number` to extracted rows. Excel extraction also attaches `_source_sheet`. These fields are technical lineage metadata, not business attributes. CSV row numbering counts the header as row 1; JSON row numbering is the 1-based array record position; Excel row numbering counts the header as row 1. The extractor rejects source columns that collide with these reserved names.
