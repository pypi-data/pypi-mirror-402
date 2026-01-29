# ============================================
# STEP 0 — Import Required Libraries
# ============================================

import sys
import pandas as pd
import numpy as np


def main():
    # ============================================
    # STEP 1 — Validate Number of Command-Line Arguments
    # ============================================

    if len(sys.argv) != 5:
        print("Usage: python topsis.py <inputFileName> <Weights> <Impacts> <resultFileName>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights_input = sys.argv[2]
    impacts_input = sys.argv[3]
    output_file = sys.argv[4]

    # ============================================
    # STEP 2 — Parse Weights and Impacts
    # ============================================

    try:
        weights = np.array([float(w) for w in weights_input.split(",")])
    except ValueError:
        print("Error: Weights must be numeric and comma-separated.")
        sys.exit(1)

    impacts = impacts_input.split(",")

    for impact in impacts:
        if impact not in ['+', '-']:
            print("Error: Impacts must be either '+' or '-'.")
            sys.exit(1)

    # ============================================
    # STEP 3 — Load Input File (File Not Found Handling)
    # ============================================

    try:
        df = pd.read_excel(input_file)
    except FileNotFoundError:
        print("Error: Input file not found.")
        sys.exit(1)
    except Exception as e:
        print("Error while reading input file:", e)
        sys.exit(1)

    # ============================================
    # STEP 4 — Validate Minimum Column Requirement
    # ============================================

    if df.shape[1] < 3:
        print("Error: Input file must contain at least three columns.")
        sys.exit(1)

    # ============================================
    # STEP 5 — Separate Identifier and Criteria Columns
    # ============================================

    data = df.iloc[:, 1:]

    # ============================================
    # STEP 6 — Validate Numeric Criteria Columns
    # ============================================

    try:
        data = data.astype(float)
    except ValueError:
        print("Error: From 2nd to last columns must contain numeric values only.")
        sys.exit(1)

    # ============================================
    # STEP 7 — Validate Weights & Impacts Length
    # ============================================

    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        print("Error: Number of weights and impacts must match number of criteria columns.")
        sys.exit(1)

    # ============================================
    # STEP 8 — Normalize the Decision Matrix
    # ============================================

    norm_data = data / np.sqrt((data ** 2).sum())

    # ============================================
    # STEP 9 — Apply Weights
    # ============================================

    weighted_data = norm_data * weights

    # ============================================
    # STEP 10 — Determine Ideal Best & Ideal Worst
    # ============================================

    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted_data.iloc[:, i].max())
            ideal_worst.append(weighted_data.iloc[:, i].min())
        else:
            ideal_best.append(weighted_data.iloc[:, i].min())
            ideal_worst.append(weighted_data.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # ============================================
    # STEP 11 — Calculate Distance from Ideal Solutions
    # ============================================

    dist_best = np.sqrt(((weighted_data - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_data - ideal_worst) ** 2).sum(axis=1))

    # ============================================
    # STEP 12 — Calculate TOPSIS Score
    # ============================================

    topsis_score = dist_worst / (dist_best + dist_worst)

    # ============================================
    # STEP 13 — Rank the Alternatives
    # ============================================

    df['Topsis Score'] = topsis_score
    df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)

    # ============================================
    # STEP 14 — Write Output File
    # ============================================

    try:
        df.to_csv(output_file, index=False)
        print("TOPSIS analysis completed successfully.")
    except Exception as e:
        print("Error while writing output file:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
