"""Run the whole pipeline: python src/run_all.py"""
import json, sys, warnings
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from config import RESULTS, DATA
import generate_data, preprocessing, statistics_analysis, probability_analysis
import correlation_regression, numpy_math, modeling


def clean(o):
    if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)): return float(o)
    if isinstance(o, (np.integer,)): return int(o)
    return o


if __name__ == "__main__":
    if not (DATA / "house_prices_raw.csv").exists():
        generate_data.generate().to_csv(DATA / "house_prices_raw.csv", index=False)
    df, parts, prep = preprocessing.run()
    res = {"preprocessing": prep}
    res["statistics"] = statistics_analysis.run(df)
    res["probability"] = probability_analysis.run(df)
    res["regression"] = correlation_regression.run(df, parts)
    res["math"] = numpy_math.run(df, parts)
    res["models"] = modeling.run(df, parts)
    (RESULTS / "results.json").write_text(json.dumps(clean(res), indent=2))
    m = res["models"]
    print("Selected model:", m["selected"])
    for k, v in m["test_metrics"].items():
        print(f"  {k:28s} MAE {v['MAE']:.2f}  RMSE {v['RMSE']:.2f}  R2 {v['R2']:.3f}")
