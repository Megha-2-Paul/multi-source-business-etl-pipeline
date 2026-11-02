# Multi-Source Business ETL Pipeline
## Project Instructions, Development Workflow, and Implementation Plan

**Document status:** Project blueprint  
**Primary destination:** PostgreSQL  
**Implementation language:** Python  
**Core pattern:** Extract → Transform → Validate → Load

---

## 1. Project Purpose

Build a practical business data integration pipeline that collects information from multiple sources, standardizes and validates it, and loads reliable records into a central PostgreSQL database.

The project should demonstrate real freelance-relevant capabilities:

- CSV and Excel data processing
- JSON and REST API extraction
- Multi-source data integration
- Python and Pandas transformations
- Data quality checks and rejected-record handling
- PostgreSQL schema design and loading
- Repeatable and safe execution
- Logging, error handling, and automated testing

The goal is a maintainable working application, not a collection of disconnected scripts or a superficial portfolio demo.

## 2. Working Principles and Assistant Instructions

The AI assistant working on this repository must follow these rules.

### 2.1 GitHub changes require approval

**Never modify the repository before receiving explicit approval.**

1. Inspect the relevant repository files and current implementation first.
2. Present a specific plan describing the problem, proposed solution, files to create or modify, dependency or database changes, risks, and verification steps.
3. Stop and wait for approval.
4. Approval applies only to the described scope. Ask again before making additional changes outside it.
5. After approval, implement the approved changes directly through the connected GitHub integration when available.
6. Preserve existing working functionality and unrelated work.
7. Never expose credentials, force-push, or rewrite history.
8. Verify the resulting changes. Do not claim an operation succeeded unless the available tools confirm it.

Approval phrases include “approved”, “proceed”, and “implement it”. If the owner asks for a revised plan, provide it and wait again.

### 2.2 Engineering standards

- Prefer clear, modular, maintainable Python.
- Follow PEP 8 and use descriptive names.
- Use type hints and docstrings where they improve clarity.
- Keep functions focused and responsibilities separated.
- Use parameterized SQL and explicit exception handling.
- Keep credentials outside source control.
- Avoid needless abstractions, overengineering, giant files, unused dependencies, redundant comments, and hardcoded machine-specific paths.
- Inspect the existing architecture before deciding how to extend it.
- Add technologies only when a real requirement justifies them.

### 2.3 No AI slop

All code, documentation, comments, and portfolio material should resemble genuine professional engineering work.

Avoid generic AI prose, repetitive explanations, inflated claims, marketing buzzwords, meaningless comments, excessive headings, decorative emojis in technical documentation, generic README templates, fake metrics, and invented business outcomes.

Use concise, natural, project-specific technical writing. Explain actual decisions and trade-offs. Document real limitations. Use real execution output and screenshots. Do not disguise placeholders as completed functionality or introduce deliberate mistakes to appear human.

### 2.4 Honesty and reporting

Never claim code was implemented, committed, pushed, inspected, or tested unless tools confirm it. Distinguish clearly between:

- Implemented
- Tested successfully
- Partially tested
- Failed
- Not implemented
- Blocked from testing

Never invent test results, record counts, processing times, performance gains, testimonials, or business impact. Do not promise a bug-free system; reduce defects through testing, review, edge-case analysis, and regression checks.

---

## 3. Business Use Case

### Proposed use case: Multi-Source Business Operations Data Integration

A business receives operational data from different systems and files. The formats and structures are inconsistent, making consolidated reporting difficult.

The pipeline will collect data from several sources, standardize it, validate its quality, and store it in PostgreSQL for downstream analysis.

Potential source roles:

| Source | Example information | Purpose |
|---|---|---|
| CSV file | Orders or transactions | File-based operational input |
| Excel file | Customer or product reference data | Spreadsheet integration |
| REST API | External order, product, or operational records | API integration |
| JSON file/API response | Additional structured business data | Flexible source integration |
| PostgreSQL | Central destination | Unified, queryable storage |

The exact datasets and APIs must be selected after repository inspection and source verification. Check licensing, API terms, availability, authentication, rate limits, and whether the data fields can be joined meaningfully.

Do not assume that every source is required in the first release. Select a small, coherent set that supports a credible end-to-end demonstration.

---

## 4. High-Level Architecture

```text
CSV / Excel       REST API       JSON / Other Source
     |                |                    |
     +----------------+--------------------+
                      |
                SOURCE EXTRACTORS
                      |
              RAW / STAGING DATA
                      |
               TRANSFORMATION
        Cleaning, mapping, normalization,
             merging, enrichment
                      |
                 VALIDATION
        Schema, types, nulls, duplicates,
          business rules, relationships
                 /          \
          Valid records    Rejected records
                |                |
                |         Rejection details
                |         and failure reasons
                |
             LOAD LAYER
        PostgreSQL transactions,
          inserts / upserts
                |
        CENTRAL POSTGRESQL DB
                |
       SQL queries / reporting output

Cross-cutting: configuration, logging, error handling,
testing, execution status, and documentation.
```

This is a conceptual architecture. The final design must be adapted to the existing repository and verified source requirements.

---

## 5. Functional Requirements

### 5.1 Extraction

Support the selected CSV, Excel, JSON, and REST API sources.

Requirements:

- Reusable extractor modules
- Configurable source paths and endpoints
- Explicit handling of missing files and invalid formats
- API timeout and HTTP error handling
- Authentication through secure configuration where needed
- Handling for empty responses and unexpected response structures
- Clear extraction logs and execution status

### 5.2 Transformation

Use Python and Pandas where appropriate.

Potential operations:

- Standardize column names
- Normalize data types
- Parse and standardize dates
- Handle missing values according to documented rules
- Detect duplicates
- Clean strings and categorical values
- Merge datasets using documented keys
- Apply business calculations and rules
- Reshape data where needed

Transformation rules must be explicit, testable, and appropriate to the selected business data.

### 5.3 Validation

Implement checks appropriate to the actual schema:

- Required columns and schema
- Data types
- Null and missing-value rules
- Duplicate records
- Valid ranges and allowed values
- Business rules
- Referential integrity where applicable

Invalid records must not disappear silently. Capture the record or a safe reference to it, the validation failure, and its reason. Decide whether a batch should continue or fail based on documented severity rules.

### 5.4 PostgreSQL loading

Use PostgreSQL as the primary destination.

Requirements:

- Documented relational schema
- Appropriate primary and foreign keys
- Managed connections
- Parameterized SQL
- Transaction handling
- Safe inserts and upserts where appropriate
- Duplicate prevention
- Repeatable execution
- Clear failure handling

Choose full-refresh or incremental loading based on source behavior and business requirements. Explain the choice and test repeated runs.

### 5.5 Observability and reliability

Provide:

- Useful application logs
- Pipeline execution status
- Counts of extracted, accepted, rejected, and loaded records where measurable
- Clear error messages
- Safe failure behavior
- Repeatable runs
- Traceable validation failures

Only report metrics that are calculated from actual execution.

---

## 6. Suggested Repository Structure

This is a starting proposal, not an instruction to replace the current repository structure. Inspect the repository and obtain approval before creating or reorganizing files.

```text
multi-source-business-etl/
├── src/
│   └── etl_pipeline/
│       ├── __init__.py
│       ├── config/
│       ├── extractors/
│       ├── transformations/
│       ├── validators/
│       ├── loaders/
│       ├── pipeline/
│       ├── database/
│       └── utils/
├── tests/
│   ├── unit/
│   └── integration/
├── data/
│   ├── samples/
│   └── rejected/
├── sql/
│   └── schema/
├── docs/
├── .github/
│   └── workflows/
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
└── requirements.txt
```

Use only the directories and files the implementation actually needs. Avoid committing private or sensitive source data.

---

## 7. Development Roadmap

Work in phases. Each phase requires a plan and approval before repository changes.

| Phase | Scope | Expected evidence |
|---|---|---|
| 0. Repository assessment | Inspect existing code, architecture, dependencies, tests, and issues | Repository audit and approved roadmap |
| 1. Requirements and sources | Finalize business scenario, data sources, fields, join keys, and licensing | Source documentation and data samples |
| 2. Architecture and setup | Agree on modules, configuration, dependencies, and database design | Approved architecture and setup |
| 3. Extraction | Implement selected file and API extractors | Extractor tests and sample extraction |
| 4. Transformation | Implement cleaning, normalization, mapping, and joins | Transformation tests and sample output |
| 5. Validation | Implement data-quality rules and rejected-record handling | Validation tests and rejection examples |
| 6. PostgreSQL | Create schema and safe loading logic | Verified database records and load tests |
| 7. Pipeline integration | Connect extraction, transformation, validation, and loading | Successful end-to-end run |
| 8. Reliability | Improve logging, configuration, transactions, and repeat execution | Failure and repeat-run evidence |
| 9. Testing and CI | Unit, integration, regression, static checks, and GitHub Actions | Actual test reports and CI result |
| 10. Documentation | Complete setup, architecture, schema, usage, and limitations | Verified README and technical docs |
| 11. Portfolio | Capture genuine screenshots and record a demo | Portfolio-ready evidence |

Phases may be combined when requested, but approval and testing requirements still apply.

---

## 8. Testing Strategy

Testing is mandatory throughout the project.

### Unit tests

Test individual extractors, transformation functions, validators, configuration handling, database helpers, and error-handling paths.

### Integration tests

Test interactions between source extraction, transformation, validation, and PostgreSQL loading. Use isolated test data and a dedicated test database. Never run destructive tests against production or personal data.

### Edge cases

Include:

- Empty or malformed input
- Missing or unexpected columns
- Nulls and duplicates
- Invalid dates and data types
- API timeouts, HTTP errors, and malformed responses
- Database connection failures
- Constraint violations
- Partial pipeline failures
- Repeated execution
- Unexpected changes in source structure

### Quality tools and CI

Use appropriate tools, such as:

- pytest for tests
- Ruff for linting and formatting checks
- Python syntax/compilation checks
- mypy where useful
- GitHub Actions for automated checks when appropriate

Do not add tools just for appearance. Protect credentials in CI and use isolated database services for integration tests where feasible.

### Failure procedure

When a test fails:

1. Identify the root cause from evidence.
2. Inspect the affected implementation.
3. Explain the proposed fix.
4. Obtain additional approval if the fix exceeds the approved scope.
5. Implement the approved fix.
6. Rerun the failed test and relevant regression tests.

Never weaken tests or suppress errors to manufacture a passing result.

---

## 9. Security and Data Handling

- Store credentials in environment variables or an appropriate secret manager.
- Commit `.env.example`, never a real `.env` containing secrets.
- Never print credentials or tokens in logs.
- Use parameterized SQL.
- Use sanitized sample data.
- Avoid committing private, licensed-restricted, or personally identifiable data.
- Keep test and development databases separate from production data.
- Document any external API terms or data restrictions.
- Do not request client passwords or API secrets through public messages or plain-text project files.

---

## 10. Documentation Requirements

The README must accurately describe:

1. Business problem and objectives
2. Supported and selected data sources
3. Architecture and repository structure
4. Extraction process
5. Transformation rules
6. Validation rules and rejected-record handling
7. PostgreSQL schema
8. Installation and configuration
9. Database setup
10. Execution commands
11. Test commands
12. Actual sample results
13. Known limitations
14. Future improvements

Include architecture diagrams or screenshots only when they reflect the actual implementation.

---

## 11. Fiverr and Portfolio Alignment

Prioritize capabilities that can be offered honestly as freelance services:

- Python ETL pipeline development
- CSV/Excel-to-database automation
- REST API integration
- API-to-PostgreSQL loading
- Multi-source data integration
- Data cleaning and transformation
- Data validation
- Incremental loading
- Logging and error handling

For each major feature, document the client problem it solves, how it works, which Basic/Standard/Premium package it could support, possible add-ons, and limitations to disclose.

Do not claim enterprise-scale capabilities or introduce Airflow, Spark, Kafka, AWS, or complex cloud infrastructure unless a real requirement justifies them and they are implemented and tested.

### Portfolio demonstration

Prepare a short, genuine demonstration showing:

1. The input sources
2. Pipeline execution
3. Transformation and validation
4. PostgreSQL loading
5. Logs and execution status
6. Final database output

Use real application screenshots and actual results. Never fabricate performance claims or business outcomes.

---

## 12. Definition of Done

The project is ready for portfolio use only when:

- Multiple selected sources work end-to-end.
- Transformations and validation behave correctly.
- Invalid records are handled and traceable.
- PostgreSQL loading is verified.
- Repeat execution does not create unintended duplicates.
- Logging and error handling work.
- Unit and relevant integration tests pass.
- Static quality checks pass.
- CI is verified where feasible.
- Documentation matches the actual implementation.
- No known critical bugs remain.
- Limitations are documented.
- Genuine screenshots and a working demo are available.

Do not describe untested features as complete. Clearly report any checks blocked by unavailable services or credentials.

---

## 13. First Action for the AI Assistant

**Inspect the connected GitHub repository. Do not modify any files.**

Return a repository assessment containing:

1. Repository health and existing functionality
2. Current architecture and folder structure
3. Dependencies and configuration
4. Existing tests and their status, if executable
5. Bugs, incomplete work, security concerns, and technical risks
6. A practical business use case suited to the repository
7. Recommended public data sources and their constraints
8. Proposed PostgreSQL schema and relationships
9. Recommended ETL architecture
10. Phased implementation roadmap
11. The first detailed implementation plan, including exact files and tests

Wait for explicit approval before making any repository changes.