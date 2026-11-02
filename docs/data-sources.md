# Data sources and constraints

This document records the sources selected for the first demonstration. Source availability, exact workbook headers, and pair-specific API coverage must be checked again when extractors are implemented.

## 1. UCI Online Retail II — transaction workbook

- Publisher: UCI Machine Learning Repository
- Dataset: Online Retail II, dataset ID 502
- Creator: Daqing Chen
- File: `online_retail_II.xlsx`
- Format: Excel workbook
- Reported size: 43.5 MB
- Reported instances: 1,067,371
- Period: 1 December 2009 to 9 December 2011
- Currency: Unit prices are stated in pounds sterling (GBP).
- Missing values: The dataset is documented as containing missing values.
- License: Creative Commons Attribution 4.0 International (CC BY 4.0).

Official source: https://archive.ics.uci.edu/dataset/502/online+retail+ii

Required attribution:

> Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D.

The CC BY 4.0 license permits sharing and adaptation with appropriate attribution. Retain this attribution in project documentation if the dataset is used. The full workbook is not included in this repository; download it separately when extraction work begins. Do not commit the 43.5 MB workbook as part of the sample-data phase.

### Documented transaction fields

UCI describes these fields:

- `InvoiceNo`: invoice identifier; values beginning with the letter C indicate cancellations.
- `StockCode`: product/item code.
- `Description`: product description.
- `Quantity`: item quantity.
- `InvoiceDate`: transaction date and time.
- `UnitPrice`: unit price in GBP.
- `CustomerID`: customer identifier; missing values occur.
- `Country`: customer country.

The workbook's exact header spelling and worksheet layout must be inspected from the downloaded file. The extractor must not assume that the displayed variable labels and physical Excel headers are identical. Header aliases, if needed, will be documented and tested rather than silently guessed.

Known data characteristics that affect implementation:

- Cancellation invoices are represented by an invoice number beginning with C.
- Customer identifiers can be missing.
- Negative quantities and other unusual numeric values must be profiled before deciding whether they are returns, cancellations, or invalid records.
- The data covers a historical period; it is not a live retail feed.

## 2. Synthetic product reference — CSV

Repository sample: `data/samples/products.csv`

The file contains demonstration product attributes keyed by `stock_code`. The stock codes and descriptions are drawn from example transaction rows in the public dataset; category and supplier attributes are invented for this demonstration. The synthetic supplier must not be represented as a real supplier of the original retailer.

The sample is intentionally small. Before full processing, compare its keys with the actual workbook and report unmatched product codes. Do not infer that this sample covers the complete product catalogue.

## 3. Synthetic customer reference — JSON

Repository sample: `data/samples/customers.json`

The file contains demonstration customer attributes keyed by `customer_id`. The customer identifier is a transaction-source key; all descriptive customer attributes in this file are synthetic. The display name is explicitly marked as synthetic and is not an attempt to identify a real customer.

The sample is not a real customer master file and must not be used to infer identity, contact details, or demographics. Missing customer IDs in the transaction source remain valid source conditions and must not be filled with invented customer identities.

## 4. Frankfurter — historical exchange rates API

- Provider: Frankfurter
- API base URL: https://api.frankfurter.dev
- API version: v2 (use v2 for new work)
- Format: JSON by default; CSV and NDJSON are also documented.
- Authentication: no API key required for the public API.
- Pricing: the provider states that its blended rates are free for commercial use.
- Limits: no daily or monthly quota is stated; requests are rate-limited to prevent abuse.
- Data: daily reference exchange rates from central banks and other official sources.
- Intended use here: optional GBP-to-USD historical reference conversion.

Official documentation: https://frankfurter.dev/

The v2 endpoint used by this project is `GET /v2/rates`. Its date-range and currency filters are `from`, `to`, `base`, and `quotes`. The response is a JSON array of observations containing `date`, `base`, `quote`, and `rate`. Example request shape:

```text
GET https://api.frankfurter.dev/v2/rates?from=2009-12-01&to=2011-12-09&base=GBP&quotes=USD
```

The extraction implementation uses this request shape. Actual GBP/USD date coverage must still be checked against the live API before enrichment is treated as complete. Do not assume every transaction date has a returned rate. Check the API's pair-specific coverage and handle missing observations explicitly. Cache rates locally or in PostgreSQL rather than repeatedly requesting the same historical data.

Frankfurter rates are reference/mid-market data, not intraday trading quotes. They should not be presented as settlement, accounting, tax, or bank transaction rates without a separate business decision and appropriate provider/source review. The API documentation notes that individual provider routes may have their own terms; the initial design uses the default blended feed.

## Source selection decision

The initial combination provides:

- Excel transaction extraction from a public licensed dataset.
- CSV product-reference extraction.
- JSON customer-reference extraction.
- REST API enrichment.
- PostgreSQL as the target database.

This combination is sufficient to demonstrate multiple formats and a coherent transaction use case without inventing access to a private retailer system. The sample references are deliberately small; key coverage and actual API coverage remain implementation-time checks.

## Extraction implementation status

Phase 3 adds generic CSV, multi-worksheet Excel, JSON-array, and Frankfurter v2 readers. The UCI workbook itself has not yet been profiled in this environment; worksheet names and physical headers remain to be confirmed locally. See [extraction-design.md](extraction-design.md) for reader contracts and limitations.
