# Multi-Source Business ETL Pipeline

A Python project for consolidating retail transaction and reference data from multiple formats, validating it, enriching it with historical exchange rates, and loading it into PostgreSQL.

## Business scenario

The initial demonstration uses the public UCI Online Retail II transaction dataset, small synthetic product and customer reference files, and the Frankfurter historical exchange-rate API. The purpose is to demonstrate a practical multi-source ETL workflow; the synthetic reference records are not real retailer master data.

## Current project status

The repository currently contains the project plan, source and business requirements, data dictionary, and small sample reference files. Phase 2 establishes the application package structure, configuration conventions, and initial PostgreSQL schema.

**The ETL application is not implemented yet.** Extractors, transformations, validation, database loading, pipeline execution, and end-to-end tests will be added in subsequent approved phases. Do not treat the presence of a schema or package skeleton as a working pipeline.

## Planned architecture

The application is organized into separate modules for configuration, extraction, transformation, validation, loading, pipeline orchestration, database access, and shared utilities. See [docs/architecture.md](docs/architecture.md).

The proposed relational design is documented in [docs/database-schema.md](docs/database-schema.md), with the initial DDL in [sql/schema/001_initial_schema.sql](sql/schema/001_initial_schema.sql).

## Requirements

- Python 3.11 or newer
- PostgreSQL 14 or newer (target database; live connectivity has not yet been implemented)
- Git

## Local setup

Run these commands from the repository root in PowerShell or a terminal.

1. Create and activate a virtual environment:

   ```powershell
   py -3.11 -m venv .venv
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

There are no application tests yet. These commands establish the test and lint configuration; passing an empty test suite is not evidence of ETL functionality.

## Data and licensing

- UCI Online Retail II is distributed under CC BY 4.0. Review [docs/data-sources.md](docs/data-sources.md) for attribution and download guidance.
- The full source workbook is not stored in this repository.
- Files under `data/samples/` are small synthetic reference examples and are explicitly marked as synthetic.
- Frankfurter is planned for historical reference-rate enrichment. API behavior and date coverage must be verified when the API extractor is implemented.

## Security and data handling

Credentials belong in environment variables or a secret manager. The committed `.env.example` contains placeholders only. Do not commit source workbooks, private customer information, credentials, generated logs, or local database files.

## Limitations

This phase adds project configuration, package structure, architecture documentation, and a proposed PostgreSQL schema. It does not provide a runnable ETL command, database migration runner, database connection layer, source extractors, or pipeline execution. These limitations will be updated as features are implemented and tested.
