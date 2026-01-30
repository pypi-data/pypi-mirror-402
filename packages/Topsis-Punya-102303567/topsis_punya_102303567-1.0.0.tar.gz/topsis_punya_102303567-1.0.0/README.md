# Topsis-Punya-102303567

This is a Python package to implement the Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS).

## Installation

```bash
pip install Topsis-Punya-102303567
```

## Usage

You can use this package via the command line:

```bash
topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
```

### Example

```bash
topsis data.csv "1,1,1,2" "+,+,+,-" result.csv
```

## Parameters

1.  **InputDataFile**: Path to the CSV file containing the data. The file should have a header row and the first column should be the object/alternative names (which will not be used in calculation). The rest of the columns must be numeric.
2.  **Weights**: Comma-separated weights for each criterion (e.g., "1,1,1,2").
3.  **Impacts**: Comma-separated impacts for each criterion ('+' for beneficial, '-' for non-beneficial) (e.g., "+,+,+,-").
4.  **OutputResultFileName**: Path for the output CSV file which will contain the original data along with the Topsis Score and Rank.

## License

MIT
