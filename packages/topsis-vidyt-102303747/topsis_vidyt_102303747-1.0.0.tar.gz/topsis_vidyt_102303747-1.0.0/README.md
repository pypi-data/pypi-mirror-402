# TOPSIS Implementation

**TOPSIS** (Technique for Order of Preference by Similarity to Ideal Solution) is a multi-criteria decision-making algorithm that ranks alternatives based on their closeness to an ideal solution.

## Installation

```bash
pip install topsis-vidyt-102303747
```

## Usage

### Command Line

```bash
python -m topsis_package <InputDataFile> <Weights> <Impacts> <OutputResultFile>
```

#### Arguments:
- **InputDataFile**: CSV or XLSX file with data (first column: identifiers, rest: numeric criteria)
- **Weights**: Comma-separated numeric weights (e.g., "0.2,0.2,0.2,0.2,0.2")
- **Impacts**: Comma-separated impacts: '+' for benefit, '-' for cost (e.g., "+,+,+,-,+")
- **OutputResultFile**: Output CSV file name

#### Example:
```bash
python -m topsis_package data.xlsx "0.2,0.2,0.2,0.2,0.2" "+,+,+,+,+" output.csv
```

### Python Code

```python
import numpy as np
from topsis_package import topsis

# Data: 8 alternatives, 5 criteria
data = np.array([
    [0.67, 0.45, 6.5, 42.0, 12.56],
    [0.60, 0.36, 3.3, 53.3, 14.47],
    [0.82, 0.67, 3.6, 38.0, 17.1],
    [0.60, 0.36, 3.5, 60.9, 18.42],
    [0.76, 0.58, 4.8, 43.0, 12.29],
    [0.69, 0.48, 6.6, 48.7, 14.12],
    [0.79, 0.62, 4.8, 59.2, 16.35],
    [0.84, 0.71, 6.5, 34.5, 10.64],
])

weights = [0.2, 0.2, 0.2, 0.2, 0.2]
impacts = ["+", "+", "+", "+", "+"]

result = topsis(data, weights, impacts)
print("Scores:", result.scores)
print("Ranks:", result.ranks)
```

## Input File Format

### CSV Example (data.csv):
```
Fund_Name,P1,P2,P3,P4,P5
M1,0.67,0.45,6.5,42.0,12.56
M2,0.60,0.36,3.3,53.3,14.47
M3,0.82,0.67,3.6,38.0,17.1
```

### XLSX Example:
Same structure, saved as .xlsx file.

## Output Format

Output CSV includes original columns plus:
- **Topsis Score**: Closeness coefficient (0 to 1, higher is better)
- **Rank**: 1-based ranking (1 is best)

### Example Output (output.csv):
```
Fund_Name,P1,P2,P3,P4,P5,Topsis Score,Rank
M1,0.67,0.45,6.5,42.0,12.56,0.650000,2
M2,0.60,0.36,3.3,53.3,14.47,0.480000,5
M3,0.82,0.67,3.6,38.0,17.1,0.720000,1
```

## Validation Rules

The program validates:
- ✓ Correct number of CLI arguments
- ✓ Weights are numeric and comma-separated
- ✓ Impacts are '+' or '-' only
- ✓ Input file exists (File not found handling)
- ✓ Input file has ≥3 columns (ID + ≥2 criteria)
- ✓ All criteria columns contain numeric values only
- ✓ Number of weights = number of impacts = number of criteria columns
- ✓ Input file has at least one data row

## TOPSIS Algorithm Steps

1. **Normalize** the decision matrix using vector normalization
2. **Weight** each normalized column
3. **Determine ideal best and worst** based on impact type (+ or -)
4. **Calculate distances** from each alternative to ideal best/worst
5. **Compute closeness coefficient** = distance_to_worst / (distance_to_best + distance_to_worst)
6. **Rank** alternatives by descending score (1 = best)

## Error Handling

The program provides clear error messages:
```
Error: Input file not found
Error: Weights must be numeric and separated by commas
Error: Impacts must be either '+' or '-' and separated by commas
Error: Number of weights, impacts, and criteria columns must match
Error: Non-numeric value found in row X (criteria columns must be numeric)
```

## Requirements

- Python ≥ 3.7
- numpy
- pandas
- openpyxl (for XLSX support)

## License

MIT License
