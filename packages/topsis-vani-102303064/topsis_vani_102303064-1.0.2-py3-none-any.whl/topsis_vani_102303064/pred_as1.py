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
            "Usage: topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>"
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
    # 3. Read input file (CSV or XLSX)
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
    # 4. Minimum column check (>= 3 columns)
    # --------------------------------------------------
    if data.shape[1] < 3:
        error_exit("Input file must contain at least three columns.")

    # --------------------------------------------------
    # 5. Extract criteria columns (2nd to last)
    # --------------------------------------------------
    criteria = data.iloc[:, 1:]

    # --------------------------------------------------
    # 6. Check numeric values in criteria columns
    # --------------------------------------------------
    if not np.all(criteria.applymap(np.isreal)):
        error_exit("From 2nd to last columns must contain numeric values only.")

    # --------------------------------------------------
    # 7. Validate comma-separated weights & impacts
    # --------------------------------------------------
    if "," not in weights_str:
        error_exit("Weights must be separated by commas.")

    if "," not in impacts_str:
        error_exit("Impacts must be separated by commas.")

    try:
        weights = [float(w.strip()) for w in weights_str.split(",")]
        impacts = [i.strip() for i in impacts_str.split(",")]
    except:
        error_exit("Invalid weights or impacts format.")

    # --------------------------------------------------
    # 8. Check counts match
    # --------------------------------------------------
    if len(weights) != criteria.shape[1] or len(impacts) != criteria.shape[1]:
        error_exit(
            "Number of weights, impacts, and criteria columns must be the same."
        )

    # --------------------------------------------------
    # 9. Validate impacts (+ or - only)
    # --------------------------------------------------
    for imp in impacts:
        if imp not in ['+', '-']:
            error_exit("Impacts must be either '+' or '-'.")

    # --------------------------------------------------
    # ---------------- TOPSIS STEPS --------------------
    # --------------------------------------------------

    # Step 1: Normalize decision matrix
    norm = np.sqrt((criteria ** 2).sum())
    normalized = criteria / norm

    # Step 2: Apply weights
    weighted = normalized * weights

    # Step 3: Ideal best and worst
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

    # Step 4: Distance from ideal best and worst
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Step 5: TOPSIS score
    topsis_score = dist_worst / (dist_best + dist_worst)

    # Step 6: Rank (higher score = better)
    rank = topsis_score.rank(ascending=False, method='dense').astype(int)

    # --------------------------------------------------
    # 10. Prepare output
    # --------------------------------------------------
    result = data.copy()
    result["Topsis Score"] = topsis_score.round(4)
    result["Rank"] = rank

    # --------------------------------------------------
    # 11. Save output file
    # --------------------------------------------------
    try:
        result.to_csv(output_file, index=False)
        print("TOPSIS analysis completed successfully.")
        print(f"Output saved to: {output_file}")
    except Exception as e:
        error_exit(f"Unable to write output file: {e}")


if __name__ == "__main__":
    main()
