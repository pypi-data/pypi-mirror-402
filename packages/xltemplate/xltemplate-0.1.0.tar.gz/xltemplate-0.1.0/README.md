# xltemplate

A lightweight Python wrapper around openpyxl that provides a clean, stateful OOP interface for populating Excel templates with DataFrames while preserving formatting.

## Installation

```bash
pip install xltemplate              # Core only
pip install xltemplate[pandas]      # With Pandas support
pip install xltemplate[polars]      # With Polars support
pip install xltemplate[all]         # With both
```

## Quick Start

```python
from xltemplate import Workbook
import pandas as pd

# Load an existing template
wb = Workbook("template.xlsx")

# Write a DataFrame starting at row 5, column 2
df = pd.DataFrame({"Name": ["Alice", "Bob"], "Score": [95, 87]})
wb.sheet("Summary").write_df(df, row=5, col=2)

# Save to a new file
wb.save("output.xlsx")
```

## Features

- **First-class Pandas & Polars support** — Pass either DataFrame type to `write_df()`
- **Format preservation** — Existing cell styles are preserved by default
- **Formula preservation** — Cells containing formulas are skipped by default
- **Clean API** — Stateful, chainable methods inspired by R's openxlsx

## API Reference

### Workbook

```python
wb = Workbook("template.xlsx")      # Load existing workbook
wb.sheet("SheetName")               # Get Sheet object
wb.sheet_names                      # List all sheet names
wb.save("output.xlsx")              # Save to file
```

### Sheet

```python
sheet = wb.sheet("Data")

# Write DataFrame
sheet.write_df(
    df,
    row=1,                    # Starting row (1-indexed)
    col=1,                    # Starting column (1-indexed)
    headers=True,             # Include column headers (default: True)
    preserve_format=True,     # Keep existing cell formatting (default: True)
    preserve_formulas=True    # Skip cells with formulas (default: True)
)

# Write single value
sheet.write_value("Hello", row=1, col=1)

# Get sheet name
sheet.name
```

## License

MIT
