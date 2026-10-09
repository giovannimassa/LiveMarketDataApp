import argparse
import itertools
import os
import sys
from pathlib import Path

import pandas as pd
import lightgbm as lgb
from sklearn.metrics import roc_auc_score

SCRIPT_DIR = Path(__file__).resolve().parent
ML_DIR = SCRIPT_DIR.parent
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SHARED_DIR = os.path.join(REPO_ROOT, "ml", "shared")

if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from features import get_feature_columns, add_derived_features

TARGET_LONG_ATR = "target_long_atr_1"
TARGET_SHORT_ATR = "target_short_atr_1"

TRAIN_CSV = ML_DIR / "eurusd_train.csv"
VALID_CSV = ML_DIR / "eurusd_valid.csv"


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
    return roc_auc_score(y_valid, y_prob), model.best_iteration


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grid search di num_leaves/min_data_in_leaf sullo split train/valid esistente.")
    parser.add_argument("--feature-set", choices=["new", "legacy"], default="new")
    parser.add_argument("--num-leaves", type=int, nargs="+", default=[15, 31])
    parser.add_argument("--min-data-in-leaf", type=int, nargs="+", default=[300, 500, 1000])
    args = parser.parse_args()

    feature_columns = get_feature_columns(args.feature_set)
    train_df = add_derived_features(pd.read_csv(TRAIN_CSV))
    valid_df = add_derived_features(pd.read_csv(VALID_CSV))

    X_train = train_df[feature_columns].values
    X_valid = valid_df[feature_columns].values

    results = []
    for num_leaves, min_data_in_leaf in itertools.product(args.num_leaves, args.min_data_in_leaf):
        auc_long, iter_long = train_and_score(
            X_train, train_df[TARGET_LONG_ATR].values,
            X_valid, valid_df[TARGET_LONG_ATR].values,
            num_leaves, min_data_in_leaf,
        )
        auc_short, iter_short = train_and_score(
            X_train, train_df[TARGET_SHORT_ATR].values,
            X_valid, valid_df[TARGET_SHORT_ATR].values,
            num_leaves, min_data_in_leaf,
        )
        avg_auc = (auc_long + auc_short) / 2
        results.append({
            "num_leaves": num_leaves,
            "min_data_in_leaf": min_data_in_leaf,
            "auc_long": auc_long,
            "iter_long": iter_long,
            "auc_short": auc_short,
            "iter_short": iter_short,
            "avg_auc": avg_auc,
        })
        print(
            f"num_leaves={num_leaves:>3} min_data_in_leaf={min_data_in_leaf:>5} -> "
            f"AUC long={auc_long:.4f} (iter {iter_long:>4}), "
            f"AUC short={auc_short:.4f} (iter {iter_short:>4}), avg={avg_auc:.4f}"
        )

    best = max(results, key=lambda r: r["avg_auc"])
    print("\nMigliore combinazione per AUC medio:", best)
