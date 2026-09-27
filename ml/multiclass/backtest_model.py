import pandas as pd
import numpy as np
import lightgbm as lgb
from collections import Counter
from itertools import product

# ============================================================
# CONFIG
# ============================================================
MODEL_PATH = "eurusd_lgbm.txt"
CSV_TEST   = "eurusd_test.csv"

T_BUY  = 0.30
T_SELL = 0.30

N_MAX_BARS = 24
ATR_SL_MULT = 1.0
ATR_TP_MULT = 2.0

# ============================================================
# FEATURE LIST
# ============================================================
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
# THRESHOLDING
# ============================================================
def apply_thresholding(probabilities, t_buy=T_BUY, t_sell=T_SELL):
    preds = []
    for p in probabilities:
        p_sell = p[0]
        p_hold = p[1]
        p_buy  = p[2]

        if p_buy >= t_buy and p_buy > p_sell:
            preds.append(1)
            continue

        if p_sell >= t_sell and p_sell > p_buy:
            preds.append(-1)
            continue

        preds.append(0)

    return np.array(preds)

# ============================================================
# BACKTEST ENGINE
# ============================================================
def run_backtest(df, signals):
    equity = 0.0
    trades = []

    prices = df["close_m5"].values
    atr    = df["atr14_m5"].values

    i = 0
    n = len(df)

    while i < n:
        sig = signals[i]

        if sig == 0:
            i += 1
            continue

        entry_price = prices[i]
        atr_val     = atr[i]
        sl = ATR_SL_MULT * atr_val
        tp = ATR_TP_MULT * atr_val

        direction = sig
        entry_index = i

        exit_price = None
        exit_reason = None

        j = i + 1
        while j < n and j - i <= N_MAX_BARS:
            high = df["high_m5"].iloc[j]
            low  = df["low_m5"].iloc[j]

            if direction == 1:
                if high >= entry_price + tp:
                    exit_price = entry_price + tp
                    exit_reason = "TP"
                    break
                if low <= entry_price - sl:
                    exit_price = entry_price - sl
                    exit_reason = "SL"
                    break
            else:
                if low <= entry_price - tp:
                    exit_price = entry_price - tp
                    exit_reason = "TP"
                    break
                if high >= entry_price + sl:
                    exit_price = entry_price + sl
                    exit_reason = "SL"
                    break

            j += 1

        if exit_price is None:
            exit_price = prices[min(j, n - 1)]
            exit_reason = "TIME"

        # Limita j ai limiti del dataframe
        j = min(j, n - 1)

        pnl = exit_price - entry_price if direction == 1 else entry_price - exit_price
        equity += pnl

        trades.append({
            "entry_index": entry_index,
            "exit_index": j,
            "direction": direction,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "reason": exit_reason,
            "entry_time": df["timestamp_m5"].iloc[entry_index],
            "exit_time": df["timestamp_m5"].iloc[j],
            "entry_year": df["year"].iloc[entry_index],
            "entry_month": df["month"].iloc[entry_index],
            "entry_hour": df["hour"].iloc[entry_index]
        })

        i = j

    return equity, trades

# ============================================================
# ANALISI TRADE
# ============================================================
def analyze_trades(trades):
    if not trades:
        return {}

    pnls = np.array([t["pnl"] for t in trades])
    wins = pnls[pnls > 0]
    losses = pnls[pnls <= 0]

    total_pnl = pnls.sum()
    winrate = len(wins) / len(trades)
    avg_win = wins.mean() if len(wins) > 0 else 0.0
    avg_loss = losses.mean() if len(losses) > 0 else 0.0
    profit_factor = wins.sum() / abs(losses.sum()) if len(losses) > 0 else np.inf

    equity_curve = pnls.cumsum()
    peak = np.maximum.accumulate(equity_curve)
    drawdown = equity_curve - peak
    max_dd = drawdown.min()

    return {
        "num_trades": len(trades),
        "total_pnl": total_pnl,
        "winrate": winrate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "max_drawdown": max_dd,
        "equity_curve": equity_curve
    }

# ============================================================
# ANALISI PER ANNO / MESE / ORA
# ============================================================
def analyze_by_group(trades, group_key):
    df = pd.DataFrame(trades)
    groups = df.groupby(group_key)

    results = []

    for key, g in groups:
        pnls = g["pnl"].values
        wins = pnls[pnls > 0]
        losses = pnls[pnls <= 0]

        profit_factor = wins.sum() / abs(losses.sum()) if len(losses) > 0 else np.inf
        winrate = len(wins) / len(pnls)
        avg_pnl = pnls.mean()

        results.append({
            group_key: key,
            "num_trades": len(pnls),
            "winrate": winrate,
            "profit_factor": profit_factor,
            "avg_pnl": avg_pnl
        })

    return pd.DataFrame(results).sort_values(group_key)

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    model = lgb.Booster(model_file=MODEL_PATH)

    df = pd.read_csv(CSV_TEST)
    df["timestamp_m5"] = pd.to_datetime(df["timestamp_m5"])
    df["year"] = df["timestamp_m5"].dt.year
    df["month"] = df["timestamp_m5"].dt.month
    df["hour"] = df["timestamp_m5"].dt.hour

    X_test = df[FEATURE_COLUMNS].values
    y_pred_prob = model.predict(X_test, num_iteration=model.best_iteration)

    signals = apply_thresholding(y_pred_prob, t_buy=T_BUY, t_sell=T_SELL)

    equity, trades = run_backtest(df, signals)
    stats = analyze_trades(trades)

    print("\n=== BACKTEST RISULTATI ===")
    print("Numero trade:", stats["num_trades"])
    print("PNL totale:", stats["total_pnl"])
    print("Winrate:", stats["winrate"])
    print("Profit factor:", stats["profit_factor"])
    print("Max drawdown:", stats["max_drawdown"])

    print("\n=== ANALISI PER ANNO ===")
    print(analyze_by_group(trades, "entry_year"))

    print("\n=== ANALISI PER MESE ===")
    print(analyze_by_group(trades, "entry_month"))

    print("\n=== ANALISI PER ORA ===")
    print(analyze_by_group(trades, "entry_hour"))
