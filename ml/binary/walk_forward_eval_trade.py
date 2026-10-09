"""Walk-forward a livello di trade, con costi e senza look-ahead.

Per ogni anno di test Y: train su anni < Y-1, validation su Y-1 (early stopping e scelta
della soglia), test su Y. Le ultime `embargo` barre di train e validation vengono scartate
perche' le loro label guardano nel periodo successivo. La metrica e' il backtest netto.
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb

SCRIPT_DIR = Path(__file__).resolve().parent
ML_DIR = SCRIPT_DIR.parent
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SHARED_DIR = os.path.join(REPO_ROOT, "ml", "shared")

for _p in (SHARED_DIR, str(SCRIPT_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from features import get_feature_columns, add_derived_features, add_true_atr
from labels import triple_barrier_labels
from backtest_optimized import PIP, simulate, summarize, select_thresholds

TARGET_LONG_ATR = "target_long_atr_1"
TARGET_SHORT_ATR = "target_short_atr_1"


def load_all_years():
    frames = [pd.read_csv(ML_DIR / f"eurusd_{name}.csv") for name in ("train", "valid", "test")]
    df = add_derived_features(pd.concat(frames, ignore_index=True))
    df["timestamp_m5"] = pd.to_datetime(df["timestamp_m5"], utc=True)
    df = df.sort_values("timestamp_m5").reset_index(drop=True)
    df["year"] = df["timestamp_m5"].dt.year
    return df


def fit(X_train, y_train, X_valid, y_valid, num_leaves, min_data_in_leaf, use_spw, extra=None):
    pos = y_train.sum()
    spw = (len(y_train) - pos) / pos if (pos > 0 and use_spw) else 1.0
    params = {
        "objective": "binary",
        "learning_rate": 0.03,
        "num_leaves": num_leaves,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "min_data_in_leaf": min_data_in_leaf,
        "lambda_l1": 1.0,
        "lambda_l2": 1.0,
        "metric": "binary_logloss",
        "scale_pos_weight": spw,
        "verbosity": -1,
        **(extra or {}),
    }
    return lgb.train(
        params,
        lgb.Dataset(X_train, label=y_train),
        num_boost_round=2000,
        valid_sets=[lgb.Dataset(X_valid, label=y_valid)],
        callbacks=[lgb.early_stopping(stopping_rounds=100, verbose=False)],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Walk-forward a livello di trade con spread.")
    parser.add_argument("--feature-sets", nargs="+", choices=["new", "legacy"], default=["new", "legacy"])
    parser.add_argument("--num-leaves", type=int, default=31)
    parser.add_argument("--min-data-in-leaf", type=int, default=500)
    parser.add_argument("--label-mode", choices=["atr", "triple-barrier", "direction"], default="atr",
                        help="direction: un solo modello su triple-barrier, addestrato solo dove vince esattamente una direzione")
    parser.add_argument("--scale-pos-weight", choices=["auto", "none"], default="none")
    parser.add_argument("--spread-pips", type=float, default=0.8)
    parser.add_argument("--embargo-bars", type=int, default=24)
    parser.add_argument("--min-trades", type=int, default=100)
    parser.add_argument("--session-filter", action="store_true")
    parser.add_argument("--true-atr", action="store_true",
                        help="SL/TP e label triple-barrier con ATR ricalcolato dagli OHLC (non influisce sulle feature)")
    parser.add_argument("--sl-mult", type=float, default=1.0, help="SL in multipli di ATR (label triple-barrier e simulazione)")
    parser.add_argument("--tp-mult", type=float, default=2.0, help="TP in multipli di ATR (label triple-barrier e simulazione)")
    parser.add_argument("--max-bars", type=int, default=24, help="Barre massime di permanenza nel trade")
    parser.add_argument("--learning-rate", type=float, default=0.03)
    parser.add_argument("--atr-col", default=None, help="Colonna ATR per barriere e label (es. atr14_h1); default atr14_m5")
    parser.add_argument("--sample-hours", type=int, default=0,
                        help="Se > 0, si entra solo a inizio ora con ora UTC multipla di N (riduce la sovrapposizione dei trade)")
    parser.add_argument("--feature-fraction", type=float, default=0.8)
    parser.add_argument("--lambda-l2", type=float, default=1.0)
    parser.add_argument("--max-depth", type=int, default=-1)
    parser.add_argument("--top-k", type=int, default=0,
                        help="Se > 0, in ogni fold tiene le K feature con gain maggiore (calcolato solo sul train) e riaddestra")
    args = parser.parse_args()
    extra = {"learning_rate": args.learning_rate, "feature_fraction": args.feature_fraction,
             "lambda_l2": args.lambda_l2, "max_depth": args.max_depth}

    df = load_all_years()
    atr_col = args.atr_col or ("atr_true_m5" if args.true_atr else "atr14_m5")
    if args.true_atr:
        df = add_true_atr(df)
    if args.label_mode in ("triple-barrier", "direction"):
        df = triple_barrier_labels(df, tf="m5", atr_col=atr_col, sl_mult=args.sl_mult, tp_mult=args.tp_mult, max_bars=args.max_bars)
        target_long, target_short = "target_long_tb_m5", "target_short_tb_m5"
        long_win, short_win = df[target_long], df[target_short]
        df["target_dir"] = np.where((long_win == 1) & (short_win == 0), 1.0,
                                    np.where((short_win == 1) & (long_win == 0), 0.0, np.nan))
    else:
        target_long, target_short = TARGET_LONG_ATR, TARGET_SHORT_ATR

    spread = args.spread_pips * PIP
    years = sorted(df["year"].unique())
    fold_years = years[2:]
    print(f"Anni: {years} | fold di test: {fold_years} | spread {args.spread_pips} pip | label {args.label_mode} | "
          f"scale_pos_weight {args.scale_pos_weight} | SL {args.sl_mult} ATR, TP {args.tp_mult} ATR, max {args.max_bars} barre")
    print(f"LightGBM: num_leaves={args.num_leaves} min_data_in_leaf={args.min_data_in_leaf} {extra} top_k={args.top_k}")

    for feature_set in args.feature_sets:
        cols = get_feature_columns(feature_set)
        print(f"\n=== Feature set: {feature_set} ({len(cols)} colonne) ===")
        results = []
        importance = {}

        for test_year in fold_years:
            val_year = test_year - 1
            train = df[df["year"] < val_year].iloc[:-args.embargo_bars]
            valid = df[df["year"] == val_year].iloc[:-args.embargo_bars].reset_index(drop=True)
            test = df[df["year"] == test_year].reset_index(drop=True)
            if len(train) < 1000 or len(valid) < 1000 or len(test) < 1000:
                print(f"Test {test_year}: dati insufficienti, salto")
                continue

            use_spw = args.scale_pos_weight == "auto"
            X_train, X_valid, X_test = (part[cols].values for part in (train, valid, test))

            def train_pair(Xtr, Xv):
                if args.label_mode == "direction":
                    mt, mv = train["target_dir"].notna().to_numpy(), valid["target_dir"].notna().to_numpy()
                    m = fit(Xtr[mt], train.loc[mt, "target_dir"].values, Xv[mv], valid.loc[mv, "target_dir"].values,
                            args.num_leaves, args.min_data_in_leaf, use_spw, extra)
                    return m, m
                ml = fit(Xtr, train[target_long].values, Xv, valid[target_long].values,
                         args.num_leaves, args.min_data_in_leaf, use_spw, extra)
                ms = fit(Xtr, train[target_short].values, Xv, valid[target_short].values,
                         args.num_leaves, args.min_data_in_leaf, use_spw, extra)
                return ml, ms

            m_long, m_short = train_pair(X_train, X_valid)
            gain_l = m_long.feature_importance("gain")
            gain_s = m_short.feature_importance("gain")
            gain = gain_l / max(gain_l.sum(), 1e-12) + gain_s / max(gain_s.sum(), 1e-12)
            for name, g in zip(cols, gain):
                importance[name] = importance.get(name, 0.0) + g / 2

            if args.top_k > 0:
                keep = np.argsort(gain)[::-1][:args.top_k]
                X_train, X_valid, X_test = X_train[:, keep], X_valid[:, keep], X_test[:, keep]
                m_long, m_short = train_pair(X_train, X_valid)

            pv_long = m_long.predict(X_valid, num_iteration=m_long.best_iteration)
            pv_short = m_short.predict(X_valid, num_iteration=m_short.best_iteration)
            pt_long = m_long.predict(X_test, num_iteration=m_long.best_iteration)
            pt_short = m_short.predict(X_test, num_iteration=m_short.best_iteration)
            if args.label_mode == "direction":
                pv_short, pt_short = 1 - pv_long, 1 - pt_long

            kw = {"session_filter": args.session_filter, "atr_col": atr_col,
                  "sl_mult": args.sl_mult, "tp_mult": args.tp_mult, "max_bars": args.max_bars}
            def entry_mask(part):
                if args.sample_hours <= 0:
                    return None
                return ((part["timestamp_m5"].dt.minute == 0) & (part["timestamp_m5"].dt.hour % args.sample_hours == 0)).to_numpy()

            best, _ = select_thresholds(valid, pv_long, pv_short, spread, min_trades=args.min_trades,
                                        **kw, signal_mask=entry_mask(valid))
            trades = simulate(test, pt_long, pt_short, best["t_long"], best["t_short"], spread=spread,
                              **kw, signal_mask=entry_mask(test))
            stats = summarize(trades)
            results.append({"test_year": test_year, "q": best["quantile"], "valid_net": best["net_pnl"], **stats})

            print(f"Test {test_year} (train {len(train)}, valid {len(valid)}, iter {m_long.best_iteration}/{m_short.best_iteration}): "
                  f"q={best['quantile']} valid_net={best['net_pnl']:+.4f} | TEST trade={stats['num_trades']:>4} "
                  f"lordo={stats['gross_pnl']:+.4f} netto={stats['net_pnl']:+.4f} pips/trade={stats['avg_net_pips']:+.3f} "
                  f"PF={stats['profit_factor']:.3f} winrate={stats['winrate']:.3f}")

        if results:
            res = pd.DataFrame(results)
            print(f"-> Fold con PNL netto > 0: {(res['net_pnl'] > 0).sum()}/{len(res)} | "
                  f"fold con PF > 1.2: {(res['profit_factor'] > 1.2).sum()}/{len(res)} | "
                  f"PNL netto totale: {res['net_pnl'].sum():+.4f} | trade totali: {int(res['num_trades'].sum())}")
            top = sorted(importance.items(), key=lambda kv: kv[1], reverse=True)
            n_folds = len(res)
            print("Importanza media (gain normalizzato, modelli a tutte le feature): "
                  + ", ".join(f"{n}={v / n_folds:.3f}" for n, v in top[:15]))
            print("Feature meno importanti: " + ", ".join(f"{n}={v / n_folds:.4f}" for n, v in top[-10:]))
