# Topsis-Khushveer-102303327

This package provides a command-line implementation of the **Technique for Order Preference by Similarity to Ideal Solution (TOPSIS)**, a popular multi-criteria decision-making (MCDM) method.

The package allows users to rank multiple alternatives based on multiple criteria, user-defined weights, and impacts (benefit or cost).

---

## Features
- Command-line based TOPSIS implementation
- Supports any number of alternatives and criteria
- User-defined weights and impacts
- Automatic calculation of TOPSIS score and rank
- Output generated in CSV format

---

## Installation

Install the package using pip:

```
pip install Topsis-Khushveer-102303327
```
## Usage

Run the TOPSIS program from the command line:
topsis <input_file.csv> "<weights>" "<impacts>" <output_file.csv>
#### Example
```
topsis data.csv "1,1,1,1,1" "+,+,-,+,+" result.csv
```
## Input Format

### Input CSV File
- The first column should contain the names of alternatives.
- The remaining columns should contain numeric values only.
- The file must contain at least three columns.

### Weights

- Provided as a comma-separated list.
- Number of weights must be equal to the number of criteria.
#### Example:
```
"1,1,1,1,1"
```

### Impacts

Provided as a comma-separated list.
Each impact must be either:

- "+" for benefit criteria
- "-" for cost criteria
#### Example:
``` 
"+,+,-,+,+"
```
## Output Format

The output CSV file contains:

- All original input columns
- Topsis Score for each alternative
- Rank (Rank 1 indicates the best alternative)

## Error Handling

The program performs validation for:

- Incorrect number of command-line arguments
- File not found errors
- Non-numeric values in criteria columns
- Mismatch between number of weights, impacts, and criteria
- Invalid impact symbols

## Author

Khushveer Kaur (102303327)
Computer Engineering, TIET
```

