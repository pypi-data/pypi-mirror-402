# Topsis-Kshitiz-102303748 User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Input File Format](#input-file-format)
5. [Parameters](#parameters)
6. [Examples](#examples)
7. [Error Handling](#error-handling)
8. [Troubleshooting](#troubleshooting)

---

## Introduction

**TOPSIS** (Technique for Order of Preference by Similarity to Ideal Solution) is a multi-criteria decision analysis method. This package provides a command-line tool that:

- Performs TOPSIS analysis on CSV data
- Automatically handles categorical columns (converts them to numeric)
- Validates all inputs comprehensively
- Generates ranked results with TOPSIS scores

---

## Installation

### From PyPI

```bash
pip install Topsis-Kshitiz-102303748
```

### From Source

```bash
git clone <repository-url>
cd Topsis
pip install -e .
```

### Verify Installation

```bash
topsis-kshitiz-102303748 --version
```

---

## Usage

### Basic Syntax

```bash
topsis-kshitiz-102303748 <InputDataFile> <Weights> <Impacts> <OutputResultFile>
```

### Parameters Format

- **InputDataFile**: Path to input CSV file
- **Weights**: Comma-separated numeric values (e.g., "1,1,2,1")
- **Impacts**: Comma-separated '+' or '-' symbols (e.g., "+,+,-,+")
- **OutputResultFile**: Path for output CSV file

**Important**: Weights and impacts must be enclosed in quotes if using command line.

---

## Input File Format

### Requirements

1. **Minimum 3 columns** (1 identifier column + at least 2 criteria columns)
2. **First column**: Name/identifier (string)
3. **Remaining columns**: Criteria values (numeric or categorical)

### Example CSV Structure

```csv
Product,Price,Storage,Camera,Battery,Rating
Phone_A,299,64,12,3500,Good
Phone_B,450,128,48,4200,Excellent
Phone_C,199,32,8,3000,Average
```

### Categorical Columns

The tool automatically converts categorical columns to numeric values:

**Ordinal Detection** (automatically recognized):

- low, medium, high → 1, 2, 3
- poor, average, good, excellent → 1, 2, 3, 4
- bad, ok, great → 1, 2, 3
- small, large → 1, 2
- yes, no → 1, 0

**Label Encoding** (for other categories):

- Categories are converted to numbers based on alphabetical order
- Example: Red, Blue, Green → 1, 2, 3

---

## Parameters

### Weights

- **Purpose**: Assign importance to each criterion
- **Format**: Comma-separated numbers
- **Example**: "1,1,2,1" means 3rd criterion has double importance
- **Count**: Must match number of criteria columns

### Impacts

- **Purpose**: Define if higher or lower values are better
- **Format**: Comma-separated '+' or '-' symbols
- **Meaning**:
  - `+` : Higher values are better (e.g., Storage, Battery)
  - `-` : Lower values are better (e.g., Price, Weight)
- **Example**: "+,+,-,+" for [Storage, Camera, Price, Battery]
- **Count**: Must match number of criteria columns

---

## Examples

### Example 1: Basic Usage

**Input file** (phones.csv):

```csv
Product,Price,Storage,Camera,Battery
Phone_A,299,64,12,3500
Phone_B,450,128,48,4200
Phone_C,199,32,8,3000
```

**Command**:

```bash
topsis-kshitiz-102303748 phones.csv "1,2,3,2" "-,+,+,+" results.csv
```

**Explanation**:

- Price: weight=1, impact='-' (lower is better)
- Storage: weight=2, impact='+' (higher is better)
- Camera: weight=3, impact='+' (highest priority)
- Battery: weight=2, impact='+' (higher is better)

**Output** (results.csv):

```csv
Product,Price,Storage,Camera,Battery,Topsis Score,Rank
Phone_B,450,128,48,4200,0.82,1
Phone_A,299,64,12,3500,0.54,2
Phone_C,199,32,8,3000,0.31,3
```

### Example 2: With Categorical Data

**Input file** (products.csv):

```csv
Product,Price,Quality,Size,Availability
Item_A,100,Good,Large,Yes
Item_B,150,Excellent,Small,Yes
Item_C,80,Average,Large,No
```

**Command**:

```bash
topsis-kshitiz-102303748 products.csv "1,2,1,1" "-,+,+,+" results.csv
```

The tool will automatically convert:

- Quality: Good→3, Excellent→4, Average→2
- Size: Large→2, Small→1
- Availability: Yes→1, No→0

### Example 3: Equal Weights

**Command**:

```bash
topsis-kshitiz-102303748 data.csv "1,1,1,1,1" "+,+,-,+,+" output.csv
```

All criteria have equal importance.

---

## Error Handling

The tool validates all inputs and provides clear error messages:

### Common Errors

**1. Incorrect Number of Parameters**

```
Error: Incorrect number of parameters.
Usage: python <program.py> <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
```

**Solution**: Provide exactly 4 arguments

**2. File Not Found**

```
Error: File 'data.csv' not found.
```

**Solution**: Check file path and spelling

**3. Too Few Columns**

```
Error: Input file must contain three or more columns.
```

**Solution**: Ensure CSV has at least 3 columns (1 name + 2 criteria)

**4. Non-Numeric Values**

```
Error: Column 'Price' contains non-numeric values that cannot be converted.
```

**Solution**: Check for invalid entries in numeric columns

**5. Mismatched Counts**

```
Error: Number of weights and impacts must match number of criteria (5).
```

**Solution**: Provide 5 weights and 5 impacts for 5 criteria columns

**6. Invalid Impact**

```
Error: Impacts must be either '+' or '-'
```

**Solution**: Use only '+' or '-' symbols in impacts

**7. Invalid Weights**

```
Error: Weights must be numeric values separated by commas.
```

**Solution**: Ensure weights are numbers: "1,2,3" not "1, two, 3"

---

## Troubleshooting

### Issue: Command not found

**Problem**: `topsis-kshitiz-102303748: command not found`

**Solutions**:

1. Reinstall package: `pip install --force-reinstall Topsis-Kshitiz-102303748`
2. Check if pip bin directory is in PATH
3. Use full path: `python -m topsis_kshitiz_102303748.topsis`

### Issue: Import errors

**Problem**: `ModuleNotFoundError: No module named 'pandas'`

**Solution**: Install dependencies manually:

```bash
pip install pandas numpy
```

### Issue: Wrong results

**Problem**: Rankings don't seem correct

**Checklist**:

1. Verify impacts ('+' vs '-') are correct for each criterion
2. Check if categorical values were converted as expected
3. Ensure weights reflect actual importance
4. Verify no missing/invalid values in input data

### Issue: Permission denied

**Problem**: `PermissionError: [Errno 13] Permission denied`

**Solution**: Close output file if open in another program, or use different filename

---

## Algorithm Overview

TOPSIS works in 5 steps:

1. **Normalization**: Vector normalization of decision matrix
2. **Weighting**: Multiply normalized values by weights
3. **Ideal Solutions**: Find best and worst values per criterion
4. **Distance Calculation**: Euclidean distance to ideal best/worst
5. **Scoring**: Score = distance_to_worst / (distance_to_best + distance_to_worst)

Higher score = better alternative (closer to ideal solution)

---

## Support

For issues, questions, or contributions:

- GitHub: [repository-url]
- Email: [your-email]
- PyPI: https://pypi.org/project/Topsis-Kshitiz-102303748/

---

## License

MIT License - see LICENSE file for details.

## Version

Current version: 0.1.0
