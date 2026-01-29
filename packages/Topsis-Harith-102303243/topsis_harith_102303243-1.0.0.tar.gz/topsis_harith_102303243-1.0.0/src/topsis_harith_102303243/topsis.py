import numpy as np
import pandas as pd


class TopsisError(Exception):
    pass


def validate_and_load(input_file: str, weights: str, impacts: str):
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        raise TopsisError(f"File not found: {input_file}")
    except Exception as e:
        raise TopsisError(f"Could not read file. Ensure it is a CSV. Details: {e}")

    if df.shape[1] < 3:
        raise TopsisError("Input file must contain at least 3 columns.")

    criteria_cols = df.columns[1:]

    for col in criteria_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if df[criteria_cols].isna().any().any():
        bad_cols = df[criteria_cols].columns[df[criteria_cols].isna().any()].tolist()
        raise TopsisError(f"Non-numeric value(s) found in criteria columns: {bad_cols}")

    if "," not in weights:
        raise TopsisError("Weights must be comma separated. Example: 1,1,2")
    if "," not in impacts:
        raise TopsisError("Impacts must be comma separated. Example: +,+,-")

    w = [x.strip() for x in weights.split(",") if x.strip()]
    im = [x.strip() for x in impacts.split(",") if x.strip()]

    if len(w) != len(criteria_cols):
        raise TopsisError("Number of weights must match number of criteria columns.")
    if len(im) != len(criteria_cols):
        raise TopsisError("Number of impacts must match number of criteria columns.")

    try:
        w = np.array([float(x) for x in w], dtype=float)
    except:
        raise TopsisError("Weights must be numeric.")

    if np.any(w <= 0):
        raise TopsisError("Weights must be positive.")

    for x in im:
        if x not in ["+", "-"]:
            raise TopsisError("Impacts must be '+' or '-' only.")

    return df, criteria_cols, w, im


def run_topsis(df, criteria_cols, weights, impacts):
    X = df[criteria_cols].values.astype(float)

    denom = np.sqrt((X ** 2).sum(axis=0))
    if np.any(denom == 0):
        raise TopsisError("Some criteria column has all zeros; cannot normalize.")
    R = X / denom

    weights = weights / weights.sum()
    V = R * weights

    ideal_best = np.zeros(V.shape[1])
    ideal_worst = np.zeros(V.shape[1])

    for j in range(V.shape[1]):
        if impacts[j] == "+":
            ideal_best[j] = np.max(V[:, j])
            ideal_worst[j] = np.min(V[:, j])
        else:
            ideal_best[j] = np.min(V[:, j])
            ideal_worst[j] = np.max(V[:, j])

    S_plus = np.sqrt(((V - ideal_best) ** 2).sum(axis=1))
    S_minus = np.sqrt(((V - ideal_worst) ** 2).sum(axis=1))

    score = S_minus / (S_plus + S_minus)
    rank = score.argsort()[::-1].argsort() + 1

    df["Topsis Score"] = np.round(score, 6)
    df["Rank"] = rank

    return df
