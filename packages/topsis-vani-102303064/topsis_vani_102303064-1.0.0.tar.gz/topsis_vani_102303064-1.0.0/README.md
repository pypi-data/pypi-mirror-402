# Topsis-Vani-102303064

This package implements the **TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)** method.
TOPSIS is a multi-criteria decision-making technique used to rank alternatives based on their distance from an ideal best and ideal worst solution.

---

## Installation

Install the package from PyPI using pip:

```bash
pip install topsis-vani-102303064
Usage (Command Line)
After installation, the package can be used directly from the command line.

Syntax
bash
Copy code
topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
Example
bash
Copy code
topsis data.csv "1,1,1,2" "+,+,-,+" output.csv
Input File Format
The input file must be a CSV or XLSX file.

The file must contain at least three columns.

First column: Alternative names (non-numeric).

From second column onwards: Numeric criteria values only.

Example Input (data.csv)
csv
Copy code
Fund Name,P1,P2,P3,P4
M1,0.67,0.45,6.5,42.6
M2,0.60,0.36,3.6,53.3
M3,0.82,0.67,3.8,63.1
Weights and Impacts
Weights must be numeric values separated by commas.
Example:

text
Copy code
1,1,1,2
Impacts must be either + or -, separated by commas.
Example:

text
Copy code
+,+,-,+
The number of weights and impacts must match the number of criteria columns.

Output File
The output file is generated in CSV format.

Two additional columns are added:

Topsis Score

Rank (Rank 1 indicates the best alternative)

Example Output Columns
text
Copy code
Fund Name,P1,P2,P3,P4,Topsis Score,Rank
Error Handling
The program performs validation checks for:

Correct number of command-line arguments

Input file existence

Minimum number of columns

Numeric values in criteria columns

Correct number of weights and impacts

Valid impact symbols (+ or -)

Appropriate error messages are displayed for invalid inputs.

License
This project is licensed under the MIT License.

Author
Vani
Roll Number: 102303064