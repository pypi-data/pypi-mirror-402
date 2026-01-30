# Topsis-Kshitiz-102303748

TOPSIS command-line tool with automatic handling of categorical columns (ordinal detection + label encoding fallback).

## Installation

```bash
pip install Topsis-Kshitiz-102303748
```

## Quick Start

```bash
topsis-kshitiz-102303748 input.csv "1,1,2,1" "+,+,-,+" output.csv
```

## Features

- ✅ Multi-criteria decision analysis using TOPSIS
- ✅ Automatic categorical-to-numeric conversion
- ✅ Comprehensive input validation
- ✅ Clear error messages
- ✅ Support for any number of criteria

## Basic Usage

```bash
topsis-kshitiz-102303748 <InputFile.csv> <Weights> <Impacts> <OutputFile.csv>
```

**Example:**

```bash
topsis-kshitiz-102303748 data.csv "1,1,1,2,1" "+,+,-,+,+" results.csv
```

## Input Format

CSV file with:

- First column: Name/identifier
- Remaining columns: Criteria (numeric or categorical)
- Minimum 3 columns required

## Parameters

- **Weights**: Comma-separated numbers (e.g., "1,2,1")
- **Impacts**: '+' (higher is better) or '-' (lower is better)
- Both must match the number of criteria columns

## For Developers

### Build from source

```bash
pip install build twine
python -m build
```

### Upload to PyPI

```bash
twine upload --repository testpypi dist/*
twine upload dist/*
```

## License

MIT License

## Version

0.1.2
