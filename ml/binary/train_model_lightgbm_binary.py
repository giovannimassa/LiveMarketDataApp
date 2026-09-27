import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    log_loss
)

# ============================================================
# CONFIG
# ============================================================
TARGET_LONG_ATR = "target_long_atr_1"
TARGET_SHORT_ATR = "target_short_atr_1"

TRAIN_CSV = "../eurusd_train.csv"
VALID_CSV = "../eurusd_valid.csv"

MODEL_LONG_PATH = "model_long.txt"
MODEL_SHORT_PATH = "model_short.txt"
MODEL_LONG_ATR_PATH = "model_long_atr.txt"
MODEL_SHORT_ATR_PATH = "model_short_atr.txt"

FEATURE_COLUMNS = [
    "open_m5","close_m5","high_m5","low_m5","volume_m5",
    "sma20_m5","sma50_m5","ema20_m5","ema50_m5","ema100_m5","ema200_m5",
    "bbands20_m5","rsi14_m5","atr14_m5","macdNorm_m5","slopeEma_m5",
    "distanceEma_m5","roc_m5","stoch_m5","obv_m5","volumeZScore_m5",
    "volumeAtrRatio_m5","fvgBullish_m5","fvgBearish_m5","fvgSize_m5",
    "fvgSizeAtrNorm_m5","bodySizePerc_m5","upperWickPerc_m5",
    "lowerWickPerc_m5","rangeExp_m5","logReturn_m5","rollingVolatility_m5",
    "rollingVolatilityAtrNorm_m5","rollingVolatilitySlope_m5",
    "sma20_m15","sma50_m15","ema20_m15","ema50_m15","ema100_m15",
    "ema200_m15","bbands20_m15","rsi14_m15","atr14_m15","macdNorm_m15",
    "slopeEma_m15","distanceEma_m15","roc_m15","stoch_m15","obv_m15",
    "volumeZScore_m15","volumeAtrRatio_m15","fvgBullish_m15",
    "fvgBearish_m15","fvgSize_m15","fvgSizeAtrNorm_m15","bodySizePerc_m15",
    "upperWickPerc_m15","lowerWickPerc_m15","rangeExp_m15","logReturn_m15",
    "rollingVolatility_m15","rollingVolatilityAtrNorm_m15",
    "rollingVolatilitySlope_m15",
    "sma20_h1","sma50_h1","ema20_h1","ema50_h1","ema100_h1","ema200_h1",
    "bbands20_h1","rsi14_h1","atr14_h1","macdNorm_h1","slopeEma_h1",
    "distanceEma_h1","roc_h1","stoch_h1","obv_h1","volumeZScore_h1",
    "volumeAtrRatio_h1","fvgBullish_h1","fvgBearish_h1","fvgSize_h1",
    "fvgSizeAtrNorm_h1","bodySizePerc_h1","upperWickPerc_h1",
    "lowerWickPerc_h1","rangeExp_h1","logReturn_h1","rollingVolatility_h1",
    "rollingVolatilityAtrNorm_h1","rollingVolatilitySlope_h1"
]

# ============================================================
# FUNZIONE GENERALE DI TRAINING BINARIO
# ============================================================
def train_binary_model(X_train, y_train, X_valid, y_valid, model_path, model_name):

    # Calcolo automatico del peso della classe positiva
    pos = y_train.sum()
    neg = len(y_train) - pos
    scale_pos_weight = neg / pos if pos > 0 else 1.0

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
        "num_leaves": 63,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "min_data_in_leaf": 50,
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

    train_df = pd.read_csv(TRAIN_CSV)
    valid_df = pd.read_csv(VALID_CSV)

    # print("target_long: ", train_df["target_long"].mean())
    # print("target_short: ", train_df["target_short"].mean())

    print("target_long_atr: ", train_df[TARGET_LONG_ATR].mean())
    print("target_short_atr: ", train_df[TARGET_SHORT_ATR].mean())

    X_train = train_df[FEATURE_COLUMNS].values
    X_valid = valid_df[FEATURE_COLUMNS].values

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
        X_train, train_df[TARGET_LONG_ATR].values,
        X_valid, valid_df[TARGET_LONG_ATR].values,
        MODEL_LONG_ATR_PATH,
        "MODEL_LONG_ATR"
    )

    # --------------------------------------------------------
    # MODELLO SHORT ATR
    # --------------------------------------------------------
    model_short_atr = train_binary_model(
        X_train, train_df[TARGET_SHORT_ATR].values,
        X_valid, valid_df[TARGET_SHORT_ATR].values,
        MODEL_SHORT_ATR_PATH,
        "MODEL_SHORT_ATR"
    )