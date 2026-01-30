# csvsmith

[![PyPI version](https://img.shields.io/pypi/v/csvsmith.svg)](https://pypi.org/project/csvsmith/)
![Python versions](https://img.shields.io/pypi/pyversions/csvsmith.svg)
[![License](https://img.shields.io/pypi/l/csvsmith.svg)](https://pypi.org/project/csvsmith/)

## Introduction

`csvsmith` is a lightweight collection of CSV utilities designed for
data integrity, deduplication, and organization. It provides a robust
Python API for programmatic data cleaning and a convenient CLI for quick
operations. Whether you need to organize thousands of files based on
their structural signatures or pinpoint duplicate rows in a complex
dataset, `csvsmith` ensures the process is predictable, transparent, and
reversible.

## Table of Contents

-   [Installation](#installation)

-   

    [Python API Usage](#python-api-usage)

    :   -   [Count duplicate values](#count-duplicate-values)
        -   [Find duplicate rows in a
            DataFrame](#find-duplicate-rows-in-a-dataframe)
        -   [Deduplicate with report](#deduplicate-with-report)
        -   [CSV File Classification](#csv-file-classification)

-   

    [CLI Usage](#cli-usage)

    :   -   [Show duplicate rows](#show-duplicate-rows)
        -   [Deduplicate and generate a duplicate
            report](#deduplicate-and-generate-a-duplicate-report)
        -   [Classify CSVs](#classify-csvs)

-   [Philosophy](#philosophy)

-   [License](#license)

## Installation

From PyPI:

``` bash
pip install csvsmith
```

For local development:

``` bash
git clone https://github.com/yeiichi/csvsmith.git
cd csvsmith
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Python API Usage

### Count duplicate values

Works on any iterable of hashable items.

``` python
from csvsmith import count_duplicates_sorted

items = ["a", "b", "a", "c", "a", "b"]
print(count_duplicates_sorted(items))
# [('a', 3), ('b', 2)]
```

### Find duplicate rows in a DataFrame

``` python
import pandas as pd
from csvsmith import find_duplicate_rows

df = pd.read_csv("input.csv")
dup_rows = find_duplicate_rows(df)
print(dup_rows)
```

### Deduplicate with report

``` python
import pandas as pd
from csvsmith import dedupe_with_report

df = pd.read_csv("input.csv")

# Use all columns
deduped, report = dedupe_with_report(df)
deduped.to_csv("deduped.csv", index=False)
report.to_csv("duplicate_report.csv", index=False)

# Use all columns except an ID column
deduped_no_id, report_no_id = dedupe_with_report(df, exclude=["id"])
```

### CSV File Classification

Organize files into directories based on their headers.

``` python
from csvsmith.classify import CSVClassifier

classifier = CSVClassifier(
    source_dir="./raw_data",
    dest_dir="./organized",
    auto=True  # Automatically group files with identical headers
)

# Execute the classification
classifier.run()

# Or rollback a previous run using its manifest
classifier.rollback("./organized/manifest_20260121_120000.json")
```

## CLI Usage

`csvsmith` includes a command-line interface for duplicate detection and
file organization.

### Show duplicate rows

``` bash
csvsmith row-duplicates input.csv
```

Save only duplicate rows to a file:

``` bash
csvsmith row-duplicates input.csv -o duplicates_only.csv
```

### Deduplicate and generate a duplicate report

``` bash
csvsmith dedupe input.csv --deduped deduped.csv --report duplicate_report.csv
```

### Classify CSVs

Organize a mess of CSV files into structured folders based on their
column headers.

``` bash
# Preview what would happen (Dry Run)
csvsmith classify --src ./raw_data --dest ./organized --auto --dry-run

# Run classification with a signature config
csvsmith classify --src ./raw_data --dest ./organized --config signatures.json

# Undo a classification run
csvsmith classify --rollback ./organized/manifest_20260121_120000.json
```

## Philosophy

1.  CSVs deserve tools that are simple, predictable, and transparent.
2.  A row has meaning only when its identity is stable and hashable.
3.  Collisions are sin; determinism is virtue.
4.  Let no delimiter sow ambiguity among fields.
5.  **Love thy \\x1f.** The unseen separator, the quiet guardian of
    clean hashes.
6.  The pipeline should be silent unless something is wrong.
7.  Your data deserves respect --- and your tools should help you give
    it.

For more, see `MANIFESTO.md`.

## License

MIT License.
