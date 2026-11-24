"""Quick correctness checks: python -m pytest tests"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import generate_data, numpy_math, correlation_regression as cr
from utils import metrics


def test_dataset_shape_and_duplicates():
    df = generate_data.generate()
    assert len(df) == 1012 and df.duplicated().sum() == 12
    assert df["Age_years"].isna().sum() > 0


def test_metrics_perfect_and_known():
    y = np.array([1., 2., 3.])
    assert metrics(y, y)["RMSE"] == 0 and metrics(y, y)["R2"] == 1
    m = metrics(y, y + 1)
    assert m["MAE"] == 1 and m["MSE"] == 1 and m["RMSE"] == 1


def test_gradient_matches_numerical_derivative():
    rng = np.random.default_rng(0)
    X, y, w = rng.normal(size=(50, 3)), rng.normal(size=50), rng.normal(size=3)
    g = numpy_math.gradient(X, y, w)
    eps = 1e-6
    num = np.array([(numpy_math.cost(X, y, w + eps * e) - numpy_math.cost(X, y, w - eps * e)) / (2 * eps)
                    for e in np.eye(3)])
    assert np.allclose(g, num, atol=1e-6)


def test_gradient_descent_reaches_normal_equation():
    rng = np.random.default_rng(1)
    X = np.column_stack([np.ones(200), rng.normal(size=(200, 2))])
    y = X @ np.array([5., 2., -3.]) + rng.normal(0, .1, 200)
    w, costs, _ = numpy_math.gradient_descent(X, y, 0.1, 1000)
    assert np.allclose(w, np.linalg.solve(X.T @ X, X.T @ y), atol=1e-4) and costs[-1] < costs[0]


def test_ols_recovers_coefficients():
    rng = np.random.default_rng(2)
    X = rng.normal(size=(500, 2)); y = 1 + 2 * X[:, 0] - X[:, 1] + rng.normal(0, .1, 500)
    beta, table, r2, _ = cr.ols(X, y, ["a", "b"])
    assert np.allclose(beta, [1, 2, -1], atol=0.05) and r2 > 0.99
