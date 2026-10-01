import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)
from collections import Counter
from itertools import product
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ML_DIR = SCRIPT_DIR.parent
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SHARED_DIR = os.path.join(REPO_ROOT, "ml", "shared")

if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from features import FEATURE_COLUMNS

# Funzione di thresholding per predizioni
def apply_thresholding(probabilities, t_buy=0.55, t_sell=0.55):
    preds = []
    for p in probabilities:
        p_sell = p[0]
        p_hold = p[1]
        p_buy  = p[2]

        # BUY
        if p_buy >= t_buy and p_buy > p_sell:
            preds.append(2)
            continue

        # SELL
        if p_sell >= t_sell and p_sell > p_buy:
            preds.append(0)
            continue

        # HOLD
        preds.append(1)

    return np.array(preds)

def evaluate_thresholds(probabilities, y_true, t_buy_values, t_sell_values):
    results = []

    for t_buy, t_sell in product(t_buy_values, t_sell_values):
        preds = apply_thresholding(probabilities, t_buy=t_buy, t_sell=t_sell)
        preds_final = preds - 1  # convert 0,1,2 → -1,0,1

        prec = precision_score(y_true, preds_final, average=None, labels=[-1,0,1], zero_division=0)
        rec  = recall_score(y_true, preds_final, average=None, labels=[-1,0,1], zero_division=0)
        f1   = f1_score(y_true, preds_final, average=None, labels=[-1,0,1], zero_division=0)

        f1_sell = f1[0]
        f1_hold = f1[1]
        f1_buy  = f1[2]

        results.append({
            "t_buy": t_buy,
            "t_sell": t_sell,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "f1_mean": (f1_sell + f1_buy) / 2,
            "f1_sell": f1_sell,
            "f1_buy": f1_buy
        })

    return sorted(results, key=lambda x: x["f1_mean"], reverse=True)

# 1) Caricamento dati
train_df = pd.read_csv("eurusd_train.csv")
valid_df = pd.read_csv("eurusd_valid.csv")
test_df  = pd.read_csv("eurusd_test.csv")

# label -1,0,1 → 0,1,2
y_train = train_df["label_signal"].values + 1
y_valid = valid_df["label_signal"].values + 1
y_test  = test_df["label_signal"].values + 1

X_train = train_df[FEATURE_COLUMNS].values
X_valid = valid_df[FEATURE_COLUMNS].values
X_test  = test_df[FEATURE_COLUMNS].values

# 1.1) Calcolo pesi per bilanciare le classi
counts = Counter(train_df["label_signal"])
print("Class distribution:", counts)
total = sum(counts.values())
weights = {
    -1: total / (3 * counts[-1]),
     0: total / (3 * counts[0]),
     1: total / (3 * counts[1])
}
print("Weights:", weights)

# Mappa i pesi ai campioni di training
sample_weights = np.array([weights[label] for label in train_df["label_signal"].values])

# 2) Dataset LightGBM con pesi
lgb_train = lgb.Dataset(X_train, label=y_train, weight=sample_weights)
lgb_valid = lgb.Dataset(X_valid, label=y_valid, reference=lgb_train)

# 3) Parametri modello
params = {
    "objective": "multiclass",
    "num_class": 3,
    "learning_rate": 0.05,
    "num_leaves": 63,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "metric": "multi_logloss",
    "verbosity": -1
}

# 4) Training con early stopping
model = lgb.train(
    params,
    lgb_train,
    num_boost_round=1000,
    valid_sets=[lgb_valid],
    callbacks=[lgb.early_stopping(stopping_rounds=50)]
)

# 5) Salvataggio modello
model.save_model("eurusd_lgbm.txt")
print("Modello LightGBM salvato in eurusd_lgbm.txt")

# 6) Valutazione su test
y_pred_prob = model.predict(X_test, num_iteration=model.best_iteration)
#y_pred = np.argmax(y_pred_prob, axis=1)
y_pred = apply_thresholding(y_pred_prob, t_buy=0.38, t_sell=0.38)

# back to -1,0,1
y_pred_final = y_pred - 1
y_test_final = y_test - 1

# acc = accuracy_score(y_test_final, y_pred_final)
# prec = precision_score(y_test_final, y_pred_final, average=None, labels=[-1,0,1])
# rec = recall_score(y_test_final, y_pred_final, average=None, labels=[-1,0,1])
# f1 = f1_score(y_test_final, y_pred_final, average=None, labels=[-1,0,1])
# cm = confusion_matrix(y_test_final, y_pred_final, labels=[-1,0,1])

# print("\n=== METRICHE TEST (LightGBM) ===")
# print("Accuracy:", acc)
# print("Precision (SELL, HOLD, BUY):", prec)
# print("Recall    (SELL, HOLD, BUY):", rec)
# print("F1        (SELL, HOLD, BUY):", f1)
# print("\nConfusion Matrix (rows=actual, cols=predicted):\n", cm)

# Range di threshold da testare
t_buy_values  = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
t_sell_values = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

# Ottimizzazione
results = evaluate_thresholds(y_pred_prob, y_test_final, t_buy_values, t_sell_values)

# Migliore combinazione
best = results[0]

print("\n=== MIGLIOR THRESHOLD TROVATO ===")
print("T_buy:", best["t_buy"])
print("T_sell:", best["t_sell"])
print("F1 SELL:", best["f1_sell"])
print("F1 BUY:", best["f1_buy"])
print("F1 medio:", best["f1_mean"])
print("Precision:", best["precision"])
print("Recall:", best["recall"])
print("F1:", best["f1"])