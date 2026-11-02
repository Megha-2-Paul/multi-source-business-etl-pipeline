# Multi-Source Business ETL Pipeline

A Python project for consolidating retail transaction and reference data from multiple formats, validating it, enriching it with historical exchange rates, and loading it into PostgreSQL.

## Business scenario

The initial demonstration uses the public UCI Online Retail II transaction dataset, small synthetic product and customer reference files, and the Frankfurter historical exchange-rate API. The purpose is to demonstrate a practical multi-source ETL workflow; the synthetic reference records are not real retailer master data.

## Current project status

The repository contains the project plan, requirements and source documentation, sample reference files, project configuration, and initial PostgreSQL schema. Phase 3 implements source extraction for CSV, Excel, JSON, and the Frankfurter v2 API, with unit tests. Phase 4 Step 1 adds a streaming workbook profiler; it does not yet implement source-specific transformations.

**The end-to-end ETL application is not implemented yet.** Transformations, business validation, PostgreSQL loading, pipeline execution, and integration tests remain future phases. Do not treat the presence of a schema or package skeleton as a working pipeline.

## Planned architecture

The application is organized into separate modules for configuration, extraction, transformation, validation, loading, pipeline orchestration, database access, and shared utilities. See [docs/architecture.md](docs/architecture.md).

The proposed relational design is documented in [docs/database-schema.md](docs/database-schema.md), with the initial DDL in [sql/schema/001_initial_schema.sql](sql/schema/001_initial_schema.sql).

## Extraction readers

The current readers are documented in [docs/extraction-design.md](docs/extraction-design.md). File inputs carry source-row metadata. The Frankfurter reader uses bounded retries and finite timeouts. Unit tests mock HTTP responses and do not require a live API.

For local UCI workbook profiling, download `online_retail_II.xlsx` from the [official UCI dataset page](https://archive.ics.uci.edu/dataset/502/online+retail+ii) and save it as `data/raw/online_retail_II.xlsx`. The workbook is ignored by Git and must not be committed. Actual sheet names and headers have not yet been profiled; do not assume them.

## Requirements

- Python 3.11 or newer
- PostgreSQL 14 or newer (target database; live connectivity has not yet been implemented)
- Git

## Local setup

Run these commands from the repository root in PowerShell or a terminal.

1. Create and activate a virtual environment:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install the project and development dependencies:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -e ".[dev]"
   ```

3. Create a local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

4. Edit `.env` with a local PostgreSQL connection string when database functionality is implemented. Never commit the real `.env` file or share credentials.

The `requirements.txt` file is also available for runtime installation with `python -m pip install -r requirements.txt`.

## Development checks

Run the currently configured checks from the repository root:

```powershell
python -m pytest
python -m ruff check .
```

Unit tests cover the extraction readers, mocked Frankfurter HTTP behavior, and the workbook profiling utility. Transformations, business validation, PostgreSQL integration, and end-to-end pipeline tests are not implemented yet.

## Data and licensing

- UCI Online Retail II is distributed under CC BY 4.0. Review [docs/data-sources.md](docs/data-sources.md) for attribution and download guidance.
- The full source workbook is not stored in this repository.
- Files under `data/samples/` are small synthetic reference examples and are explicitly marked as synthetic.
- Frankfurter v2 extraction is implemented for historical reference-rate retrieval. Pair-specific date coverage still needs a live check before enrichment.

## Security and data handling

Credentials belong in environment variables or a secret manager. The committed `.env.example` contains placeholders only. Do not commit source workbooks, private customer information, credentials, generated logs, or local database files.

## Limitations

The repository now includes CSV, Excel, JSON, and Frankfurter v2 extraction modules with unit tests. It still does not provide a runnable end-to-end ETL command, database migration runner, database connection layer, transformations, business validation, PostgreSQL loading, or pipeline execution. The UCI workbook must be profiled locally before source-specific header mapping. Follow [docs/workbook-profiling.md](docs/workbook-profiling.md) to generate the local JSON profile; the workbook and generated report are excluded from Git.
