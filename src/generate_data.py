"""Generate the synthetic housing dataset (reproducible, seed = 42).

The dataset is SYNTHETIC: prices follow a hedonic (feature-based) pricing rule plus
random noise, so that the statistical methods can be demonstrated on a known process.
To use real data instead, replace data/house_prices_raw.csv with a CSV that has the
same column names and run `python src/run_all.py`.

Raw file deliberately contains a few missing values and duplicate rows
(injected at random) so that the cleaning step has something real to do.
"""
import numpy as np
import pandas as pd
from config import DATA, N_HOUSES, SEED


def generate(n=N_HOUSES, seed=SEED):
    rng = np.random.default_rng(seed)
    loc = rng.choice(["Urban", "Suburban", "Rural"], size=n, p=[0.40, 0.40, 0.20])
    loc_area = {"Urban": -100, "Suburban": 0, "Rural": 200}
    area = np.array([rng.normal(1400 + loc_area[l], 420) for l in loc]).clip(500, 3500).round(-1)
    dist = np.array([{"Urban": rng.gamma(4, 1.6), "Suburban": rng.gamma(6, 2.5),
                      "Rural": rng.gamma(8, 4.2)}[l] for l in loc])
    dist = np.clip(dist, 1, 60).round(1)
    bedrooms = np.clip(np.round(area / 550 + rng.normal(0, 0.6, n)), 1, 5).astype(int)
    bathrooms = np.clip(bedrooms + rng.choice([-1, 0, 0, 1], n), 1, 4).astype(int)
    age = np.clip(rng.gamma(2, 7, n), 0, 45).round().astype(int)
    rating_mu = {"Urban": 6.7, "Suburban": 6.2, "Rural": 5.4}
    rating = np.clip(np.round([rng.normal(rating_mu[l], 1.6) for l in loc]), 1, 10).astype(int)
    parking = np.array([rng.choice([0, 1, 2], p={"Urban": [.3, .5, .2], "Suburban": [.15, .5, .35],
                                                  "Rural": [.05, .35, .6]}[l]) for l in loc])
    furnishing = rng.choice(["Unfurnished", "Semi-Furnished", "Furnished"], n, p=[.35, .40, .25])

    loc_eff = pd.Series(loc).map({"Urban": 12, "Suburban": 0, "Rural": -6}).to_numpy()
    furn_eff = pd.Series(furnishing).map({"Unfurnished": 0, "Semi-Furnished": 2.5, "Furnished": 5}).to_numpy()
    base = (12 + 0.034 * area + 3.5 * bedrooms + 2.5 * bathrooms - 0.45 * age
            - 0.55 * dist + 4.2 * rating + 3.0 * parking + loc_eff + furn_eff)
    price = np.clip(base * (1 + rng.normal(0, 0.06, n)), 15, None).round(1)   # 6% multiplicative noise

    df = pd.DataFrame({
        "House_ID": [f"H{i:04d}" for i in range(1, n + 1)],
        "Location_Type": loc, "Area_sqft": area.astype(int), "Bedrooms": bedrooms,
        "Bathrooms": bathrooms, "Age_years": age, "Distance_to_City_km": dist,
        "Neighborhood_Rating": rating, "Parking_Spaces": parking, "Furnishing": furnishing,
        "Price_Lakhs": price})

    # inject ~1.5% missing values in two columns and 12 duplicate rows
    for col in ["Age_years", "Neighborhood_Rating"]:
        idx = rng.choice(n, size=int(0.015 * n), replace=False)
        df[col] = df[col].astype("float")
        df.loc[idx, col] = np.nan
    dups = df.sample(12, random_state=seed)
    df = pd.concat([df, dups]).sample(frac=1, random_state=seed).reset_index(drop=True)
    return df


if __name__ == "__main__":
    out = generate()
    out.to_csv(DATA / "house_prices_raw.csv", index=False)
    print(f"Saved {len(out)} raw rows to {DATA / 'house_prices_raw.csv'}")
