import sys
import os
import pandas as pd
import numpy as np


def error_exit(msg):
    print(f"Error: {msg}")
    sys.exit(1)


def parse_weights_impacts(weights_str, impacts_str, n_cols):
    # check comma separated
    if "," not in weights_str or "," not in impacts_str:
        error_exit("Impacts and weights must be separated by ',' (comma).")

    try:
        weights = [float(x.strip()) for x in weights_str.split(",")]
    except:
        error_exit("Weights must be numeric and comma separated.")

    impacts = [x.strip() for x in impacts_str.split(",")]

    if len(weights) != n_cols:
        error_exit("Number of weights must be equal to number of columns (from 2nd to last).")

    if len(impacts) != n_cols:
        error_exit("Number of impacts must be equal to number of columns (from 2nd to last).")

    for imp in impacts:
        if imp not in ["+", "-"]:
            error_exit("Impacts must be either '+' or '-' only.")

    if any(w <= 0 for w in weights):
        error_exit("Weights must be positive numbers.")

    return np.array(weights, dtype=float), impacts


def topsis(input_file, weights_str, impacts_str, output_file):
    # File check
    if not os.path.exists(input_file):
        error_exit("File not found.")

    # Read file
    try:
        df = pd.read_csv(input_file)
    except:
        error_exit("Unable to read input file. Ensure it is a valid CSV.")

    # Column check (>=3 columns)
    if df.shape[1] < 3:
        error_exit("Input file must contain three or more columns.")

    # criteria matrix = from 2nd column to last
    data = df.iloc[:, 1:].copy()

    # numeric check
    for col in data.columns:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    if data.isnull().any().any():
        error_exit("From 2nd to last columns must contain numeric values only.")

    n_criteria = data.shape[1]

    # validate weights & impacts
    weights, impacts = parse_weights_impacts(weights_str, impacts_str, n_criteria)

    # Step 1: Normalize
    denom = np.sqrt((data ** 2).sum(axis=0))
    if (denom == 0).any():
        error_exit("Normalization error: one or more criteria columns have all zeros.")

    norm_data = data / denom

    # Step 2: Weighted normalized matrix
    weighted = norm_data * weights

    # Step 3: Ideal best and ideal worst
    ideal_best = []
    ideal_worst = []

    for j in range(n_criteria):
        col_vals = weighted.iloc[:, j].values
        if impacts[j] == "+":
            ideal_best.append(col_vals.max())
            ideal_worst.append(col_vals.min())
        else:
            ideal_best.append(col_vals.min())
            ideal_worst.append(col_vals.max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Step 4: Distances
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Step 5: TOPSIS score
    score = dist_worst / (dist_best + dist_worst)

    # Ranking (higher score -> better rank 1)
    rank = score.rank(ascending=False, method="dense").astype(int)

    # Output
    result = df.copy()
    result["Topsis Score"] = np.round(score * 100, 2)  # like sample output
    result["Rank"] = rank

    try:
        result.to_csv(output_file, index=False)
    except:
        error_exit("Unable to write output file.")

    print(f"Success: TOPSIS result saved to '{output_file}'")


if __name__ == "__main__":
    # Argument check
    if len(sys.argv) != 5:
        error_exit("Incorrect number of parameters.\nUsage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputFileName>")

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    topsis(input_file, weights_str, impacts_str, output_file)
