# Topsis-Yajat-102303185

A Python package for TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) multi-criteria decision analysis.

## Installation

```bash
pip install Topsis-Yajat-102303185
```

## Usage

### Command Line

```bash
topsis <InputDataFile> <Weights> <Impacts> <ResultFileName>
```

### Example

```bash
topsis data.csv "1,1,1,2,1" "+,+,-,+,-" output.csv
```

### In Python

```python
from Topsis_Yajat_102303185 import topsis

topsis("data.csv", "1,1,1,2,1", "+,+,-,+,-", "output.csv")
```

## Input File Format

The input CSV file should have the following format:
- First column: Object/Alternative names
- Second column onwards: Numeric criteria values

Example (`data.csv`):
```
Fund Name,P1,P2,P3,P4,P5
M1,0.67,0.45,6.5,42.6,12.56
M2,0.6,0.36,3.6,53.3,14.47
M3,0.82,0.67,3.8,63.1,17.1
```

## Parameters

| Parameter | Description |
|-----------|-------------|
| InputDataFile | Path to input CSV file |
| Weights | Comma-separated weights (e.g., "1,1,1,2,1") |
| Impacts | Comma-separated impacts, + or - (e.g., "+,+,-,+,-") |
| ResultFileName | Output CSV file path |

## Output

The output CSV file contains the original data with two additional columns:
- **Topsis Score**: The calculated TOPSIS score (0-1)
- **Rank**: Rank based on the score (1 = best)

## License

MIT License
