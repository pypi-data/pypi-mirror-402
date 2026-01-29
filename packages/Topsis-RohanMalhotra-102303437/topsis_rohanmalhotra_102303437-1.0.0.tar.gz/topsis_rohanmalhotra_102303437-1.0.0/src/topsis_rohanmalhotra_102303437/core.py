import math
import os
from typing import List, Tuple

import pandas as pd


class TopsisError(Exception):
    """Raised for TOPSIS input/processing errors."""


def _parse_weights_impacts(weights_s: str, impacts_s: str) -> Tuple[List[float], List[str]]:
    if "," not in weights_s or "," not in impacts_s:
        raise TopsisError("Impacts and weights must be separated by ',' (comma).")

    weights_raw = [w.strip() for w in weights_s.split(",") if w.strip() != ""]
    impacts_raw = [i.strip() for i in impacts_s.split(",") if i.strip() != ""]

    try:
        weights = [float(w) for w in weights_raw]
    except ValueError as e:
        raise TopsisError("Weights must be numeric values separated by commas.") from e

    impacts = impacts_raw
    for imp in impacts:
        if imp not in ["+", "-"]:
            raise TopsisError("Impacts must be either '+' or '-' separated by commas.")

    return weights, impacts


def _validate_input_df(df: pd.DataFrame) -> None:
    if df.shape[1] < 3:
        raise TopsisError("Input file must contain three or more columns.")

    crit = df.iloc[:, 1:]
    for col in crit.columns:
        coerced = pd.to_numeric(crit[col], errors="coerce")
        if coerced.isna().any():
            raise TopsisError("From 2nd to last columns must contain numeric values only.")


def topsis_dataframe(df: pd.DataFrame, weights: List[float], impacts: List[str]) -> pd.DataFrame:
    out = df.copy()

    crit = out.iloc[:, 1:].apply(pd.to_numeric)
    n_criteria = crit.shape[1]

    if len(weights) != n_criteria or len(impacts) != n_criteria:
        raise TopsisError(
            "The number of weights, impacts and number of columns (from 2nd to last) must be the same."
        )

    denom = (crit ** 2).sum(axis=0).apply(math.sqrt)
    denom = denom.replace(0, 1.0)
    norm = crit / denom

    w = pd.Series(weights, index=crit.columns, dtype=float)
    weighted = norm * w

    ideal_best = pd.Series(index=crit.columns, dtype=float)
    ideal_worst = pd.Series(index=crit.columns, dtype=float)
    for col, imp in zip(crit.columns, impacts):
        if imp == "+":
            ideal_best[col] = weighted[col].max()
            ideal_worst[col] = weighted[col].min()
        else:
            ideal_best[col] = weighted[col].min()
            ideal_worst[col] = weighted[col].max()

    d_best = ((weighted - ideal_best) ** 2).sum(axis=1).apply(math.sqrt)
    d_worst = ((weighted - ideal_worst) ** 2).sum(axis=1).apply(math.sqrt)

    score = d_worst / (d_best + d_worst)
    out["Topsis Score"] = score
    out["Rank"] = out["Topsis Score"].rank(ascending=False, method="dense").astype(int)
    return out


def topsis_from_file(input_path: str, weights_s: str, impacts_s: str) -> pd.DataFrame:
    if not os.path.isfile(input_path):
        raise TopsisError("File not Found")

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise TopsisError("Unable to read input file. Ensure it is a valid CSV.") from e

    _validate_input_df(df)
    weights, impacts = _parse_weights_impacts(weights_s, impacts_s)
    return topsis_dataframe(df, weights, impacts)
