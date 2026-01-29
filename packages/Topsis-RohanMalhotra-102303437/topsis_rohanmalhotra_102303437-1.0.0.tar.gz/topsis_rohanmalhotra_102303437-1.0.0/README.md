# TOPSIS Python Package (Assignment)

**Package name on PyPI:** `Topsis-RohanMalhotra-102303437`

## What this package does
This package implements **TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)** and provides a **command-line interface**.

## Input format
Input must be a CSV with:
- **1st column**: Alternative name/ID (string)
- **2nd to last columns**: numeric criteria columns

Example:
```csv
Fund Name,P1,P2,P3,P4,P5
M1,0.67,0.45,6.5,4.2,16.58
M2,0.60,0.36,6.3,5.3,14.47
```

## Install (after you upload to PyPI)
```bash
pip install Topsis-RohanMalhotra-102303437
```

## Run from command line
```bash
topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
```

Example:
```bash
topsis data.csv "1,1,1,1,1" "+,+,-,+,+" output.csv
```

## Output
The output CSV will contain all input columns plus:
- `Topsis Score`
- `Rank` (1 = best)

## Common errors (as required)
- Wrong number of parameters
- Input file not found
- Less than 3 columns
- Non-numeric values in criteria columns
- Number of weights/impacts not equal to number of criteria
- Impacts not in `+` or `-`
- Weights/impacts not comma separated
