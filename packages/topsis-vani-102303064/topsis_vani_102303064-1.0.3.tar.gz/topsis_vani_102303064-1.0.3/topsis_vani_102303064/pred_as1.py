import sys
import os
import pandas as pd
import numpy as np


def error_exit(msg):
    print("Error:", msg)
    sys.exit(1)


def main():
    # --------------------------------------------------
    # 1. Check number of command-line arguments
    # --------------------------------------------------
    if len(sys.argv) != 5:
        error_exit(
            "Incorrect number of parameters.\n"
            "Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>"
        )

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    # --------------------------------------------------
    # 2. Check if input file exists
    # --------------------------------------------------
    if not os.path.isfile(input_file):
        error_exit("Input file not found.")

    # --------------------------------------------------
    # 3. Read input file
    # --------------------------------------------------
    try:
        if input_file.endswith(".csv"):
            data = pd.read_csv(input_file)
        elif input_file.endswith(".xlsx"):
            data = pd.read_excel(input_file)
        else:
            error_exit("Input file must be a .csv or .xlsx file.")
    except Exception as e:
        error_exit(f"Unable to read input file: {e}")

    # --------------------------------------------------
    # 4. Minimum column check
    # --------------------------------------------------
    if data.shape[1] < 3:
        error_exit("Input file must contain at least three columns.")

    # --------------------------------------------------
    # 5. Extract criteria columns
    # --------------------------------------------------
    criteria = data.iloc[:, 1:]

    # --------------------------------------------------
    # 6. Numeric validation
    # --------------------------------------------------
    try:
        criteria = criteria.apply(pd.to_numeric)
    except ValueError:
        error_exit("From 2nd to last columns must contain numeric values only.")

    # --------------------------------------------------
    # 7. Validate weights (comma-separated & numeric)
    # --------------------------------------------------
    try:
        weights = [float(w.strip()) for w in weights_str.split(",")]
        if len(weights) < 2:
            raise ValueError
    except:
        error_exit("Weights must be numeric and separated by commas.")

    # --------------------------------------------------
    # 8. Validate impacts (comma-separated & + / -)
    # --------------------------------------------------
    impacts = [i.strip() for i in impacts_str.split(",")]

    if len(impacts) < 2 or any(i not in ['+', '-'] for i in impacts):
        error_exit("Impacts must be either '+' or '-' and separated by commas.")

    # --------------------------------------------------
    # 9. Check counts match
    # --------------------------------------------------
    if len(weights) != criteria.shape[1] or len(impacts) != criteria.shape[1]:
        error_exit(
            "Number of weights, impacts, and criteria columns must be the same."
        )

    # --------------------------------------------------
    # ---------------- TOPSIS STEPS --------------------
    # --------------------------------------------------

    norm = np.sqrt((criteria ** 2).sum())
    normalized = criteria / norm

    weighted = normalized * weights

    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    topsis_score = dist_worst / (dist_best + dist_worst)
    rank = topsis_score.rank(ascending=False, method='dense').astype(int)

    # --------------------------------------------------
    # 10. Output
    # --------------------------------------------------
    result = data.copy()
    result["Topsis Score"] = topsis_score.round(4)
    result["Rank"] = rank

    # --------------------------------------------------
    # 11. Save file
    # --------------------------------------------------
    try:
        result.to_csv(output_file, index=False)
        print("TOPSIS analysis completed successfully.")
        print(f"Output saved to: {output_file}")
    except Exception as e:
        error_exit(f"Unable to write output file: {e}")


if __name__ == "__main__":
    main()
