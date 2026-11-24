"""Task 1 - load, inspect, clean and split the data."""
import numpy as np
import pandas as pd
from config import DATA, NUMERIC, CATEGORICAL, TARGET, SEED


def run():
    raw = pd.read_csv(DATA / "house_prices_raw.csv")
    out = {"raw_rows": len(raw), "raw_cols": raw.shape[1]}
    out["missing_before"] = {k: int(v) for k, v in raw.isna().sum().items() if v}
    out["duplicates"] = int(raw.duplicated().sum())
    df = raw.drop_duplicates().reset_index(drop=True)

    # impute: median for numeric, mode for categorical
    imputed = {}
    for c in NUMERIC:
        n = int(df[c].isna().sum())
        if n:
            imputed[c] = {"count": n, "method": "median", "value": float(df[c].median())}
            df[c] = df[c].fillna(df[c].median())
    for c in CATEGORICAL:
        n = int(df[c].isna().sum())
        if n:
            imputed[c] = {"count": n, "method": "mode", "value": df[c].mode()[0]}
            df[c] = df[c].fillna(df[c].mode()[0])
    out["imputed"] = imputed
    for c in ["Age_years", "Neighborhood_Rating"]:
        df[c] = df[c].round().astype(int)

    # impossible values
    bad = int(((df["Area_sqft"] <= 0) | (df[TARGET] <= 0) | (df["Age_years"] < 0)
               | (~df["Neighborhood_Rating"].between(1, 10))).sum())
    out["impossible_values"] = bad
    out["clean_rows"] = len(df)
    out["numeric_vars"] = NUMERIC + [TARGET]
    out["categorical_vars"] = CATEGORICAL
    out["id_column"] = "House_ID"

    # IQR outlier check
    rows = []
    for c in ["Area_sqft", "Distance_to_City_km", "Age_years", TARGET]:
        q1, q3 = df[c].quantile([.25, .75]); i = q3 - q1
        lo, hi = q1 - 1.5 * i, q3 + 1.5 * i
        rows.append({"variable": c, "lower": float(lo), "upper": float(hi),
                     "outliers": int(((df[c] < lo) | (df[c] > hi)).sum())})
    out["outliers"] = rows
    df.to_csv(DATA / "house_prices_clean.csv", index=False)

    # random 70 / 15 / 15 split
    idx = np.random.default_rng(SEED).permutation(len(df))
    n_tr, n_va = int(0.70 * len(df)), int(0.15 * len(df))
    parts = {"train": df.iloc[idx[:n_tr]], "val": df.iloc[idx[n_tr:n_tr + n_va]], "test": df.iloc[idx[n_tr + n_va:]]}
    out["split"] = {k: len(v) for k, v in parts.items()}
    return df, parts, out
