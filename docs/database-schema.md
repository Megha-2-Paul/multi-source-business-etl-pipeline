# PostgreSQL schema design

## Design overview

The initial schema separates run/source tracking, raw staging, normalized business entities, exchange-rate enrichment, and rejected records. The DDL is in `sql/schema/001_initial_schema.sql`.

All tables are created in PostgreSQL's default `public` schema for the initial version. A separate application schema can be considered later if deployment requirements justify it.

## Tables and relationships

| Table | Key | Purpose |
|---|---|---|
| `etl_runs` | `run_id` UUID | One record per pipeline execution |
| `source_files` | `source_file_id` | One source artifact/API extraction per run |
| `stg_retail_transactions` | `staging_id` | Raw payload and parsed transaction fields before final loading |
| `customers` | `customer_id` text | Customer identifiers and optional reference attributes |
| `products` | `stock_code` text | Product identifiers, source descriptions, and optional reference attributes |
| `invoices` | `invoice_no` text | Invoice-level date, customer, country, and cancellation flag |
| `invoice_lines` | `invoice_line_id` | Transaction line amounts and product relationship |
| `exchange_rates` | Composite natural key | Daily currency pair and provider observation |
| `rejected_records` | `rejection_id` | Source row, reason codes, and rejection details |

## Relationship outline

- One `etl_runs` record can have many `source_files`, staging rows, and rejected records.
- One `source_files` record can have many staging rows, invoice lines, and rejected records.
- One customer can be associated with many invoices. The customer ID on an invoice is nullable for source rows without a customer identifier.
- One product can be associated with many invoice lines.
- One invoice can have many invoice lines.
- Exchange rates are looked up by rate date, base currency, quote currency, and provider key.

## Important loading rules

1. Customer and product identifiers are text. Numeric-looking identifiers must not be converted to integers.
2. Reference tables can contain transaction-observed keys even when optional synthetic reference attributes are unavailable. A `reference_matched` flag distinguishes a matched reference row from an identifier retained only to satisfy the relationship.
3. A null source customer ID remains null. It is not replaced with an invented customer.
4. Product codes observed in transactions should be represented in `products` with nullable reference attributes when no CSV reference row matches.
5. Invoice lines retain `source_file_id` and `source_row_number`; their pair is unique to prevent the same source row being loaded twice.
6. The natural key for an invoice line must be re-evaluated if workbook profiling shows that source-row numbering is not stable across workbook revisions.
7. Negative quantities, cancellation invoices, and non-positive prices are retained for classification. They are not automatically discarded by the schema.
8. Monetary values use `NUMERIC`. Original GBP values remain authoritative; converted USD values are derived from a separately stored rate observation.
9. Rejected records store one or more reason codes and the source payload needed for investigation. Sensitive source data must not be copied into logs.

## Staging and rejection

`stg_retail_transactions` stores the raw source payload as JSONB alongside nullable canonical fields and a processing status. This supports traceability when a field cannot be parsed. The source file and row reference should remain available even when parsing fails.

`rejected_records` stores rejected payloads as JSONB and a PostgreSQL text array of reason codes. The application layer must enforce non-empty reason codes; additional database checks can be added if required by implementation.

## Migration policy

The SQL file is an initial schema migration. Applied migrations should be treated as immutable. Future schema changes should be added as new, ordered migration files rather than editing an already-applied migration. A migration runner and schema-version tracking are not part of this phase.

## Limitations

The schema is a proposed first-release model based on documented source fields. It has not been applied to a live PostgreSQL server or validated against a downloaded copy of the workbook. Column types, nullability, indexes, and duplicate identity may be adjusted after source profiling, with a separate approved change plan.
