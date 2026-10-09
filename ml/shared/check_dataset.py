"""Controlli di coerenza sui CSV generati dal data-engine.

1. ATR: atr14_m5 deve essere vicino all'ATR di Wilder ricalcolato dagli OHLC m5.
2. Label: target_long_atr_1 deve coincidere con (close[i+20]-close[i])/atr14_m5[i] > 1 sulla stessa riga.

Uso: py ml/shared/check_dataset.py ml/eurusd_train.csv ml/eurusd_valid.csv ml/eurusd_test.csv
"""
import sys

import numpy as np
import pandas as pd

HORIZON = 20
ATR_RATIO_MAX = 1.5
LABEL_AGREEMENT_MIN = 0.97


def check(path):
    df = pd.read_csv(path, usecols=["timestamp_m5", "high_m5", "low_m5", "close_m5", "atr14_m5", "target_long_atr_1"])
    close = df["close_m5"].to_numpy(dtype=float)
    atr_csv = pd.to_numeric(df["atr14_m5"], errors="coerce").to_numpy(dtype=float)

    prev_close = df["close_m5"].shift(1)
    tr = np.maximum(df["high_m5"] - df["low_m5"],
                    np.maximum((df["high_m5"] - prev_close).abs(), (df["low_m5"] - prev_close).abs()))
    tr.iloc[0] = df["high_m5"].iloc[0] - df["low_m5"].iloc[0]
    atr_true = tr.ewm(alpha=1 / 14, adjust=False).mean().to_numpy()
    ratio = float(np.nanmedian(atr_csv / atr_true))

    move = np.full(len(df), np.nan)
    move[:-HORIZON] = (close[HORIZON:] - close[:-HORIZON]) / atr_csv[:-HORIZON]
    expected = (move > 1.0).astype(float)
    valid = ~np.isnan(move)
    label = df["target_long_atr_1"].to_numpy(dtype=float)
    # Accordo per blocchi: se le label scorrono, l'accordo cala man mano che si avanza nel file
    blocks = np.array_split(np.flatnonzero(valid), 5)
    agreement = [float(np.mean(label[b] == expected[b])) for b in blocks]

    ok_atr = ratio <= ATR_RATIO_MAX
    ok_label = min(agreement) >= LABEL_AGREEMENT_MIN
    print(f"{path}: righe={len(df)} | ATR csv/ricalcolato mediano={ratio:.2f} {'OK' if ok_atr else 'KO'} | "
          f"accordo label per blocco={[round(a, 3) for a in agreement]} {'OK' if ok_label else 'KO'}")
    return ok_atr and ok_label


if __name__ == "__main__":
    results = [check(p) for p in sys.argv[1:]]
    sys.exit(0 if all(results) else 1)
