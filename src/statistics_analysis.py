"""Task 2 - descriptive statistics, sampling and hypothesis testing."""
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from config import NUMERIC, TARGET, SEED, ALPHA, LOC_COLORS, BLUE, ORANGE, NAVY, GREY, GREEN, TABLES
from utils import savefig


def run(df):
    out = {}
    cols = NUMERIC + [TARGET]
    rows = []
    for c in cols:
        s = df[c]
        rows.append({"variable": c, "mean": s.mean(), "median": s.median(), "mode": s.mode()[0],
                     "variance": s.var(), "std": s.std(), "min": s.min(), "q1": s.quantile(.25),
                     "q3": s.quantile(.75), "max": s.max(), "skew": s.skew()})
    desc = pd.DataFrame(rows)
    desc.to_csv(TABLES / "descriptive_statistics.csv", index=False)
    out["descriptive"] = desc.round(3).to_dict("records")
    p = df[TARGET]
    out["price"] = {"mean": p.mean(), "median": p.median(), "std": p.std(), "skew": p.skew(),
                    "kurtosis": p.kurt(), "min": p.min(), "max": p.max(), "shapiro_p": stats.shapiro(p)[1]}
    out["by_location"] = df.groupby("Location_Type").agg(
        houses=(TARGET, "size"), mean_price=(TARGET, "mean"), median_price=(TARGET, "median"),
        mean_area=("Area_sqft", "mean")).round(2).reset_index().to_dict("records")
    out["by_furnishing"] = df.groupby("Furnishing").agg(
        houses=(TARGET, "size"), mean_price=(TARGET, "mean")).round(2).reset_index().to_dict("records")
    out["by_bedrooms"] = df.groupby("Bedrooms").agg(
        houses=(TARGET, "size"), mean_price=(TARGET, "mean")).round(2).reset_index().to_dict("records")

    # ---- figures: distribution -------------------------------------------------
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    sns.histplot(p, bins=30, kde=True, color=BLUE, ax=ax[0], edgecolor="white")
    ax[0].axvline(p.mean(), color=ORANGE, ls="--", label=f"mean {p.mean():.1f}")
    ax[0].axvline(p.median(), color=NAVY, ls=":", label=f"median {p.median():.1f}")
    ax[0].set(title="Distribution of house price", xlabel="Price (Rs lakhs)", ylabel="Count"); ax[0].legend()
    order = ["Urban", "Suburban", "Rural"]
    sns.boxplot(data=df, x="Location_Type", y=TARGET, order=order, palette=LOC_COLORS, ax=ax[1], linewidth=0.8)
    ax[1].set(title="Price by location type", xlabel="", ylabel="Price (Rs lakhs)")
    savefig(fig, "fig01_price_distribution")

    fig, ax = plt.subplots(1, 3, figsize=(10, 3.2))
    sns.barplot(data=df, x="Location_Type", y=TARGET, order=order, palette=LOC_COLORS, ax=ax[0], errorbar=None)
    sns.barplot(data=df, x="Furnishing", y=TARGET, order=["Unfurnished", "Semi-Furnished", "Furnished"],
                color=BLUE, ax=ax[1], errorbar=None)
    sns.barplot(data=df, x="Bedrooms", y=TARGET, color=ORANGE, ax=ax[2], errorbar=None)
    for a, t in zip(ax, ["Mean price by location", "Mean price by furnishing", "Mean price by bedrooms"]):
        a.set(title=t, xlabel="", ylabel="Mean price (Rs lakhs)")
    ax[1].tick_params(axis="x", labelsize=7)
    savefig(fig, "fig02_group_means")

    fig, ax = plt.subplots(2, 3, figsize=(10, 5))
    for a, c in zip(ax.ravel(), ["Area_sqft", "Age_years", "Distance_to_City_km", "Neighborhood_Rating",
                                  "Bedrooms", "Parking_Spaces"]):
        sns.histplot(df[c], bins=20 if df[c].nunique() > 10 else df[c].nunique(), color=BLUE, ax=a,
                     edgecolor="white", discrete=df[c].nunique() <= 10)
        a.set(title=c.replace("_", " "), xlabel="", ylabel="Count")
    savefig(fig, "fig03_feature_distributions")

    # ---- sampling --------------------------------------------------------------
    rng = np.random.default_rng(SEED)
    mu, sigma = p.mean(), p.std(ddof=0)
    srs = df.sample(100, random_state=SEED)[TARGET]
    se = srs.std() / np.sqrt(100)
    ci = stats.t.interval(0.95, 99, loc=srs.mean(), scale=se)
    share = df["Location_Type"].value_counts(normalize=True)
    strat = pd.concat([df[df.Location_Type == k].sample(int(round(100 * v)), random_state=SEED)
                       for k, v in share.items()])[TARGET]
    means30 = np.array([rng.choice(p.to_numpy(), 30, replace=False).mean() for _ in range(1000)])
    out["sampling"] = {
        "population_mean": mu, "srs_n": 100, "srs_mean": srs.mean(), "srs_se": se,
        "srs_ci": [ci[0], ci[1]], "strat_n": len(strat), "strat_mean": strat.mean(),
        "clt_n": 30, "clt_samples": 1000, "clt_mean_of_means": means30.mean(),
        "clt_std_of_means": means30.std(ddof=1), "clt_theory_se": sigma / np.sqrt(30),
        "clt_skew_of_means": float(stats.skew(means30))}
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.3))
    sns.histplot(p, bins=30, color=GREY, ax=ax[0], edgecolor="white")
    ax[0].set(title="Population (1,000 prices)", xlabel="Price (Rs lakhs)", ylabel="Count")
    sns.histplot(means30, bins=25, color=BLUE, ax=ax[1], edgecolor="white", stat="density")
    xs = np.linspace(means30.min(), means30.max(), 200)
    ax[1].plot(xs, stats.norm.pdf(xs, mu, sigma / np.sqrt(30)), color=ORANGE, lw=2, label="Normal (theory)")
    ax[1].set(title="Means of 1,000 samples (n = 30)", xlabel="Sample mean (Rs lakhs)", ylabel="Density")
    ax[1].legend()
    savefig(fig, "fig04_sampling_distribution")

    # ---- hypothesis test: Urban vs Suburban ------------------------------------
    a = df[df.Location_Type == "Urban"][TARGET].to_numpy()
    b = df[df.Location_Type == "Suburban"][TARGET].to_numpy()
    t, pv = stats.ttest_ind(a, b, equal_var=False)
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    dof = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    diff = a.mean() - b.mean(); se_d = np.sqrt(va + vb); tc = stats.t.ppf(0.975, dof)
    sp = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    groups = [df[df.Location_Type == k][TARGET] for k in order]
    f, pf = stats.f_oneway(*groups)
    out["hypothesis"] = {
        "group_a": "Urban", "group_b": "Suburban", "n_a": len(a), "n_b": len(b),
        "mean_a": a.mean(), "mean_b": b.mean(), "diff": diff, "ci": [diff - tc * se_d, diff + tc * se_d],
        "t": t, "df": dof, "p": pv, "cohens_d": diff / sp, "alpha": ALPHA,
        "mannwhitney_p": stats.mannwhitneyu(a, b)[1], "levene_p": stats.levene(a, b)[1],
        "shapiro_p_a": stats.shapiro(a)[1], "shapiro_p_b": stats.shapiro(b)[1],
        "decision": "Reject H0" if pv < ALPHA else "Fail to reject H0",
        "anova_F": f, "anova_p": pf}
    fig, ax = plt.subplots(figsize=(6, 3.3))
    ax.hist(a, bins=25, alpha=.7, color=BLUE, label=f"Urban (mean {a.mean():.1f})", edgecolor="white")
    ax.hist(b, bins=25, alpha=.7, color=ORANGE, label=f"Suburban (mean {b.mean():.1f})", edgecolor="white")
    ax.set(title="Hypothesis test: price in two location types", xlabel="Price (Rs lakhs)", ylabel="Houses")
    ax.legend()
    savefig(fig, "fig05_hypothesis_test")
    return out
