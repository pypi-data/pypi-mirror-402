# Topsis-Lakshita-102303505

[![PyPI version](https://img.shields.io/pypi/v/Topsis-Lakshita-102303505.svg)](https://pypi.org/project/Topsis-Lakshita-102303505/)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution)** - A Python package for multi-criteria decision analysis.

## What is TOPSIS?

TOPSIS is a multi-criteria decision analysis method that identifies the alternative closest to the ideal solution and farthest from the negative-ideal solution. The ideal solution maximizes benefit criteria and minimizes cost criteria.

## Installation

```bash
pip install Topsis-Lakshita-102303505
```

## Usage

### Command Line

```bash
topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
```

### Examples

```bash
# Example 1: Equal weights, all positive impacts
topsis data.csv "1,1,1,1,1" "+,+,+,+,+" output.csv

# Example 2: Different weights, mixed impacts
topsis data.csv "2,1,3,1,2" "+,+,-,+,+" results.csv

# Example 3: Using Excel file
topsis data.xlsx "1,1,1,2" "+,+,-,+" output.csv
```

### Python API

```python
from Topsis_Lakshita_102303505 import topsis_analysis

result_df = topsis_analysis(
    input_file='data.csv',
    weights='1,1,1,2',
    impacts='+,+,-,+',
    output_file='output.csv'
)

print(result_df)
```

## Input File Format

The input file (CSV or Excel) must have:
- **At least 3 columns**: 1 name column + 2 or more criteria columns
- **First column**: Alternative names (text)
- **Remaining columns**: Numeric criteria values only

**Example:**

| Model | Price | Storage | Camera | Looks |
|-------|-------|---------|--------|-------|
| M1    | 250   | 16      | 12     | 5     |
| M2    | 200   | 16      | 8      | 3     |
| M3    | 300   | 32      | 16     | 4     |

## Parameters

- **Weights**: Comma-separated numeric values (e.g., `"1,1,1,2"`)
  - Must match the number of criteria columns
  
- **Impacts**: Comma-separated `+` or `-` signs (e.g., `"+,+,-,+"`)
  - `+` for beneficial criteria (higher is better)
  - `-` for cost criteria (lower is better)
  - Must match the number of criteria columns

## Output

The output CSV file contains all original columns plus:
- **Topsis Score**: Performance score (0-1 range, higher is better)
- **Rank**: Integer ranking (1 = best alternative)

**Example Output:**

| Model | Price | Storage | Camera | Looks | Topsis Score | Rank |
|-------|-------|---------|--------|-------|--------------|------|
| M3    | 300   | 32      | 16     | 4     | 0.691        | 1    |
| M1    | 250   | 16      | 12     | 5     | 0.534        | 2    |
| M2    | 200   | 16      | 8      | 3     | 0.308        | 3    |

## Error Handling

The package validates:
- ✅ File existence
- ✅ Minimum 3 columns
- ✅ Numeric values in criteria columns
- ✅ Matching counts of weights, impacts, and criteria
- ✅ Valid impact signs (+ or -)
- ✅ Proper comma separation

## Algorithm Steps

1. **Normalize** the decision matrix using vector normalization
2. **Apply weights** to normalized values
3. **Identify ideal solutions** (best and worst)
4. **Calculate Euclidean distances** from ideal solutions
5. **Compute performance scores**
6. **Rank alternatives** based on scores

## Dependencies

- pandas >= 1.0.0
- numpy >= 1.18.0
- openpyxl >= 3.0.0 (for Excel support)

## License

MIT License - See [LICENSE](LICENSE) file for details

## Author

**Lakshita Gupta**  
Email: lakshitagupta0518@gmail.com  
Roll Number: 102303505

## Links

- **PyPI**: https://pypi.org/project/Topsis-Lakshita-102303505/
- **GitHub**: https://github.com/Lakshita018/topsis

## Version

**1.0.0** (2026-01-20)
- Initial release
- TOPSIS algorithm implementation
- CSV and Excel file support
- Command-line interface
- Python API
- Comprehensive error handling

---

For detailed documentation, examples, and troubleshooting, visit the [GitHub repository](https://github.com/Lakshita018/topsis).


