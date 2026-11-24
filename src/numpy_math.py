"""Tasks 6 and 7 - linear algebra, cost function, derivatives and gradient descent with NumPy only."""
import numpy as np
import matplotlib.pyplot as plt
from config import NUMERIC, TARGET, BLUE, ORANGE, GREEN, RED, GREY
from utils import savefig, build_features, metrics


def cost(X, y, w):
    r = X @ w - y
    return float(r @ r / (2 * len(y)))            # J(w) = (1/2m) * sum (Xw - y)^2


def gradient(X, y, w):
    return X.T @ (X @ w - y) / len(y)              # dJ/dw = (1/m) X^T (Xw - y)


def gradient_descent(X, y, alpha, iters):
    w = np.zeros(X.shape[1]); costs, path = [cost(X, y, w)], [w.copy()]
    for _ in range(iters):
        w = w - alpha * gradient(X, y, w)
        costs.append(cost(X, y, w)); path.append(w.copy())
    return w, np.array(costs), np.array(path)


def run(df, parts):
    out = {}
    tr, te = parts["train"], parts["test"]
    # ---- Task 6: vectors, matrices, dot products ---------------------------------
    price_vec = df[TARGET].to_numpy()[:7]
    feat = build_features(df)[NUMERIC].to_numpy()
    M1, M2 = feat[:5, :4], feat[5:10, :4]
    A = tr[["Area_sqft"]].to_numpy(float).ravel(); y = tr[TARGET].to_numpy()
    Ac, yc = A - A.mean(), y - y.mean()
    Xd = np.column_stack([np.ones(7), feat[:7]])
    out["linear_algebra"] = {
        "vector": price_vec.tolist(), "vector_shape": list(price_vec.shape),
        "matrix_shape": list(feat[:7].shape),
        "matrix_add_mean_first_row": ((M1 + M2) / 2)[0].tolist(),
        "dot_area_price_centered": float(Ac @ yc),
        "cosine_area_price": float(Ac @ yc / (np.linalg.norm(Ac) * np.linalg.norm(yc))),
        "xtx_shape": list((Xd.T @ Xd).shape),
        "price_row1_features": feat[0].tolist(),
    }
    # ---- Task 7: standardise, normal equation, cost, gradient descent -----------
    Xtr_raw, Xte_raw = build_features(tr).to_numpy(), build_features(te).to_numpy()
    mu, sd = Xtr_raw.mean(0), Xtr_raw.std(0)
    Xtr = np.column_stack([np.ones(len(Xtr_raw)), (Xtr_raw - mu) / sd])
    Xte = np.column_stack([np.ones(len(Xte_raw)), (Xte_raw - mu) / sd])
    ytr, yte = tr[TARGET].to_numpy(), te[TARGET].to_numpy()
    out["linear_algebra"]["xtx_condition_number"] = float(np.linalg.cond(Xtr.T @ Xtr))
    w_ne = np.linalg.solve(Xtr.T @ Xtr, Xtr.T @ ytr)                # normal equation
    alpha, iters = 0.1, 2000
    w_gd, costs, path = gradient_descent(Xtr, ytr, alpha, iters)
    cols = ["intercept"] + list(build_features(tr).columns)
    out["gradient_descent"] = {
        "alpha": alpha, "iterations": iters, "initial_cost": costs[0], "cost_10": costs[10],
        "cost_100": costs[100], "final_cost": costs[-1], "normal_eq_cost": cost(Xtr, ytr, w_ne),
        "max_weight_diff": float(np.abs(w_gd - w_ne).max()), "test": metrics(yte, Xte @ w_gd),
        "weights_gd": dict(zip(cols, np.round(w_gd, 3))), "weights_ne": dict(zip(cols, np.round(w_ne, 3)))}
    lr = {}
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
    ax[0].plot(costs, color=BLUE, lw=2); ax[0].axhline(cost(Xtr, ytr, w_ne), color=RED, ls="--", label="normal-equation minimum")
    ax[0].set(title="Cost J(w) during gradient descent", xlabel="Iteration", ylabel="Cost", yscale="log"); ax[0].legend(fontsize=7)
    cmap = plt.get_cmap("tab20")
    for j, c in enumerate(cols[1:], 1):          # intercept (~95) is left out so the others stay visible
        ax[1].plot(path[:, j], lw=1.2, color=cmap(j - 1), label=c)
    ax[1].set(title="Parameter values during gradient descent", xlabel="Iteration", ylabel="Weight (excluding intercept)")
    ax[1].set_ylim(top=24); ax[1].legend(fontsize=5.5, ncol=2, loc="upper right")
    for a_, col in zip([0.001, 0.01, 0.1, 0.5], [GREY, ORANGE, BLUE, GREEN]):
        _, c_, _ = gradient_descent(Xtr, ytr, a_, 200)
        lr[str(a_)] = float(c_[-1]); ax[2].plot(c_, color=col, lw=1.6, label=f"alpha = {a_}")
    ax[2].set(title="Effect of the learning rate", xlabel="Iteration", ylabel="Cost", yscale="log"); ax[2].legend(fontsize=7, loc="center right")
    savefig(fig, "fig10_gradient_descent")
    out["gradient_descent"]["cost_after_200_by_alpha"] = lr
    return out
