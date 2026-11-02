# Application architecture

## Design goals

The application is organized around the ETL stages and keeps external I/O separate from data rules. Modules should be small enough to test independently. The package uses a `src/` layout so tests and installed execution resolve the same package.

## Package responsibilities

| Package | Responsibility | Expected dependencies |
|---|---|---|
| `config` | Read and validate environment-backed settings | Standard library; python-dotenv for local development |
| `extractors` | Read CSV, Excel, JSON, and HTTP API inputs into predictable raw structures | pandas, openpyxl, requests |
| `transformations` | Normalize fields, parse values, calculate amounts, and join reference data | pandas, standard library decimal/date tools |
| `validators` | Apply schema and business rules; return valid and rejected records with reasons | pandas or typed Python structures |
| `loaders` | Persist staging, valid business records, rates, and rejections | psycopg |
| `pipeline` | Coordinate stages and record run status/counts | Internal packages |
| `database` | Manage PostgreSQL connections and transaction boundaries | psycopg |
| `utils` | Shared logging and narrowly scoped helpers | Standard library |

The dependency direction should flow from the pipeline into stage modules. Extractors, transformations, and validators should not import the pipeline or call database operations directly.

## Planned data flow

1. Create a run record and identify the configured input sources.
2. Extract each source, preserving source identifiers and raw values.
3. Write or retain staging records before applying business transformations.
4. Normalize column names, identifiers, dates, quantities, and decimal monetary values.
5. Enrich transaction rows with product/customer reference attributes using left joins.
6. Optionally retrieve and cache historical GBP/USD observations.
7. Validate required fields, types, business rules, duplicate identity, and reference relationships.
8. Persist accepted records and rejected records with traceable source-row references.
9. Complete the run with actual extracted, accepted, rejected, and loaded counts.

This is the target flow, not implemented behavior. Each stage will be delivered and tested in its own approved phase.

## Error handling

Expected input and external-service failures should raise explicit, contextual exceptions. API calls must have finite connect/read timeouts and distinguish HTTP failures, timeouts, malformed JSON, and unexpected response shapes. A source failure should be recorded against the run and source. Whether the entire batch stops or continues must depend on the source's role and documented failure policy.

Validation failures are data-quality outcomes, not unexpected application exceptions. They should be represented as rejected records with stable reason codes. Unexpected programming or database failures must not be silently converted into successful runs.

## Configuration and secrets

Application settings are read from environment variables. A local `.env` may be used for development but is excluded from Git. `.env.example` documents setting names and safe placeholders. Logs must not include database URLs, passwords, access tokens, or complete records containing sensitive data.

## Database transaction boundaries

Database connections are managed by the database package. Writes for a logically consistent load should use explicit transactions. A failed transaction must roll back. Staging and rejection persistence should be designed so a failed load does not leave accepted business tables partially updated.

## Repeatability

The schema includes source-file and source-row references to support idempotent loads. The exact source-row identity and conflict policy will be implemented only after profiling the downloaded workbook. Re-running the same input must not create duplicate invoice lines. Updates to reference data and historical rates must have explicit upsert rules.

## Testing boundaries

- Unit tests cover parsing, normalization, joins, validation, configuration, and SQL helpers.
- API tests use mocked HTTP responses; ordinary unit tests must not depend on live network availability.
- Database integration tests use a dedicated test database and verify transactions, constraints, upserts, and repeat runs.
- End-to-end tests use small fixture inputs and an isolated PostgreSQL service.

## Current implementation status

This document describes the agreed target design for the project setup phase. It does not imply that any extractor, transformation, validator, loader, pipeline runner, or connection manager has been implemented.
