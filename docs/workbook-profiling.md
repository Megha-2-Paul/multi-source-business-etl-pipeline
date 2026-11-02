# UCI workbook profiling

The workbook profile is a discovery step, not a transformation. It records the
workbook's actual worksheet names, reported dimensions, physical header values
and positions, row/column emptiness, observed value types, null counts, and a
small sample of source rows. It does not rename columns or infer business rules.

## Download and place the source workbook

Download the UCI Online Retail II workbook from the
[official UCI dataset page](https://archive.ics.uci.edu/dataset/502/online+retail+ii).
Save it locally as:

    data/raw/online_retail_II.xlsx

The workbook is excluded by .gitignore. Do not commit it or include it in a
pull request.

## Run the profiler

From the repository root in PowerShell:

    python -m etl_pipeline.utils.workbook_profile data/raw/online_retail_II.xlsx

The default report is written to
data/processed/workbook_profile.json, which is also excluded by Git. To
choose another report location or adjust the sample size:

    python -m etl_pipeline.utils.workbook_profile data/raw/online_retail_II.xlsx --output data/processed/retail_profile.json --sample-rows 5

The profiler uses openpyxl read-only mode and iterates worksheet rows rather
than loading the workbook into pandas. The report stores only the source
filename, structural metadata, and the configured number of example rows; it
does not copy the workbook.

## Interpreting the report

- headers lists each physical header position and its original value.
  Blank and repeated header names are preserved; positions are authoritative.
- columns reports non-empty counts, null counts, observed value types, and
  whether a column is entirely empty. Date-like Excel cells are identified
  using their cell formatting; numeric-looking identifiers remain numeric if
  that is how the workbook stores them.
- sample_rows contains at most the requested number of non-empty rows, with
  physical worksheet row numbers and original column positions.
- empty_data_rows counts blank rows after the header.
- duplicate_analysis counts exact duplicate full rows and repeated
  non-empty values per column within the first 100,000 non-empty data rows by
  default. This analysis is intentionally bounded to limit memory use. It is
  a discovery signal, not proof of a business key or duplicate transaction.
- Worksheet dimensions are the dimensions reported by the workbook metadata;
  actual scanned row counts are reported separately.

Review the JSON report before designing source-specific transformations.
Preserve the original header labels and source-row lineage in any subsequent
mapping. Do not drop cancellations, negative quantities, missing customer
identifiers, or unmatched reference records based only on profiling results.
