# Topsis-Keshav-102303502

This is a Python package to implement the TOPSIS technique for Multi-Criteria Decision Making.

## Installation

```bash
pip install Topsis-Keshav-102303502
```

## Usage

Command Line:
```bash
topsis <InputDataFile> <Weights> <Impacts> <ResultFileName>
```

Example:
```bash
topsis data.csv "1,1,1,1" "+,-,+,+" result.csv
```

## Input File Format
CSV file with 3 or more columns.
First column is the object/fund name.
Rest columns are numeric parameters.
