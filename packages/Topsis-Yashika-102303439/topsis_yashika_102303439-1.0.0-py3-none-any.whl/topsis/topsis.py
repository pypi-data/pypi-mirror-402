# -------------------------------------------------
# TOPSIS Command Line Program
# Usage:
# python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
# Example:
# python topsis.py data.csv "1,1,1,1,1" "+,+,-,+,+" output-result.csv
# -------------------------------------------------

import sys
import os
import pandas as pd
import numpy as np


def topsis(input_file, weights, impacts, output_file):

    # ---------- Read input file ----------
    if not os.path.isfile(input_file):
        print("Error: Input file not found")
        sys.exit(1)

    df = pd.read_csv(input_file)

    # ---------- Validate columns ----------
    if df.shape[1] < 3:
        print("Error: Input file must contain three or more columns")
        sys.exit(1)

    # ---------- Validate numeric values ----------
    try:
        data = df.iloc[:, 1:].astype(float)
    except ValueError:
        print("Error: From 2nd column onward values must be numeric")
        sys.exit(1)

    n_criteria = data.shape[1]

    # ---------- Validate weights & impacts ----------
    if len(weights) != n_criteria:
        print("Error: Number of weights must match number of criteria")
        sys.exit(1)

    if len(impacts) != n_criteria:
        print("Error: Number of impacts must match number of criteria")
        sys.exit(1)

    for i in impacts:
        if i not in ['+', '-']:
            print("Error: Impacts must be + or -")
            sys.exit(1)

    # ---------- Normalize decision matrix ----------
    normalized = data / np.sqrt((data ** 2).sum())

    # ---------- Apply weights ----------
    weights = np.array(weights)
    weighted = normalized * weights

    # ---------- Ideal best & worst ----------
    ideal_best = []
    ideal_worst = []

    for i in range(n_criteria):
        if impacts[i] == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # ---------- Distance calculation ----------
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # ---------- TOPSIS score ----------
    score = dist_worst / (dist_best + dist_worst)

    # ---------- Ranking ----------
    df["Topsis Score"] = score
    df["Rank"] = df["Topsis Score"].rank(ascending=False, method="dense").astype(int)

    # ---------- Save output ----------
    df.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully!")
    print("Output saved to:", output_file)


# ---------------- MAIN ----------------
if __name__ == "__main__":

    # Check arguments count
    if len(sys.argv) != 5:
        print("Usage:")
        print("python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights_input = sys.argv[2]
    impacts_input = sys.argv[3]
    output_file = sys.argv[4]

    # Parse weights
    try:
        weights = list(map(float, weights_input.split(',')))
    except ValueError:
        print("Error: Weights must be numeric")
        sys.exit(1)

    # Parse impacts
    impacts = impacts_input.split(',')

    topsis(input_file, weights, impacts, output_file)
