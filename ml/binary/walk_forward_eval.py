"""Walk-forward: finestra espandibile annuale su train+valid+test concatenati.

Verifica se il vantaggio di un feature-set (new/legacy) sullo split fisso
e' consistente nel tempo o dipende dal singolo periodo di validazione/test.
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import lightgbm as lgb
from sklearn.metrics import roc_auc_score, log_loss

SCRIPT_DIR = Path(__file__).resolve().parent
ML_DIR = SCRIPT_DIR.parent
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SHARED_DIR = os.path.join(REPO_ROOT, "ml", "shared")

if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from features import get_feature_columns, add_derived_features
from labels import triple_barrier_labels

TARGET_LONG_ATR = "target_long_atr_1"
TARGET_SHORT_ATR = "target_short_atr_1"


def load_all_years():
    frames = [
        pd.read_csv(ML_DIR / "eurusd_train.csv"),
        pd.read_csv(ML_DIR / "eurusd_valid.csv"),
        pd.read_csv(ML_DIR / "eurusd_test.csv"),
    ]
    df = add_derived_features(pd.concat(frames, ignore_index=True))
    df["timestamp_m5"] = pd.to_datetime(df["timestamp_m5"], utc=True)
    df["year"] = df["timestamp_m5"].dt.year
    return df.sort_values("timestamp_m5").reset_index(drop=True)


def train_and_score(X_train, y_train, X_valid, y_valid, num_leaves, min_data_in_leaf):
    pos = y_train.sum()
    neg = len(y_train) - pos

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
        "scale_pos_weight": neg / pos if pos > 0 else 1.0,
        "verbosity": -1,
    }

    train_data = lgb.Dataset(X_train, label=y_train)
    valid_data = lgb.Dataset(X_valid, label=y_valid)

    model = lgb.train(
        params,
        train_data,
        num_boost_round=2000,
        valid_sets=[valid_data],
        valid_names=["valid"],
        callbacks=[lgb.early_stopping(stopping_rounds=100, verbose=False)],
    )

    y_prob = model.predict(X_valid, num_iteration=model.best_iteration)
    return roc_auc_score(y_valid, y_prob), log_loss(y_valid, y_prob), model.best_iteration


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Walk-forward espandibile anno su anno, confronto feature-set.")
    parser.add_argument("--feature-sets", nargs="+", choices=["new", "legacy"], default=["new", "legacy"])
    parser.add_argument("--num-leaves", type=int, default=63)
    parser.add_argument("--min-data-in-leaf", type=int, default=50)
    parser.add_argument("--label-mode", choices=["atr", "triple-barrier"], default="atr")
    args = parser.parse_args()

    df = load_all_years()
    if args.label_mode == "triple-barrier":
        df = triple_barrier_labels(df, tf="m5")
        target_long_col = "target_long_tb_m5"
        target_short_col = "target_short_tb_m5"
    else:
        target_long_col = TARGET_LONG_ATR
        target_short_col = TARGET_SHORT_ATR

    years = sorted(df["year"].unique())
    # Ogni fold: train su tutti gli anni precedenti, valida sull'anno corrente
    fold_years = years[1:]

    print(f"Anni disponibili: {years}")

    for feature_set in args.feature_sets:
        feature_columns = get_feature_columns(feature_set)
        print(f"\n=== Feature set: {feature_set} ({len(feature_columns)} colonne) ===")

        for fold_year in fold_years:
            train_mask = df["year"] < fold_year
            valid_mask = df["year"] == fold_year

            train_part = df.loc[train_mask]
            valid_part = df.loc[valid_mask]

            if len(train_part) < 1000 or len(valid_part) < 100:
                print(f"Anno {fold_year}: dati insufficienti, salto")
                continue

            X_train = train_part[feature_columns].values
            X_valid = valid_part[feature_columns].values

            auc_long, ll_long, iter_long = train_and_score(
                X_train, train_part[target_long_col].values,
                X_valid, valid_part[target_long_col].values,
                args.num_leaves, args.min_data_in_leaf,
            )
            auc_short, ll_short, iter_short = train_and_score(
                X_train, train_part[target_short_col].values,
                X_valid, valid_part[target_short_col].values,
                args.num_leaves, args.min_data_in_leaf,
            )

            print(
                f"Anno {fold_year} (train {len(train_part)} righe, valid {len(valid_part)} righe): "
                f"AUC long={auc_long:.4f} (iter {iter_long:>4}, logloss {ll_long:.4f}), "
                f"AUC short={auc_short:.4f} (iter {iter_short:>4}, logloss {ll_short:.4f})"
            )
