import os
import numpy as np
import pandas as pd


class TopsisError(Exception):
    """Raised when TOPSIS input or processing fails."""
    pass


def _parse_vector(vec: str, kind: str):
    """Parse comma separated string values with trimming."""
    parts = [x.strip() for x in vec.split(",") if x.strip() != ""]
    if not parts:
        raise TopsisError(f"{kind} cannot be empty.")
    return parts


def run_topsis(input_csv: str, weights: str, impacts: str, output_csv: str) -> None:
    # ---- Input file check ----
    if not os.path.isfile(input_csv):
        raise TopsisError(f"Input file not found: {input_csv}")

    # ---- Read CSV ----
    try:
        df = pd.read_csv(input_csv)
    except Exception as e:
        raise TopsisError(f"Could not read CSV: {e}")

    if df.shape[1] < 3:
        raise TopsisError("CSV must contain at least 3 columns (ID + 2 criteria columns).")

    # ---- Extract numeric criteria matrix ----
    try:
        X = df.iloc[:, 1:].astype(float).to_numpy()
    except Exception:
        raise TopsisError("Columns from 2nd onward must contain numeric values only.")

    # ---- Parse weights & impacts ----
    w_list = _parse_vector(weights, "Weights")
    i_list = _parse_vector(impacts, "Impacts")

    m, n = X.shape

    if len(w_list) != n:
        raise TopsisError(f"Expected {n} weights, got {len(w_list)}.")

    if len(i_list) != n:
        raise TopsisError(f"Expected {n} impacts, got {len(i_list)}.")

    try:
        w = np.array([float(x) for x in w_list], dtype=float)
    except ValueError:
        raise TopsisError("Weights must be numeric values.")

    if np.any(w <= 0):
        raise TopsisError("Weights must be greater than 0.")

    impacts_clean = []
    for x in i_list:
        if x not in ("+", "-"):
            raise TopsisError("Impacts must be only '+' or '-'.")
        impacts_clean.append(x)

    # ---- Step 1: Normalize ----
    denom = np.sqrt((X ** 2).sum(axis=0))
    if np.any(denom == 0):
        raise TopsisError("Normalization failed: one or more criteria columns are all zeros.")

    norm = X / denom

    # ---- Step 2: Apply weights ----
    V = norm * w

    # ---- Step 3: Ideal best / worst ----
    ideal_best = np.zeros(n)
    ideal_worst = np.zeros(n)

    for j in range(n):
        if impacts_clean[j] == "+":
            ideal_best[j] = V[:, j].max()
            ideal_worst[j] = V[:, j].min()
        else:
            ideal_best[j] = V[:, j].min()
            ideal_worst[j] = V[:, j].max()

    # ---- Step 4: Euclidean distances ----
    d_plus = np.sqrt(((V - ideal_best) ** 2).sum(axis=1))
    d_minus = np.sqrt(((V - ideal_worst) ** 2).sum(axis=1))

    # ---- Step 5: Performance score ----
    score = d_minus / (d_plus + d_minus)

    # ---- Rank (1 = best) ----
    rank = score.argsort()[::-1].argsort() + 1

    # ---- Output ----
    df["Topsis Score (102303554)"] = score
    df["Rank (Harshit)"] = rank
    df.to_csv(output_csv, index=False)
