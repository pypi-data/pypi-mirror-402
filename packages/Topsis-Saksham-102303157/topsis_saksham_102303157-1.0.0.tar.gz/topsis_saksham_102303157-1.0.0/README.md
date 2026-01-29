# Topsis-Saksham-102303157

A Python package implementing TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution), a multi-criteria decision analysis method.

## Description

TOPSIS is a method of compensatory aggregation that compares a set of alternatives by identifying weights for each criterion, normalizing scores for each criterion, and calculating the geometric distance between each alternative and the ideal alternative.

## Installation

```bash
pip install Topsis-Saksham-102303157
```

## Usage

### Command Line

After installation, you can use the `topsis` command directly from the terminal:

```bash
topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
```

### Example

```bash
topsis data.csv "1,1,1,2" "+,+,-,+" output.csv
```

### Parameters

- **InputDataFile**: Path to the input CSV file
- **Weights**: Comma-separated weights for each criterion (e.g., "1,1,1,2")
- **Impacts**: Comma-separated impacts (+ or -) for each criterion (e.g., "+,+,-,+")
- **OutputResultFileName**: Path for the output CSV file

### Input File Format

The input CSV file should have:
- First column: Names/identifiers of alternatives
- Remaining columns: Numeric values for each criterion

Example (data.csv):
```csv
Fund Name,P1,P2,P3,P4,P5
M1,0.67,0.45,6.5,42.6,12.56
M2,0.6,0.36,3.6,53.3,14.47
M3,0.82,0.67,3.8,63.1,17.1
```

### Output

The program generates a CSV file with two additional columns:
- **Topsis Score**: The calculated TOPSIS score for each alternative
- **Rank**: Ranking based on TOPSIS score (1 = best)

## Features

- Input validation (file existence, column count, numeric values)
- Proper error handling with descriptive messages
- Vector normalization method
- Weighted normalized decision matrix
- Euclidean distance calculation
- TOPSIS score and ranking

## Requirements

- Python 3.6+
- pandas >= 1.0.0
- numpy >= 1.18.0

## License

MIT License

## Author

Saksham (Roll Number: 102303157)

## Contributing

Contributions, issues, and feature requests are welcome!

## Support

For support, email your.email@example.com