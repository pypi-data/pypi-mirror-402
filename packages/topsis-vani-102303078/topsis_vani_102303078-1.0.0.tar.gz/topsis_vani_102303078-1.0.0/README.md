# Topsis-Vani-102303078

[![PyPI version](https://badge.fury.io/py/Topsis-Vani-102303078.svg)](https://badge.fury.io/py/Topsis-Vani-102303078)
[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python package implementing TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) for multi-criteria decision making.

**Author:** Vani Goyal  
**Roll Number:** 102303078  
**Email:** vgoyal_be23@thapar.edu

## What is TOPSIS?

TOPSIS is a multi-criteria decision analysis method that identifies the best alternative by calculating the geometric distance from the ideal solution and the negative-ideal solution.

## Installation

```bash
pip install Topsis-Vani-102303078
```

## Usage

### Command Line Interface

```bash
topsis <InputDataFile> <Weights> <Impacts> <OutputFileName>
```

### Example

```bash
topsis data.csv "1,1,1,2" "+,+,-,+" result.csv
```

### Python Module

```python
from topsis_vani_102303078 import topsis

topsis('input.csv', '1,1,1,2', '+,+,-,+', 'output.csv')
```

## Input Format

CSV file with:
- **Column 1:** Alternative names/IDs
- **Columns 2-N:** Numeric criteria values

Example:
```csv
Fund Name,P1,P2,P3,P4,P5
M1,0.84,0.71,6.7,42.1,12.59
M2,0.91,0.83,7.0,31.7,10.11
```

## Parameters

### Weights
Comma-separated positive numbers (e.g., `"1,1,1,2"`)

### Impacts
Comma-separated `+` or `-` signs:
- `+` : Higher values are better (benefit criterion)
- `-` : Lower values are better (cost criterion)

Example: `"+,+,-,+"` means maximize P1, P2, P4 and minimize P3

## Output

CSV file with original data plus:
- **Topsis Score:** Performance score (0-100, higher is better)
- **Rank:** Final ranking (1 is best)

## Algorithm Steps

1. **Normalization:** Vector normalization of decision matrix
2. **Weighted Matrix:** Apply criterion weights  
3. **Ideal Solutions:** Identify best and worst solutions
4. **Distance Calculation:** Euclidean distances from ideals
5. **TOPSIS Score:** Closeness coefficient calculation
6. **Ranking:** Sort by TOPSIS score

## Requirements

- Python >= 3.7
- pandas >= 1.0.0
- numpy >= 1.18.0

## License

MIT License - see LICENSE file

## Links

- **GitHub:** https://github.com/vgalpha/Topsis-Vani-102303078
- **PyPI:** https://pypi.org/project/Topsis-Vani-102303078/

## Author

Vani Goyal  
Roll Number: 102303078  
Thapar Institute of Engineering & Technology  
Email: vgoyal_be23@thapar.edu
