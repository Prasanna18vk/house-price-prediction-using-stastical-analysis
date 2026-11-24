"""Helpers shared by all modules: plotting style, feature building, metrics."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from config import FIGS, NUMERIC, TARGET, NAVY, BLUE, ORANGE, GREEN, GREY

sns.set_theme(style="whitegrid", font_scale=0.85)
plt.rcParams.update({"axes.titleweight": "bold", "axes.titlesize": 10, "axes.edgecolor": "#BBBBBB",
                     "grid.color": "#E5E7EB", "figure.dpi": 100})


def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(FIGS / f"{name}.png", dpi=200, facecolor="white")
    plt.close(fig)


def build_features(df):
    """Numeric features + dummy variables (baselines: Rural, Unfurnished)."""
    X = df[NUMERIC].astype(float).copy()
    X["Loc_Suburban"] = (df["Location_Type"] == "Suburban").astype(float)
    X["Loc_Urban"] = (df["Location_Type"] == "Urban").astype(float)
    X["Furn_Semi"] = (df["Furnishing"] == "Semi-Furnished").astype(float)
    X["Furn_Full"] = (df["Furnishing"] == "Furnished").astype(float)
    return X


def metrics(y, yhat):
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    r = y - yhat
    mse = float(np.mean(r ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return {"MAE": float(np.mean(np.abs(r))), "MSE": mse, "RMSE": float(np.sqrt(mse)),
            "R2": float(1 - np.sum(r ** 2) / ss_tot), "MAPE": float(np.mean(np.abs(r / y)) * 100)}


def split_xy(df):
    return build_features(df), df[TARGET].to_numpy(float)
