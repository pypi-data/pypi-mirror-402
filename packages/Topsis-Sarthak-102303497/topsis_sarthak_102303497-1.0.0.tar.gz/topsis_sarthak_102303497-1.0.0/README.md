# Topsis-Sarthak-102303497

A Python package for TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) multi-criteria decision analysis.

## Installation

```bash
pip install Topsis-Sarthak-102303497
```

## Usage

### Command Line

```bash
topsis <InputDataFile> <Weights> <Impacts> <ResultFileName>
```

### Example

```bash
topsis data.csv "1,1,1,2" "+,+,-,+" result.csv
```

### Parameters

- **InputDataFile**: Path to CSV file containing the data
- **Weights**: Comma-separated weights for each criterion (e.g., "1,1,1,2")
- **Impacts**: Comma-separated impacts for each criterion (+ for benefit, - for cost)
- **ResultFileName**: Path for the output CSV file

### Input File Format

The input CSV must have:
- First column: Object/Alternative names
- Remaining columns: Numeric criteria values

Example:
```
Fund Name,P1,P2,P3,P4,P5
M1,0.67,0.45,6.5,42.6,12.56
M2,0.6,0.36,3.6,53.3,14.47
```

### Output File Format

The output CSV will contain all input columns plus:
- **Topsis Score**: The calculated TOPSIS score
- **Rank**: Rank based on the TOPSIS score (1 = best)

## License

MIT License
