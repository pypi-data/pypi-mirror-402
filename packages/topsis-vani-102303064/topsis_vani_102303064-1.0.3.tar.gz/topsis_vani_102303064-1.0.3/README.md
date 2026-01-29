
# Topsis-Vani-102303064

This package implements the **TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)** method.
It is used to rank alternatives based on multiple criteria.

---

## Installation

```bash

pip install topsis-vani-102303064

```

Usage (Command Line)

```bash
topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
```

Example
```bash
topsis data.csv "1,1,1,2" "+,+,-,+" output.csv
```

Input File Format
-CSV file
-Minimum 3 columns
-First column: alternative names (non-numeric)
-Remaining columns: numeric criteria values

Example Input
```bash
Fund Name,P1,P2,P3,P4
M1,0.67,0.45,6.5,42.6
M2,0.60,0.36,3.6,53.3
M3,0.82,0.67,3.8,63.1
```

Weights and Impacts
Weights (comma separated):
-1,1,1,2
Impacts (+ for benefit, - for cost):
-+,+,-,+

Output
-Output file is generated in CSV format
-Two new columns are added:
-Topsis Score
-Rank (Rank 1 = Best alternative)

License
-MIT License

Author
-Vani
-Roll Number: 102303064