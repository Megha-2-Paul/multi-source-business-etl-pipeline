# Business requirements

## Business problem

A small online retailer receives transaction data as a spreadsheet and maintains product and customer reference information separately. The data is difficult to combine consistently for sales and operational reporting. The proposed pipeline will consolidate these inputs, apply documented data-quality rules, enrich records with historical exchange rates, and load queryable business data into PostgreSQL.

This is a demonstration built from a public research dataset and clearly identified synthetic reference data. It is not a production integration with the original retailer's systems.

## Initial source set

| Source | Format | Role | Key |
|---|---|---|---|
| UCI Online Retail II | Excel workbook | Transaction line items | Invoice number + stock code + source row identity |
| Product reference sample | CSV | Synthetic product attributes | Stock code |
| Customer reference sample | JSON | Synthetic customer attributes | Customer ID |
| Frankfurter | REST API / JSON | Historical GBP-to-USD reference rates | Rate date + base + quote |
| PostgreSQL | Database | Consolidated destination | Relational primary and foreign keys |

The UCI workbook is the primary transaction source. The CSV and JSON files provide synthetic reference attributes and are not presented as data supplied by the original retailer. Their sample keys are chosen to demonstrate joins against known public transaction identifiers. Before using a complete workbook, the implementation must check actual key coverage and report unmatched references.

The exchange-rate API is an optional enrichment source. Original GBP amounts must remain available and must never be overwritten by converted values.

## Business outputs

The initial pipeline should make it possible to query:

- Transaction line items and invoice totals.
- Sales by date, product, customer segment, and country.
- Products with missing or unmatched reference attributes.
- Transactions with missing customer identifiers.
- Cancelled invoices and negative-quantity records.
- GBP sales alongside an optional USD reference amount and the rate used.

No dashboard or business-impact claim is part of this phase.

## Initial business rules to confirm during implementation

1. Treat invoice and stock codes as strings. Do not cast identifiers to numbers.
2. Preserve source values in staging before normalization.
3. Treat invoice numbers beginning with `C` (case-insensitive) as cancellation indicators; do not silently discard them.
4. Preserve negative quantities and zero/negative prices for review. Their business meaning must be assessed rather than assumed invalid.
5. A missing customer ID is allowed in the source. Keep the transaction and classify the customer relationship as unknown/unassigned.
6. Product and customer enrichment is a left join. Missing reference matches must be visible and must not remove transaction lines.
7. Calculate line amount in GBP as quantity multiplied by unit price, retaining the original quantity and unit price.
8. Convert to USD only when a valid rate for the relevant date and GBP/USD pair is available. Otherwise retain the GBP amount and record the missing-rate condition.
9. Do not use the synthetic customer attributes as facts about any real person. They exist only to demonstrate schema joins.
10. Every rejected record must retain a source identifier or safe source-row reference and one or more explicit rejection reasons.

These are proposed rules for the first implementation. Validation severity, duplicate identity, and cancellation treatment will be finalized against the actual workbook structure before coding.

## Out of scope for this phase

- Downloading or committing the full 43.5 MB source workbook.
- Building Python extractors or transformations.
- Creating PostgreSQL tables or database credentials.
- Scheduling, orchestration, dashboards, or cloud deployment.
- Claiming the synthetic reference files represent real retailer master data.

## Phase 1 acceptance criteria

- The selected sources and their limitations are documented.
- Dataset attribution and API terms are recorded.
- Canonical source fields and proposed normalized names are documented.
- Sample CSV and JSON files are valid, clearly synthetic, and have documented join keys.
- No application code, dependencies, database objects, or credentials are added in this phase.
