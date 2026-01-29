# TOPSIS Command Line Program
# Usage:
# python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
# Example:
# python topsis.py data.csv "1,1,1,2" "+,+,-,+" output-result.csv

import sys
import pandas as pd
import numpy as np
import os

def error_exit(msg):
    print(f"Error: {msg}")
    sys.exit(1)

def main():
    # =========================
    # 1. Check parameters
    # =========================
    if len(sys.argv) != 5:
        error_exit("Usage: python <program.py> <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    # =========================
    # 2. File existence check
    # =========================
    if not os.path.exists(input_file):
        error_exit("Input file not found")

    # =========================
    # 3. Read CSV file
    # =========================
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        error_exit(f"Unable to read file: {e}")

    if df.shape[1] < 3:
        error_exit("Input file must contain three or more columns")

    data = df.copy()

    # =========================
    # 4. Validate numeric columns (2nd to last)
    # =========================
    try:
        numeric_data = data.iloc[:, 1:].apply(pd.to_numeric)
    except:
        error_exit("From 2nd to last columns must contain numeric values only")

    # =========================
    # 5. Parse weights & impacts
    # =========================
    try:
        weights = list(map(float, weights_str.split(",")))
        impacts = impacts_str.split(",")
    except:
        error_exit("Weights and impacts must be comma separated")

    n_cols = numeric_data.shape[1]

    if len(weights) != n_cols or len(impacts) != n_cols:
        error_exit("Number of weights, impacts, and numeric columns must be the same")

    for imp in impacts:
        if imp not in ["+", "-"]:
            error_exit("Impacts must be either + or -")

    weights = np.array(weights, dtype=float)

    # =========================
    # STEP 2: Vector Normalization
    # =========================
    norm = np.sqrt((numeric_data ** 2).sum())
    normalized = numeric_data / norm

    # =========================
    # STEP 3: Weight Assignment
    # =========================
    weighted = normalized * weights

    # =========================
    # STEP 4: Ideal Best & Worst
    # =========================
    ideal_best = []
    ideal_worst = []

    for i in range(n_cols):
        if impacts[i] == "+":
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # =========================
    # STEP 5: Euclidean Distance
    # =========================
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # =========================
    # STEP 6 & 7: TOPSIS Score & Rank
    # =========================
    topsis_score = dist_worst / (dist_best + dist_worst)

    data["Topsis Score"] = topsis_score
    data["Rank"] = data["Topsis Score"].rank(ascending=False, method="dense").astype(int)

    # =========================
    # Save Output
    # =========================
    try:
        data.to_csv(output_file, index=False)
        print(f"TOPSIS result saved to {output_file}")
    except Exception as e:
        error_exit(f"Unable to write output file: {e}")

if __name__ == "__main__":
    main()
