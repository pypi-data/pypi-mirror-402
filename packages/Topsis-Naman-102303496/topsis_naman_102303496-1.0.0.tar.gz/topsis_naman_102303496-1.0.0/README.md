# Topsis-Naman-102303496

A Python package implementing TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) for multi-criteria decision making.

## Installation

```bash
pip install Topsis-Naman-102303496
```

## Usage

### Command Line

```bash
topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
```

### Example

```bash
topsis data.csv "1,1,1,2" "+,+,-,+" output.csv
```

### As a Module

```python
from topsis_naman_102303496 import topsis

topsis("data.csv", "1,1,1,2", "+,+,-,+", "output.csv")
```

## Input File Format

The input CSV file should have the following format:
- First column: Object/Alternative names
- Remaining columns: Numeric values for each criterion

| Fund Name | P1   | P2   | P3   | P4    | P5    |
|-----------|------|------|------|-------|-------|
| M1        | 0.67 | 0.45 | 6.5  | 42.6  | 12.56 |
| M2        | 0.6  | 0.36 | 3.6  | 53.3  | 14.47 |

## Output File Format

The output file includes all original columns plus:
- **Topsis Score**: The calculated TOPSIS score
- **Rank**: Ranking based on the score (1 = best)

## Parameters

- **InputDataFile**: Path to the input CSV file
- **Weights**: Comma-separated weights for each criterion (e.g., "1,1,1,2")
- **Impacts**: Comma-separated impacts, + for benefit, - for cost (e.g., "+,+,-,+")
- **OutputResultFileName**: Path for the output CSV file

## License

MIT
