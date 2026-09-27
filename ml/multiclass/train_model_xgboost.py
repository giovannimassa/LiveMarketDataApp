import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

# -----------------------------
# 1. Feature list
# -----------------------------
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

# -----------------------------
# 2. Load datasets
# -----------------------------
train_df = pd.read_csv("eurusd_train.csv")
valid_df = pd.read_csv("eurusd_valid.csv")
test_df  = pd.read_csv("eurusd_test.csv")

X_train = train_df[FEATURE_COLUMNS].values
y_train = train_df["label_signal"].values + 1  # convert -1,0,1 → 0,1,2

X_valid = valid_df[FEATURE_COLUMNS].values
y_valid = valid_df["label_signal"].values + 1

X_test = test_df[FEATURE_COLUMNS].values
y_test = test_df["label_signal"].values + 1

# -----------------------------
# 3. Train XGBoost
# -----------------------------
dtrain = xgb.DMatrix(X_train, label=y_train)
dvalid = xgb.DMatrix(X_valid, label=y_valid)
dtest  = xgb.DMatrix(X_test,  label=y_test)

params = {
    "objective": "multi:softprob",
    "num_class": 3,
    "eta": 0.05,
    "max_depth": 8,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "eval_metric": "mlogloss"
}

evals = [(dtrain, "train"), (dvalid, "valid")]

model = xgb.train(
    params,
    dtrain,
    num_boost_round=500,
    evals=evals,
    early_stopping_rounds=30
)

# -----------------------------
# 4. Save model
# -----------------------------
model.save_model("eurusd_model.json")
print("Modello salvato in eurusd_model.json")

# -----------------------------
# 5. Evaluate on test set
# -----------------------------
y_pred_prob = model.predict(dtest)
y_pred = np.argmax(y_pred_prob, axis=1)

# Convert back to -1,0,1
y_pred_final = y_pred - 1
y_test_final = y_test - 1

# Metrics
acc = accuracy_score(y_test_final, y_pred_final)
prec = precision_score(y_test_final, y_pred_final, average=None, labels=[-1,0,1])
rec = recall_score(y_test_final, y_pred_final, average=None, labels=[-1,0,1])
f1 = f1_score(y_test_final, y_pred_final, average=None, labels=[-1,0,1])
cm = confusion_matrix(y_test_final, y_pred_final, labels=[-1,0,1])

print("\n=== METRICHE TEST ===")
print("Accuracy:", acc)
print("Precision (SELL, HOLD, BUY):", prec)
print("Recall    (SELL, HOLD, BUY):", rec)
print("F1        (SELL, HOLD, BUY):", f1)
print("\nConfusion Matrix (rows=actual, cols=predicted):\n", cm)