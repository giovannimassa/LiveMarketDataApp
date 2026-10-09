import argparse
import pandas as pd
import numpy as np
import lightgbm as lgb
import os
import sys
from pathlib import Path
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    log_loss
)

SCRIPT_DIR = Path(__file__).resolve().parent
ML_DIR = SCRIPT_DIR.parent
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SHARED_DIR = os.path.join(REPO_ROOT, "ml", "shared")

if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from features import get_feature_columns, model_suffix, add_derived_features
from labels import triple_barrier_labels

# ============================================================
# CONFIG
# ============================================================
TARGET_LONG_ATR = "target_long_atr_1"
TARGET_SHORT_ATR = "target_short_atr_1"

TRAIN_CSV = ML_DIR / "eurusd_train.csv"
VALID_CSV = ML_DIR / "eurusd_valid.csv"

MODEL_LONG_PATH = SCRIPT_DIR / "model_long.txt"
MODEL_SHORT_PATH = SCRIPT_DIR / "model_short.txt"

# ============================================================
# FUNZIONE GENERALE DI TRAINING BINARIO
# ============================================================
def train_binary_model(X_train, y_train, X_valid, y_valid, model_path, model_name, num_leaves=63, min_data_in_leaf=50, use_scale_pos_weight=True):

    # Calcolo automatico del peso della classe positiva
    pos = y_train.sum()
    neg = len(y_train) - pos
    scale_pos_weight = neg / pos if (pos > 0 and use_scale_pos_weight) else 1.0

    print(f"\n[{model_name}] Positivi: {pos}, Negativi: {neg}, scale_pos_weight={scale_pos_weight:.2f}")

    train_data = lgb.Dataset(X_train, label=y_train)
    valid_data = lgb.Dataset(X_valid, label=y_valid)

    # params = {
    #     "objective": "binary",
    #     "learning_rate": 0.03,
    #     "num_leaves": 63,
    #     "feature_fraction": 0.8,
    #     "bagging_fraction": 0.8,
    #     "bagging_freq": 1,
    #     "min_data_in_leaf": 50,
    #     "lambda_l1": 1.0,
    #     "lambda_l2": 1.0,
    #     "metric": "binary_logloss",
    #     # "scale_pos_weight": scale_pos_weight,
    #     "verbosity": -1
    # }

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
        "scale_pos_weight": scale_pos_weight,
        "verbosity": -1
    }

    THRESHOLD = 0.20

    model = lgb.train(
        params,
        train_data,
        num_boost_round=2000,
        valid_sets=[valid_data],
        valid_names=["valid"],
        callbacks=[lgb.early_stopping(stopping_rounds=100)]
    )

    model.save_model(model_path)
    print(f"Modello salvato: {model_path}")

    # --------------------------------------------------------
    # METRICHE
    # --------------------------------------------------------
    y_prob = model.predict(X_valid, num_iteration=model.best_iteration)
    # y_prob = model.predict(X_valid)

    # threshold
    y_pred = (y_prob >= THRESHOLD).astype(int)

    print(f"\n=== METRICHE VALID ({model_name}) ===")
    print("Threshold:", THRESHOLD)
    print("Accuracy:", accuracy_score(y_valid, y_pred))
    print("Precision:", precision_score(y_valid, y_pred, zero_division=0))
    print("Recall:", recall_score(y_valid, y_pred, zero_division=0))
    print("F1:", f1_score(y_valid, y_pred, zero_division=0))
    print("AUC:", roc_auc_score(y_valid, y_prob))
    print("LogLoss:", log_loss(y_valid, y_prob))

    return model


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--feature-set",
        choices=["new", "legacy"],
        default=os.environ.get("FEATURE_SET", "new"),
        help="Elenco di feature da usare per il training (default: new)",
    )
    parser.add_argument("--num-leaves", type=int, default=63, help="Parametro LightGBM num_leaves (default: 63)")
    parser.add_argument("--min-data-in-leaf", type=int, default=50, help="Parametro LightGBM min_data_in_leaf (default: 50)")
    parser.add_argument(
        "--label-mode",
        choices=["atr", "triple-barrier"],
        default="atr",
        help="atr: movimento a 20 candele > k*ATR (default). triple-barrier: TP/SL path-dependent come in backtest.py",
    )
    parser.add_argument(
        "--scale-pos-weight",
        choices=["auto", "none"],
        default="auto",
        help="auto: pesa la classe positiva (probabilita' gonfiate). none: probabilita' non distorte",
    )
    parser.add_argument(
        "--output-suffix",
        default=None,
        help="Suffisso aggiuntivo per i file modello, per non sovrascrivere altri esperimenti (default: quello legato al feature-set)",
    )
    args = parser.parse_args()
    feature_columns = get_feature_columns(args.feature_set)
    suffix = args.output_suffix if args.output_suffix is not None else (
        model_suffix(args.feature_set) + ("_tb" if args.label_mode == "triple-barrier" else "")
    )

    train_df = add_derived_features(pd.read_csv(TRAIN_CSV))
    valid_df = add_derived_features(pd.read_csv(VALID_CSV))

    if args.label_mode == "triple-barrier":
        train_df = triple_barrier_labels(train_df, tf="m5")
        valid_df = triple_barrier_labels(valid_df, tf="m5")
        target_long_col = "target_long_tb_m5"
        target_short_col = "target_short_tb_m5"
    else:
        target_long_col = TARGET_LONG_ATR
        target_short_col = TARGET_SHORT_ATR

    print(f"{target_long_col}: ", train_df[target_long_col].mean())
    print(f"{target_short_col}: ", train_df[target_short_col].mean())

    X_train = train_df[feature_columns].values
    X_valid = valid_df[feature_columns].values

    # --------------------------------------------------------
    # MODELLO LONG (RETURN-BASED)
    # --------------------------------------------------------
    # model_long = train_binary_model(
    #     X_train, train_df["target_long"].values,
    #     X_valid, valid_df["target_long"].values,
    #     MODEL_LONG_PATH,
    #     "MODEL_LONG"
    # )

    # --------------------------------------------------------
    # MODELLO SHORT (RETURN-BASED)
    # --------------------------------------------------------
    # model_short = train_binary_model(
    #     X_train, train_df["target_short"].values,
    #     X_valid, valid_df["target_short"].values,
    #     MODEL_SHORT_PATH,
    #     "MODEL_SHORT"
    # )

    # --------------------------------------------------------
    # MODELLO LONG ATR
    # --------------------------------------------------------
    model_long_atr = train_binary_model(
        X_train, train_df[target_long_col].values,
        X_valid, valid_df[target_long_col].values,
        SCRIPT_DIR / f"model_long_atr{suffix}.txt",
        "MODEL_LONG_ATR",
        num_leaves=args.num_leaves,
        min_data_in_leaf=args.min_data_in_leaf,
        use_scale_pos_weight=args.scale_pos_weight == "auto",
    )

    # --------------------------------------------------------
    # MODELLO SHORT ATR
    # --------------------------------------------------------
    model_short_atr = train_binary_model(
        X_train, train_df[target_short_col].values,
        X_valid, valid_df[target_short_col].values,
        SCRIPT_DIR / f"model_short_atr{suffix}.txt",
        "MODEL_SHORT_ATR",
        num_leaves=args.num_leaves,
        min_data_in_leaf=args.min_data_in_leaf,
        use_scale_pos_weight=args.scale_pos_weight == "auto",
    )
