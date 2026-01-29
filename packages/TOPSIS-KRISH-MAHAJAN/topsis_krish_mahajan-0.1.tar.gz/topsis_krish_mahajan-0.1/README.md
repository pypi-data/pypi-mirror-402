# TOPSIS Package

A Python implementation of **TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)** - a Multi-Criteria Decision Making (MCDM) method for ranking alternatives based on multiple criteria.

## Overview

TOPSIS helps you select the best alternative from multiple options by comparing them across various criteria. It considers both benefit criteria (higher is better) and cost criteria (lower is better).

## Installation

### Prerequisites
- Python 3.4 or higher
- pandas >= 0.23.0
- numpy >= 1.14.0

### Install via pip
```bash
pip install TOPSIS-KRISH-MAHAJAN
```

### Install from source
```bash
git clone https://github.com/krishmahajan7/TOPSIS-KRSH-MAHAJAN-102303139.git
cd TOPSIS-KRSH-MAHAJAN-102303139
pip install -r requirements.txt
python setup.py install
```

## Usage

### Basic Example

```python
from TOPSIS_KRISH_MAHAJAN import TOPSIS

topsis = TOPSIS()

topsis.topsis(
    input_file='data.csv',
    weights='1,2,1,3',
    impacts='+,+,-,+',
    result_file='results.csv'
)
```

### Parameters

- **input_file**: Path to input CSV file
- **weights**: Comma-separated weights for each criterion (string or list)
- **impacts**: '+' for benefit criteria, '-' for cost criteria (string or list)
- **result_file**: Path where output CSV will be saved

### Input File Format

```
Alternative,Criterion1,Criterion2,Criterion3
Option_A,5,3,6
Option_B,6,4,5
Option_C,7,2,7
```

- First column: Alternative names (non-numeric)
- Other columns: Numeric criterion values
- Minimum 3 columns required (1 alternative + 2 criteria)

### Output File Format

```
Alternative,Criterion1,Criterion2,Criterion3,Topsis_Score,Rank
Option_A,5,3,6,0.564,2
Option_B,6,4,5,0.628,1
Option_C,7,2,7,0.542,3
```

- **Topsis_Score**: Similarity to ideal solution (0-1, higher is better)
- **Rank**: Position in the ranking (1 = best)

## Error Handling

The package validates:
- Input file exists
- At least 3 columns in CSV
- Numeric values in criteria columns
- Correct number of weights
- Correct number of impacts

## Supported Python Versions

- Python 3.4, 3.5, 3.6, 3.7, 3.8

## License

MIT License - See LICENSE.txt for details

## Author

**Krish Mahajan** (Roll No: 102303139)
- GitHub: [@krishmahajan7](https://github.com/krishmahajan7)

## Repository

[TOPSIS-KRSH-MAHAJAN-102303139](https://github.com/krishmahajan7/TOPSIS-KRSH-MAHAJAN-102303139)

