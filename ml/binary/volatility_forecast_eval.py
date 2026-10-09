"""Previsione della volatilita' realizzata a breve termine, walk-forward annuale.

Target: log del range (max high - min low) delle prossime H barre m5, diviso per il close.
Confronto fra: persistenza dell'ATR, stagionalita' ora-della-settimana e LightGBM sulle feature.
Fold: train < Y-1, validation Y-1 (early stopping), test Y, con embargo di H barre.
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import r2_score

SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = os.path.join(os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..")), "ml", "shared")
for _p in (SHARED_DIR, str(SCRIPT_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from features import get_feature_columns
from walk_forward_eval_trade import load_all_years

PIP = 0.0001


def add_vol_target(df, horizon):
    high, low, close = df["high_m5"], df["low_m5"], df["close_m5"]
    fut_high = high.rolling(horizon).max().shift(-horizon)
    fut_low = low.rolling(horizon).min().shift(-horizon)
    rng = (fut_high - fut_low).clip(lower=PIP / 10)
    y = np.log(rng / close)
    # Scarta le finestre che attraversano un buco di dati (weekend, festivi)
    span = (df["timestamp_m5"].shift(-horizon) - df["timestamp_m5"]).dt.total_seconds()
    y[span > horizon * 300 * 1.5] = np.nan
    df = df.copy()
    df["y"] = y
    df["range_pips"] = rng / PIP
    return df


def fit_lgbm(X_train, y_train, X_valid, y_valid):
    params = {"objective": "regression", "learning_rate": 0.05, "num_leaves": 31, "min_data_in_leaf": 500,
              "feature_fraction": 0.8, "bagging_fraction": 0.8, "bagging_freq": 1, "lambda_l2": 5.0, "verbosity": -1}
    return lgb.train(params, lgb.Dataset(X_train, label=y_train), num_boost_round=1500,
                     valid_sets=[lgb.Dataset(X_valid, label=y_valid)],
                     callbacks=[lgb.early_stopping(stopping_rounds=100, verbose=False)])


def week_key(part):
    return (part["timestamp_m5"].dt.dayofweek * 24 + part["timestamp_m5"].dt.hour).to_numpy()


def top_quintile_lift(pred, realized_pips):
    cut = np.quantile(pred, 0.8)
    return realized_pips[pred >= cut].mean(), realized_pips[pred <= np.quantile(pred, 0.2)].mean(), realized_pips.mean()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizons", type=int, nargs="+", default=[12, 48])
    parser.add_argument("--feature-set", choices=["new", "legacy"], default="new")
    args = parser.parse_args()

    base = load_all_years()
    cols = get_feature_columns(args.feature_set)
    base["log_atr_m5"] = np.log(pd.to_numeric(base["atr14_m5"]) / base["close_m5"])
    years = sorted(base["year"].unique())

    for horizon in args.horizons:
        df = add_vol_target(base, horizon)
        print(f"\n=== Orizzonte {horizon} barre m5 ({horizon * 5} min), feature set {args.feature_set} ===")
        rows = []
        for test_year in years[2:]:
            tr = df[df["year"] < test_year - 1].iloc[:-horizon]
            va = df[df["year"] == test_year - 1].iloc[:-horizon]
            te = df[df["year"] == test_year]
            tr, va, te = (p[p["y"].notna()] for p in (tr, va, te))

            # Persistenza: regressione lineare di y su log(ATR/close)
            slope, intercept = np.polyfit(tr["log_atr_m5"], tr["y"], 1)
            p_persist = intercept + slope * te["log_atr_m5"].to_numpy()
            # Stagionalita' ora-della-settimana
            season = tr.groupby(week_key(tr))["y"].mean()
            p_season = pd.Series(week_key(te)).map(season).fillna(tr["y"].mean()).to_numpy()
            # LightGBM sulle feature
            model = fit_lgbm(tr[cols].values, tr["y"].values, va[cols].values, va["y"].values)
            p_lgbm = model.predict(te[cols].values, num_iteration=model.best_iteration)

            y = te["y"].to_numpy()
            pips = te["range_pips"].to_numpy()
            r = {"year": test_year}
            for name, p in (("persist", p_persist), ("season", p_season), ("lgbm", p_lgbm)):
                r[f"r2_{name}"] = r2_score(y, p)
                r[f"sp_{name}"] = pd.Series(p).corr(pd.Series(y), method="spearman")
            top, bottom, overall = top_quintile_lift(p_lgbm, pips)
            r.update(top_pips=top, bottom_pips=bottom, all_pips=overall)
            rows.append(r)
            print(f"Test {test_year}: R2 persist={r['r2_persist']:.3f} season={r['r2_season']:.3f} lgbm={r['r2_lgbm']:.3f} | "
                  f"Spearman persist={r['sp_persist']:.3f} season={r['sp_season']:.3f} lgbm={r['sp_lgbm']:.3f} | "
                  f"range medio previsto alto/basso/tutto = {top:.1f}/{bottom:.1f}/{overall:.1f} pip")

        res = pd.DataFrame(rows)
        print("Media fold: " + " ".join(f"{c}={res[c].mean():.3f}" for c in res.columns if c.startswith(("r2_", "sp_"))))
        print(f"Range realizzato medio (pip): quintile alto={res['top_pips'].mean():.1f} basso={res['bottom_pips'].mean():.1f} "
              f"tutto={res['all_pips'].mean():.1f} -> costo spread 0.8 pip = {0.8 / res['top_pips'].mean() * 100:.1f}% (alto) "
              f"vs {0.8 / res['bottom_pips'].mean() * 100:.1f}% (basso) del range")
