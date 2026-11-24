"""Task 3 - probability, conditional probability, Bayes' theorem, law of large numbers."""
import numpy as np
import matplotlib.pyplot as plt
from config import HIGH_PRICE, BIG_AREA, TARGET, SEED, BLUE, ORANGE, GREEN, RED
from utils import savefig


def run(df):
    high = df[TARGET] > HIGH_PRICE
    large = df["Area_sqft"] > BIG_AREA
    urban = df["Location_Type"] == "Urban"
    p_high, p_large = high.mean(), large.mean()
    p_high_large = high[large].mean()
    p_high_small = high[~large].mean()
    p_urban = urban.mean()
    p_high_urban = high[urban].mean()
    bayes = p_high_urban * p_urban / p_high           # P(Urban | high)
    direct = urban[high].mean()
    out = {"threshold_price": HIGH_PRICE, "threshold_area": BIG_AREA,
           "n_high": int(high.sum()), "n": len(df), "p_high": p_high, "p_large": p_large,
           "p_high_and_large": (high & large).mean(), "p_high_given_large": p_high_large,
           "p_high_given_not_large": p_high_small, "p_urban": p_urban,
           "p_high_given_urban": p_high_urban, "p_urban_given_high_bayes": bayes,
           "p_urban_given_high_direct": direct, "independence_product": p_high * p_large}

    # Law of large numbers
    rng = np.random.default_rng(SEED)
    ind = high.to_numpy().astype(float)
    fig, ax = plt.subplots(figsize=(7, 3.4))
    errs = []
    for k, col in enumerate([BLUE, ORANGE, GREEN], 1):
        s = rng.choice(ind, 2000, replace=True)
        run_mean = np.cumsum(s) / np.arange(1, 2001)
        ax.plot(np.arange(1, 2001), run_mean, color=col, lw=1.2, label=f"random sample {k}")
        errs.append({"sample": k, "err_n10": abs(run_mean[9] - p_high), "err_n2000": abs(run_mean[-1] - p_high)})
    ax.axhline(p_high, color=RED, ls="--", lw=1.2, label=f"true P(high) = {p_high:.3f}")
    ax.set(title="Law of large numbers: running share of high-priced houses", xlabel="Number of sampled houses",
           ylabel="Sample proportion", ylim=(0, 1)); ax.legend(fontsize=7)
    savefig(fig, "fig06_law_of_large_numbers")
    out["lln"] = errs
    return out
