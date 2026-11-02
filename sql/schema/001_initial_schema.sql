BEGIN;

CREATE TABLE etl_runs (
    run_id UUID PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'succeeded', 'partial', 'failed')),
    records_extracted BIGINT NOT NULL DEFAULT 0 CHECK (records_extracted >= 0),
    records_accepted BIGINT NOT NULL DEFAULT 0 CHECK (records_accepted >= 0),
    records_rejected BIGINT NOT NULL DEFAULT 0 CHECK (records_rejected >= 0),
    records_loaded BIGINT NOT NULL DEFAULT 0 CHECK (records_loaded >= 0),
    error_message TEXT,
    CONSTRAINT etl_runs_finished_after_started
        CHECK (finished_at IS NULL OR finished_at >= started_at)
);

CREATE TABLE source_files (
    source_file_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES etl_runs (run_id),
    source_name TEXT NOT NULL,
    source_format TEXT NOT NULL
        CHECK (source_format IN ('csv', 'excel', 'json', 'api', 'database', 'other')),
    file_name TEXT,
    source_location TEXT,
    checksum_sha256 CHAR(64),
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'succeeded', 'partial', 'failed')),
    records_extracted BIGINT NOT NULL DEFAULT 0 CHECK (records_extracted >= 0),
    error_message TEXT,
    CONSTRAINT source_files_checksum_length
        CHECK (checksum_sha256 IS NULL OR length(checksum_sha256) = 64)
);

CREATE INDEX idx_source_files_run_id ON source_files (run_id);
CREATE INDEX idx_source_files_checksum ON source_files (checksum_sha256);

CREATE TABLE stg_retail_transactions (
    staging_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES etl_runs (run_id),
    source_file_id BIGINT NOT NULL REFERENCES source_files (source_file_id),
    source_row_number BIGINT NOT NULL CHECK (source_row_number > 0),
    raw_payload JSONB NOT NULL,
    invoice_no TEXT,
    stock_code TEXT,
    product_description TEXT,
    quantity INTEGER,
    invoice_at TIMESTAMP,
    unit_price_gbp NUMERIC(18, 4),
    customer_id TEXT,
    customer_country TEXT,
    is_cancellation BOOLEAN,
    line_amount_gbp NUMERIC(18, 4),
    processing_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (processing_status IN ('pending', 'valid', 'rejected')),
    CONSTRAINT stg_retail_transactions_source_row_unique
        UNIQUE (source_file_id, source_row_number)
);

CREATE INDEX idx_stg_retail_transactions_run_id
    ON stg_retail_transactions (run_id);
CREATE INDEX idx_stg_retail_transactions_invoice_no
    ON stg_retail_transactions (invoice_no);
CREATE INDEX idx_stg_retail_transactions_stock_code
    ON stg_retail_transactions (stock_code);

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    display_name TEXT,
    customer_segment TEXT,
    customer_country TEXT,
    reference_matched BOOLEAN NOT NULL DEFAULT FALSE,
    metadata_is_synthetic BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE products (
    stock_code TEXT PRIMARY KEY,
    product_description TEXT,
    product_category TEXT,
    supplier_code TEXT,
    supplier_name TEXT,
    reference_matched BOOLEAN NOT NULL DEFAULT FALSE,
    metadata_is_synthetic BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE invoices (
    invoice_no TEXT PRIMARY KEY,
    invoice_at TIMESTAMP NOT NULL,
    customer_id TEXT REFERENCES customers (customer_id),
    customer_country TEXT,
    is_cancellation BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_invoices_invoice_at ON invoices (invoice_at);
CREATE INDEX idx_invoices_customer_id ON invoices (customer_id);

CREATE TABLE invoice_lines (
    invoice_line_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_no TEXT NOT NULL REFERENCES invoices (invoice_no),
    source_file_id BIGINT NOT NULL REFERENCES source_files (source_file_id),
    source_row_number BIGINT NOT NULL CHECK (source_row_number > 0),
    stock_code TEXT NOT NULL REFERENCES products (stock_code),
    product_description TEXT,
    quantity INTEGER NOT NULL,
    unit_price_gbp NUMERIC(18, 4) NOT NULL,
    line_amount_gbp NUMERIC(18, 4) NOT NULL,
    CONSTRAINT invoice_lines_source_row_unique
        UNIQUE (source_file_id, source_row_number)
);

CREATE INDEX idx_invoice_lines_invoice_no ON invoice_lines (invoice_no);
CREATE INDEX idx_invoice_lines_stock_code ON invoice_lines (stock_code);

CREATE TABLE exchange_rates (
    rate_date DATE NOT NULL,
    base_currency CHAR(3) NOT NULL,
    quote_currency CHAR(3) NOT NULL,
    provider_key TEXT NOT NULL DEFAULT 'frankfurter-default',
    exchange_rate NUMERIC(20, 10) NOT NULL CHECK (exchange_rate > 0),
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    provider_metadata JSONB,
    PRIMARY KEY (rate_date, base_currency, quote_currency, provider_key),
    CONSTRAINT exchange_rates_distinct_currencies
        CHECK (base_currency <> quote_currency)
);

CREATE TABLE rejected_records (
    rejection_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES etl_runs (run_id),
    source_file_id BIGINT REFERENCES source_files (source_file_id),
    source_name TEXT NOT NULL,
    source_row_number BIGINT CHECK (source_row_number IS NULL OR source_row_number > 0),
    source_record JSONB NOT NULL,
    reason_codes TEXT[] NOT NULL,
    rejection_message TEXT,
    rejected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rejected_records_run_id ON rejected_records (run_id);
CREATE INDEX idx_rejected_records_source_file_id
    ON rejected_records (source_file_id);

COMMIT;
