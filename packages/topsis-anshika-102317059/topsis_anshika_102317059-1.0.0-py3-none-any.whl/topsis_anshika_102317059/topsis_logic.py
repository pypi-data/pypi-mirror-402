import os
import pandas as pd
import numpy as np

class TopsisError(Exception):
    pass

def parse_weights_impacts(weights_str, impacts_str):
    if "," not in weights_str or "," not in impacts_str:
        raise TopsisError("Impacts and weights must be separated by ',' (comma).")

    weights = [w.strip() for w in weights_str.split(",")]
    impacts = [i.strip() for i in impacts_str.split(",")]

    try:
        weights = [float(w) for w in weights]
    except:
        raise TopsisError("Weights must be numeric values separated by commas.")

    for imp in impacts:
        if imp not in ["+", "-"]:
            raise TopsisError("Impacts must be either '+' or '-' only.")

    return weights, impacts

def run_topsis(input_file, weights_str, impacts_str, output_file):
    # File not found
    if not os.path.exists(input_file):
        raise TopsisError(f"File not found: {input_file}")

    # Read
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        raise TopsisError(f"Unable to read input file: {str(e)}")

    # At least 3 columns
    if df.shape[1] < 3:
        raise TopsisError("Input file must contain three or more columns.")

    data = df.iloc[:, 1:].copy()
    n_cols = data.shape[1]

    weights, impacts = parse_weights_impacts(weights_str, impacts_str)

    if len(weights) != n_cols or len(impacts) != n_cols:
        raise TopsisError("Number of weights, impacts and columns (from 2nd to last) must be the same.")

    for col in data.columns:
        try:
            data[col] = pd.to_numeric(data[col])
        except:
            raise TopsisError(f"Non-numeric value found in column '{col}'.")

    matrix = data.to_numpy(dtype=float)

    # Normalize
    norm = np.sqrt((matrix ** 2).sum(axis=0))
    if np.any(norm == 0):
        raise TopsisError("Normalization failed because a column has all zeros.")
    normalized = matrix / norm

    # Weighted
    weights_arr = np.array(weights, dtype=float)
    weighted = normalized * weights_arr

    # Ideal best/worst
    ideal_best = np.zeros(n_cols)
    ideal_worst = np.zeros(n_cols)

    for j in range(n_cols):
        if impacts[j] == "+":
            ideal_best[j] = np.max(weighted[:, j])
            ideal_worst[j] = np.min(weighted[:, j])
        else:
            ideal_best[j] = np.min(weighted[:, j])
            ideal_worst[j] = np.max(weighted[:, j])

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)
    rank = score.argsort()[::-1] + 1

    df["Topsis Score"] = score.round(4)
    df["Rank"] = rank

    df.to_csv(output_file, index=False)
    return output_file
