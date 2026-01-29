# Topsis-Prabhpreet-102303258

A Python package implementing **TOPSIS** (Technique for Order Preference by Similarity to Ideal Solution) for multi-criteria decision analysis.

[![PyPI version](https://badge.fury.io/py/Topsis-Prabhpreet-102303258.svg)](https://pypi.org/project/Topsis-Prabhpreet-102303258/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Package Structure

```
Topsis-Prabhpreet-102303258/
│
├── topsis_prabhpreet_102303258/
│   ├── __init__.py
│   └── topsis.py
│
├── README.md
├── requirements.txt
├── pyproject.toml
├── LICENSE
└── sample_data.csv
```

---

### How TOPSIS Works

1. **Normalize** the decision matrix using vector normalization
2. **Weight** the normalized matrix with user-defined weights
3. **Identify** ideal best and ideal worst solutions for each criterion
4. **Calculate** Euclidean distances from ideal solutions
5. **Compute** relative closeness score (TOPSIS Score)
6. **Rank** alternatives based on their scores (higher = better)

---

## Installation

### From PyPI (Recommended)

```bash
pip install Topsis-Prabhpreet-102303258
```

### From Source

```bash
git clone https://github.com/PrabhpreetSingh/Topsis-Prabhpreet-102303258.git
cd Topsis-Prabhpreet-102303258
pip install .
```

---

## Command-Line Usage

### Syntax

```bash
topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
```

### Parameters

| Parameter | Description |
|-----------|-------------|
| `InputDataFile` | Path to input CSV file containing the decision matrix |
| `Weights` | Comma-separated numeric weights for each criterion |
| `Impacts` | Comma-separated impacts: `+` (beneficial) or `-` (non-beneficial) |
| `OutputResultFileName` | Path for the output CSV file with results |

### Example

```bash
topsis sample_data.csv "1,1,1,2" "+,+,-,+" result.csv
```

This command:
- Reads `sample_data.csv` as input
- Applies weights `[1, 1, 1, 2]` to four criteria
- Uses impacts `[+, +, -, +]` (maximize 1st, 2nd, 4th; minimize 3rd)
- Saves results to `result.csv`

---

## Input File Format

The input CSV file must follow this structure:

```csv
Object,Criterion1,Criterion2,Criterion3,Criterion4
M1,0.79,0.62,1.25,38.5
M2,0.66,0.44,2.89,63.7
M3,0.56,0.31,1.57,42.1
M4,0.82,0.67,2.68,74.2
M5,0.75,0.56,1.83,51.9
```

### Requirements

- **First column**: Object/alternative names (can be text)
- **Columns 2 onwards**: Numeric criteria values only
- **Minimum**: 3 columns total (1 name + 2 criteria)

---

## Output Description

The output CSV contains all original columns plus:

| Column | Description |
|--------|-------------|
| `Topsis Score` | Relative closeness coefficient (0 to 1, higher is better) |
| `Rank` | Ranking position (1 = best) |

### Example Output

```csv
Model,Corr,R2,RMSE,Accuracy,Topsis Score,Rank
M1,0.79,0.62,1.25,38.5,0.534,3
M2,0.66,0.44,2.89,63.7,0.308,5
M3,0.56,0.31,1.57,42.1,0.373,4
M4,0.82,0.67,2.68,74.2,0.695,1
M5,0.75,0.56,1.83,51.9,0.535,2
```

---

## Error Handling

The program validates all inputs and provides clear error messages:

| Error | Cause |
|-------|-------|
| `Incorrect number of parameters` | Not exactly 4 command-line arguments provided |
| `Input file not found` | Specified input file does not exist |
| `Must contain at least three columns` | Input file has fewer than 3 columns |
| `Must contain numeric values only` | Non-numeric values found in criteria columns |
| `Number of weights must equal criteria` | Mismatch between weights and number of criteria |
| `Number of impacts must equal criteria` | Mismatch between impacts and number of criteria |
| `Impact must be '+' or '-'` | Invalid impact character used |

### Example Error Messages

```bash
# Wrong number of arguments
$ topsis data.csv "1,1,1"
Error: Incorrect number of parameters.
Usage: topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>

# File not found
$ topsis missing.csv "1,1,1,1" "+,+,-,+" out.csv
Error: Input file 'missing.csv' not found.

# Invalid impact
$ topsis data.csv "1,1,1,1" "+,+,x,+" out.csv
Error: Impact at position 3 must be '+' or '-', got 'x'.
```

---

## Complete Example

### Step 1: Create Input File

Create `data.csv`:

```csv
Model,Corr,R2,RMSE,Accuracy
M1,0.79,0.62,1.25,38.5
M2,0.66,0.44,2.89,63.7
M3,0.56,0.31,1.57,42.1
M4,0.82,0.67,2.68,74.2
M5,0.75,0.56,1.83,51.9
```

### Step 2: Run TOPSIS

```bash
topsis data.csv "1,1,1,2" "+,+,-,+" result.csv
```

**Explanation:**
- **Corr** (weight=1, impact=+): Higher correlation is better
- **R2** (weight=1, impact=+): Higher R² is better
- **RMSE** (weight=1, impact=-): Lower RMSE is better
- **Accuracy** (weight=2, impact=+): Higher accuracy is better (double weight)

### Step 3: View Results

```bash
cat result.csv
```

Output shows M4 ranked #1 with highest TOPSIS score.

---

## Dependencies

- Python >= 3.8
- pandas >= 1.3.0
- numpy >= 1.21.0

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Author

**Prabhpreet Singh**  
Roll Number: 102303258  
Thapar Institute of Engineering and Technology  
Email: psingh4_be23@thapar.edu

---

## Links

- **PyPI**: https://pypi.org/project/Topsis-Prabhpreet-102303258/
- **GitHub**: https://github.com/PrabhpreetSingh/Topsis-Prabhpreet-102303258
