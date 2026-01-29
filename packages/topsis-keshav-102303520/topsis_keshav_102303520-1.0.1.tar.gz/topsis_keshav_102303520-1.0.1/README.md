# TOPSIS-Keshav-102303520

A Python library for solving Multiple Criteria Decision Making (MCDM) problems using the Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS).

## Project Description

This package implements TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution), a multi-criteria decision analysis method. TOPSIS is based on the concept that the chosen alternative should have the shortest geometric distance from the positive ideal solution and the longest geometric distance from the negative ideal solution.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the package:

```bash
pip install topsis-keshav-102303520
```

## Usage

Enter CSV filename followed by `.csv` extension, then enter the weights vector with vector values separated by commas, followed by the impacts vector with comma separated signs (+,-).

### Method 1: With quotes

```bash
topsis sample.csv "1,1,1,1" "+,-,+,+" output.csv
```

### Method 2: Without quotes

```bash
topsis sample.csv 1,1,1,1 +,-,+,+ output.csv
```

**Note:** The second representation does not provide for inadvertent spaces between vector values. So, if the input string contains spaces, make sure to enclose it between double quotes ("").

To view usage help, use:

```bash
topsis -h
```

## Example

### sample.csv

A CSV file showing data for different mobile handsets having varying features:

| Model | Storage space(in gb) | Camera(in MP) | Price(in $) | Looks(out of 5) |
| ----- | -------------------- | ------------- | ----------- | --------------- |
| M1    | 16                   | 12            | 250         | 5               |
| M2    | 16                   | 8             | 200         | 3               |
| M3    | 32                   | 16            | 300         | 4               |
| M4    | 32                   | 8             | 275         | 4               |
| M5    | 16                   | 16            | 225         | 2               |

### Input

```bash
topsis sample.csv "0.25,0.25,0.25,0.25" "+,+,-,+" output.csv
```

Where:
- **weights vector** = [0.25, 0.25, 0.25, 0.25]
- **impacts vector** = [+, +, -, +]

### Output

```
TOPSIS RESULTS
------------------------------
Model  P-Score  Rank
   M3  0.691632    1
   M4  0.534737    2
   M1  0.534277    3
   M5  0.401046    4
   M2  0.308368    5
```

The results show the TOPSIS score (P-Score) and rank for each alternative, where rank 1 indicates the best option.

## Other Notes

- The first column and first row are removed by the library before processing, in attempt to remove indices and headers. So make sure the CSV follows the format as shown in sample.csv
- Make sure the CSV does not contain categorical values
- Ensure the number of weights and impacts matches the number of criteria (columns)
- Impacts must be either '+' (beneficial) or '-' (non-beneficial)

## Input File Format Requirements

1. The input file must be a CSV with the first column as object/alternative names
2. From the 2nd column onwards, there must be numeric values only
3. The number of weights, impacts, and columns (from 2nd column) must be the same
4. Impacts must be either +ve ('+') or -ve ('-')
5. Weights must be numeric and greater than 0

## Algorithm

TOPSIS follows these steps:

1. **Normalize** the decision matrix
2. **Calculate weighted normalized** decision matrix
3. **Determine ideal best and ideal worst** solutions
4. **Calculate Euclidean distances** from ideal best and ideal worst
5. **Calculate performance score** and rank alternatives

## Features

- ✅ Easy to use command-line interface
- ✅ Handles multiple criteria decision making
- ✅ Automatic validation of inputs
- ✅ Generates ranked results with TOPSIS scores
- ✅ Exports results to CSV format
- ✅ Comprehensive error handling

## Requirements

- Python >=3.6
- pandas >=1.0.0
- numpy >=1.18.0

## Author

**Keshav Sharma**  
Roll No: 102303520
Email: ksharma5_be23@thapar.edu


## Contributing

Pull requests are welcome. For major changes, pleases open an issue first to discuss what you would like to change.

## Keywords

- TOPSIS
- MCDM
- Multi-Criteria Decision Making
- Decision Analysis
- Optimization
- Python
- Data Science

## Version History

- **1.0.0** (Initial Release)
  - Basic TOPSIS implementation
  - Command-line interface
  - CSV input/output support
  - Input validation
  - Error handling
  