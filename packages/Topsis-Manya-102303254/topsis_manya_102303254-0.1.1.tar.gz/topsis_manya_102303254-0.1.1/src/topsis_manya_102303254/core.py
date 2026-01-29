import numpy as np
import pandas as pd

class TopsisError(Exception):
    pass


def _parse_vector(vec: str, n: int, kind: str):
    if "," not in vec:
        raise TopsisError(f"{kind} must be comma-separated.")
    parts = [x.strip() for x in vec.split(",")]
    if len(parts) != n:
        raise TopsisError(f"Number of {kind} ({len(parts)}) must match number of criteria ({n}).")
    return parts


def _parse_weights(weights: str, n: int) -> np.ndarray:
    parts = _parse_vector(weights, n, "weights")
    try:
        w = np.array([float(x) for x in parts], dtype=float)
    except Exception:
        raise TopsisError("Weights must be numeric.")
    if np.any(w <= 0):
        raise TopsisError("Weights must be positive.")
    return w


def _parse_impacts(impacts: str, n: int) -> np.ndarray:
    parts = _parse_vector(impacts, n, "impacts")
    for x in parts:
        if x not in ["+", "-"]:
            raise TopsisError("Impacts must contain only '+' or '-'.")
    return np.array(parts, dtype=str)


def topsis_from_csv(path: str, weights: str, impacts: str) -> pd.DataFrame:
    # Read CSV
    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise TopsisError(f"Unable to read CSV: {e}")

    # Must have at least 3 columns (ID + 2 criteria minimum)
    if df.shape[1] < 3:
        raise TopsisError("Input file must contain three or more columns.")

    # "Other notes": remove first column (ID/Model) for processing
    criteria_df = df.iloc[:, 1:].copy()

    # Ensure numeric
    for col in criteria_df.columns:
        criteria_df[col] = pd.to_numeric(criteria_df[col], errors="coerce")

    if criteria_df.isna().any().any():
        bad_cols = criteria_df.columns[criteria_df.isna().any()].tolist()
        raise TopsisError(f"CSV contains non-numeric values in criteria columns: {bad_cols}")

    n = criteria_df.shape[1]
    w = _parse_weights(weights, n)
    imp = _parse_impacts(impacts, n)

    X = criteria_df.to_numpy(dtype=float)

    # Normalize
    denom = np.sqrt((X ** 2).sum(axis=0))
    if np.any(denom == 0):
        raise TopsisError("One or more criteria columns have all zeros, cannot normalize.")
    norm = X / denom

    # Weighted normalized
    wnorm = norm * w

    # Ideal best/worst
    ideal_best = np.zeros(n, dtype=float)
    ideal_worst = np.zeros(n, dtype=float)
    for j in range(n):
        col = wnorm[:, j]
        if imp[j] == "+":
            ideal_best[j] = col.max()
            ideal_worst[j] = col.min()
        else:
            ideal_best[j] = col.min()
            ideal_worst[j] = col.max()

    # Distances
    d_pos = np.sqrt(((wnorm - ideal_best) ** 2).sum(axis=1))
    d_neg = np.sqrt(((wnorm - ideal_worst) ** 2).sum(axis=1))

    # Performance score
    p_score = d_neg / (d_pos + d_neg)

    # Rank (1 = best)
    rank = (-p_score).argsort().argsort() + 1

    # Return result only like sample output (P-Score, Rank)
    out = pd.DataFrame({
        "P-Score": np.round(p_score, 6),
        "Rank": rank.astype(int)
    })
    return out
