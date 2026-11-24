"""Task 8 (and model development) - tuned models, MAE/MSE/RMSE/R2, residual analysis."""
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import GridSearchCV
from config import TARGET, SEED, BLUE, ORANGE, GREEN, RED, GREY, NAVY, LOC_COLORS, TABLES
from utils import savefig, build_features, metrics


def run(df, parts):
    tr, va, te = parts["train"], parts["val"], parts["test"]
    Xtr, Xva, Xte = build_features(tr), build_features(va), build_features(te)
    ytr, yva, yte = tr[TARGET].to_numpy(), va[TARGET].to_numpy(), te[TARGET].to_numpy()
    out = {}
    cols_simple = ["Area_sqft"]

    rf_grid = {"n_estimators": [200, 400], "max_depth": [5, 8, None], "min_samples_leaf": [1, 3, 5]}
    gb_grid = {"learning_rate": [0.03, 0.1], "n_estimators": [150, 300], "max_depth": [2, 3]}
    rf = GridSearchCV(RandomForestRegressor(random_state=SEED), rf_grid, cv=5,
                      scoring="neg_root_mean_squared_error", n_jobs=-1).fit(Xtr, ytr)
    gb = GridSearchCV(GradientBoostingRegressor(random_state=SEED), gb_grid, cv=5,
                      scoring="neg_root_mean_squared_error", n_jobs=-1).fit(Xtr, ytr)
    out["tuning"] = {
        "Random Forest": {"params": rf.best_params_, "cv_rmse": -rf.best_score_, "combinations": len(rf.cv_results_["params"])},
        "Gradient Boosting": {"params": gb.best_params_, "cv_rmse": -gb.best_score_, "combinations": len(gb.cv_results_["params"])}}

    models = {
        "Mean baseline": (DummyRegressor(strategy="mean").fit(Xtr[cols_simple], ytr), cols_simple),
        "Simple Linear Regression": (LinearRegression().fit(Xtr[cols_simple], ytr), cols_simple),
        "Multiple Linear Regression": (LinearRegression().fit(Xtr, ytr), list(Xtr.columns)),
        "Random Forest": (rf.best_estimator_, list(Xtr.columns)),
        "Gradient Boosting": (gb.best_estimator_, list(Xtr.columns))}
    val_m, test_m, preds = {}, {}, {}
    for name, (m, cols) in models.items():
        val_m[name] = metrics(yva, m.predict(Xva[cols]))
        preds[name] = m.predict(Xte[cols]); test_m[name] = metrics(yte, preds[name])
    learned = [k for k in models if k != "Mean baseline"]
    best = min(learned, key=lambda k: val_m[k]["RMSE"])
    out.update({"val_metrics": val_m, "test_metrics": test_m, "selected": best,
                "n_beat_baseline": sum(test_m[k]["RMSE"] < test_m["Mean baseline"]["RMSE"] for k in learned),
                "n_learned": len(learned)})
    pd.DataFrame(test_m).T.to_csv(TABLES / "test_metrics.csv"); pd.DataFrame(val_m).T.to_csv(TABLES / "validation_metrics.csv")

    # ---- comparison figure -------------------------------------------------------
    names = list(models)
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.2))
    for a, k in zip(ax, ["MAE", "RMSE", "R2"]):
        vals = [test_m[n][k] for n in names]
        cols = [GREY if n == "Mean baseline" else (ORANGE if n == best else BLUE) for n in names]
        a.barh(names, vals, color=cols, height=.6); a.invert_yaxis()
        for i, v in enumerate(vals): a.text(v, i, f" {round(v, 3) + 0.0:.3f}", va="center", fontsize=7)
        a.set(title=f"{k} (test set)" + (" - lakhs" if k != "R2" else "")); a.set_xlim(0, max(vals) * 1.2)
        if a is not ax[0]: a.set_yticklabels([])
    savefig(fig, "fig11_model_comparison")

    # ---- residual analysis (selected model) -------------------------------------
    p = preds[best]; res = yte - p                    # residual = actual - predicted
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.3))
    ax[0].scatter(p, res, s=9, alpha=.6, color=BLUE); ax[0].axhline(0, color=RED, ls="--", lw=1.2)
    ax[0].set(title="Residuals vs predicted", xlabel="Predicted price (Rs lakhs)", ylabel="Residual (lakhs)")
    sns.histplot(res, bins=25, kde=True, color=GREEN, ax=ax[1], edgecolor="white"); ax[1].axvline(0, color=RED, ls="--", lw=1.2)
    ax[1].set(title="Residual distribution", xlabel="Residual (lakhs)", ylabel="Count")
    stats.probplot(res, dist="norm", plot=ax[2]); ax[2].set_title("Residual Q-Q plot")
    ax[2].get_lines()[0].set(markersize=3, color=BLUE); ax[2].get_lines()[1].set(color=RED)
    savefig(fig, "fig12_residuals")

    fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.8))
    ax[0].scatter(yte, p, s=11, alpha=.6, color=BLUE)
    lim = [min(yte.min(), p.min()) - 3, max(yte.max(), p.max()) + 3]; ax[0].plot(lim, lim, color=RED, ls="--", label="perfect prediction")
    ax[0].set(title=f"Actual vs predicted - {best}", xlabel="Actual price (Rs lakhs)", ylabel="Predicted price (Rs lakhs)"); ax[0].legend(fontsize=7)
    sample = np.random.default_rng(SEED).choice(len(yte), 60, replace=False); sample.sort()
    ax[1].plot(np.arange(60), yte[sample], color=NAVY, lw=1.4, marker="o", ms=3, label="Actual")
    ax[1].plot(np.arange(60), p[sample], color=ORANGE, lw=1.4, ls="--", marker="o", ms=3, label="Predicted")
    ax[1].set(title="Actual vs predicted (60 random test houses)", xlabel="House (test sample)", ylabel="Price (Rs lakhs)"); ax[1].legend(fontsize=7)
    savefig(fig, "fig13_actual_vs_predicted")

    rows = []
    for n in names:
        r = yte - preds[n]
        tend = "unbiased" if abs(r.mean()) < 0.1 * r.std() else ("underestimates" if r.mean() > 0 else "overestimates")
        rows.append({"model": n, "mean_residual": r.mean(), "std": r.std(), "within_5": float(np.mean(np.abs(r) <= 5) * 100),
                     "within_10": float(np.mean(np.abs(r) <= 10) * 100), "tendency": tend})
    out["residual_summary"] = rows
    te2 = te.copy(); te2["residual"] = res; te2["abs_pct"] = np.abs(res / yte) * 100
    seg = te2.groupby("Location_Type").agg(n=("residual", "size"), mean_residual=("residual", "mean"),
                                           mape=("abs_pct", "mean")).round(2).reset_index()
    out["residual_by_location"] = seg.to_dict("records")
    te2["band"] = pd.qcut(te2[TARGET], 3, labels=["Low-priced", "Mid-priced", "High-priced"])
    band = te2.groupby("band", observed=True).agg(n=("residual", "size"), mean_residual=("residual", "mean")).round(2).reset_index()
    band["band"] = band["band"].astype(str); out["residual_by_price_band"] = band.to_dict("records")
    out["residual_stats"] = {"mean": res.mean(), "std": res.std(), "shapiro_p": stats.shapiro(res)[1],
                             "max_over": float(-res.min()), "max_under": float(res.max()),
                             "corr_resid_pred": float(np.corrcoef(p, res)[0, 1]),
                             "within_5": float(np.mean(np.abs(res) <= 5) * 100), "within_10": float(np.mean(np.abs(res) <= 10) * 100)}

    # ---- feature importance -------------------------------------------------------
    sd = Xtr.std()
    lin = models["Multiple Linear Regression"][0]
    std_coef = pd.Series(lin.coef_ * sd.to_numpy(), index=Xtr.columns).sort_values(key=abs)
    imp = pd.Series(rf.best_estimator_.feature_importances_, index=Xtr.columns).sort_values()
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    ax[0].barh(std_coef.index, std_coef.values, color=[BLUE if v > 0 else ORANGE for v in std_coef.values], height=.6)
    ax[0].set(title="Standardised coefficients (multiple regression)", xlabel="Effect of +1 SD on price (lakhs)")
    ax[1].barh(imp.index, imp.values, color=BLUE, height=.6); ax[1].set(title="Random forest feature importance", xlabel="Importance")
    savefig(fig, "fig14_feature_importance")
    out["rf_importance"] = imp.sort_values(ascending=False).round(4).to_dict()
    return out
