"""Tasks 4 and 5 - correlation analysis, simple and multiple linear regression (OLS)."""
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from config import NUMERIC, TARGET, BLUE, ORANGE, GREEN, RED, TABLES, LOC_COLORS
from utils import savefig, build_features, metrics


def ols(X, y, names):
    """Ordinary least squares with an intercept: coefficients, SE, t, p and 95% CI (NumPy)."""
    A = np.column_stack([np.ones(len(X)), X])
    beta = np.linalg.solve(A.T @ A, A.T @ y)
    resid = y - A @ beta
    n, k = A.shape
    sigma2 = resid @ resid / (n - k)
    se = np.sqrt(np.diag(sigma2 * np.linalg.inv(A.T @ A)))
    t = beta / se
    p = 2 * stats.t.sf(np.abs(t), n - k)
    tc = stats.t.ppf(0.975, n - k)
    r2 = 1 - resid @ resid / np.sum((y - y.mean()) ** 2)
    table = pd.DataFrame({"variable": ["Intercept"] + names, "coef": beta, "std_err": se, "t": t, "p": p,
                          "ci_low": beta - tc * se, "ci_high": beta + tc * se})
    return beta, table, r2, 1 - (1 - r2) * (n - 1) / (n - k)


def vif(X):
    out = {}
    for j, c in enumerate(X.columns):
        others = np.delete(X.to_numpy(), j, axis=1)
        _, _, r2, _ = ols(others, X.iloc[:, j].to_numpy(), list(range(others.shape[1])))
        out[c] = 1 / (1 - r2)
    return out


def run(df, parts):
    out = {}
    cols = NUMERIC + [TARGET]
    pear, spear = df[cols].corr("pearson"), df[cols].corr("spearman")
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
    for a, m, t in zip(ax, [pear, spear], ["Pearson correlation matrix", "Spearman correlation matrix"]):
        sns.heatmap(m, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1, ax=a, annot_kws={"size": 7},
                    cbar_kws={"shrink": .8}, linewidths=.4)
        a.set_title(t); a.tick_params(labelsize=7)
        a.set_xticklabels([c.replace("_", " ") for c in cols], rotation=40, ha="right")
        a.set_yticklabels([c.replace("_", " ") for c in cols], rotation=0)
    savefig(fig, "fig07_correlation_matrices")
    rows = []
    for c in NUMERIC:
        r, pr = stats.pearsonr(df[c], df[TARGET]); rho, ps = stats.spearmanr(df[c], df[TARGET])
        rows.append({"variable": c, "pearson_r": r, "pearson_p": pr, "spearman_rho": rho, "spearman_p": ps})
    ct = pd.DataFrame(rows).sort_values("pearson_r", key=abs, ascending=False)
    ct.to_csv(TABLES / "correlation_with_price.csv", index=False)
    out["corr_with_price"] = ct.to_dict("records")
    pear.to_csv(TABLES / "pearson_matrix.csv"); spear.to_csv(TABLES / "spearman_matrix.csv")
    # strongest pair among predictors
    pairs = [(a, b, pear.loc[a, b]) for i, a in enumerate(NUMERIC) for b in NUMERIC[i + 1:]]
    pairs.sort(key=lambda x: -abs(x[2]))
    out["top_predictor_pairs"] = [{"a": a, "b": b, "r": r} for a, b, r in pairs[:3]]

    top3 = ct["variable"].head(3).tolist()
    fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.3))
    for a, c, col in zip(ax, top3, [BLUE, ORANGE, GREEN]):
        a.scatter(df[c], df[TARGET], s=6, alpha=.35, color=col)
        m, b = np.polyfit(df[c], df[TARGET], 1); xs = np.linspace(df[c].min(), df[c].max(), 50)
        a.plot(xs, m * xs + b, color=RED, lw=1.5)
        a.set(title=f"Price vs {c.replace('_', ' ')}", xlabel=c.replace("_", " "), ylabel="Price (Rs lakhs)")
    savefig(fig, "fig08_top_scatter")

    # ---- regression (fit on training set only) ---------------------------------
    tr, va, te = parts["train"], parts["val"], parts["test"]
    ytr, yte = tr[TARGET].to_numpy(), te[TARGET].to_numpy()
    # simple: Area -> Price
    b_s, t_s, r2_s, adj_s = ols(tr[["Area_sqft"]].to_numpy(float), ytr, ["Area_sqft"])
    pred_s = b_s[0] + b_s[1] * te["Area_sqft"].to_numpy(float)
    out["simple"] = {"intercept": b_s[0], "slope": b_s[1], "train_r2": r2_s, "adj_r2": adj_s,
                     "table": t_s.round(5).to_dict("records"),
                     "test": metrics(yte, pred_s), "val": metrics(va[TARGET], b_s[0] + b_s[1] * va["Area_sqft"])}
    # multiple: all features
    Xtr, Xte = build_features(tr), build_features(te)
    b_m, t_m, r2_m, adj_m = ols(Xtr.to_numpy(), ytr, list(Xtr.columns))
    pred_m = b_m[0] + Xte.to_numpy() @ b_m[1:]
    t_m.to_csv(TABLES / "mlr_coefficients.csv", index=False)
    sd = Xtr.std().to_numpy()
    std_coef = pd.Series(b_m[1:] * sd, index=Xtr.columns).sort_values(key=abs, ascending=False)
    out["multiple"] = {"train_r2": r2_m, "adj_r2": adj_m, "table": t_m.round(5).to_dict("records"),
                       "std_coef": std_coef.round(3).to_dict(), "test": metrics(yte, pred_m),
                       "val": metrics(va[TARGET], b_m[0] + build_features(va).to_numpy() @ b_m[1:]),
                       "vif": {k: round(v, 2) for k, v in vif(Xtr[NUMERIC]).items()},
                       "f_stat": float((r2_m / (Xtr.shape[1])) / ((1 - r2_m) / (len(ytr) - Xtr.shape[1] - 1)))}
    out["multiple"]["f_p"] = float(stats.f.sf(out["multiple"]["f_stat"], Xtr.shape[1], len(ytr) - Xtr.shape[1] - 1))

    fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.8))
    for k, col in LOC_COLORS.items():
        s = tr[tr.Location_Type == k]
        ax[0].scatter(s["Area_sqft"], s[TARGET], s=7, alpha=.45, color=col, label=k)
    xs = np.linspace(tr["Area_sqft"].min(), tr["Area_sqft"].max(), 50)
    ax[0].plot(xs, b_s[0] + b_s[1] * xs, color=RED, lw=2, label="fitted line")
    ax[0].set(title="Simple linear regression (training data)", xlabel="Area (sq ft)", ylabel="Price (Rs lakhs)")
    ax[0].legend(fontsize=7)
    ax[1].scatter(yte, pred_m, s=10, alpha=.6, color=BLUE)
    lim = [min(yte.min(), pred_m.min()) - 3, max(yte.max(), pred_m.max()) + 3]
    ax[1].plot(lim, lim, color=RED, ls="--", lw=1.2)
    ax[1].set(title="Multiple linear regression (test set)", xlabel="Actual price (Rs lakhs)",
              ylabel="Predicted price (Rs lakhs)")
    savefig(fig, "fig09_regression")
    return out
