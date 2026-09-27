import pandas as pd
import numpy as np
import lightgbm as lgb
import time

# ============================================================
# CONFIG
# ============================================================
CSV_TEST = "eurusd_test.csv"

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

# Threshold ottimali trovati nei test
T_LONG_ATR = 0.20
T_SHORT_ATR = 0.20

# Parametri backtest
N_MAX_BARS = 24
ATR_SL_MULT = 1.0
ATR_TP_MULT = 2.0

# ============================================================
# CARICAMENTO MODELLI
# ============================================================
model_long_atr = lgb.Booster(model_file=MODEL_LONG_ATR_PATH)
model_short_atr = lgb.Booster(model_file=MODEL_SHORT_ATR_PATH)

# ============================================================
# ENSEMBLE ATR‑ONLY
# ============================================================
def ensemble_atr_signal(x_row):
    pLongAtr = float(model_long_atr.predict(x_row)[0])
    pShortAtr = float(model_short_atr.predict(x_row)[0])

    long_signal = pLongAtr > T_LONG_ATR
    short_signal = pShortAtr > T_SHORT_ATR

    # BUY
    if long_signal and not short_signal:
        return 1, pLongAtr, pShortAtr

    # SELL
    if short_signal and not long_signal:
        return -1, pLongAtr, pShortAtr

    # Conflitto → vince il più forte
    if long_signal and short_signal:
        if pLongAtr > pShortAtr:
            return 1, pLongAtr, pShortAtr
        else:
            return -1, pLongAtr, pShortAtr

    # HOLD
    return 0, pLongAtr, pShortAtr

# ============================================================
# BACKTEST ENGINE (OTTIMIZZATO)
# ============================================================
def run_backtest(df):
    equity = 0.0
    trades = []

    prices = df["close_m5"].values
    atr = df["atr14_m5"].values
    highs = df["high_m5"].values
    lows = df["low_m5"].values

    i = 0
    n = len(df)

    while i < n:
        x = df.iloc[i:i+1][FEATURE_COLUMNS].values
        signal, pLongAtr, pShortAtr = ensemble_atr_signal(x)

        if signal == 0:
            i += 1
            continue

        entry_price = prices[i]
        atr_val = atr[i]
        sl = ATR_SL_MULT * atr_val
        tp = ATR_TP_MULT * atr_val

        direction = signal
        entry_index = i

        exit_price = None
        exit_reason = None
        exit_index = i + 1

        # Ricerca efficiente dell'exit usando vettorizzazione
        j = i + 1
        max_j = min(i + N_MAX_BARS + 1, n)
        
        if direction == 1:  # BUY
            high_slice = highs[j:max_j]
            low_slice = lows[j:max_j]
            
            # TP hit
            tp_hits = np.where(high_slice >= entry_price + tp)[0]
            if len(tp_hits) > 0:
                exit_index = j + tp_hits[0]
                exit_price = entry_price + tp
                exit_reason = "TP"
            else:
                # SL hit
                sl_hits = np.where(low_slice <= entry_price - sl)[0]
                if len(sl_hits) > 0:
                    exit_index = j + sl_hits[0]
                    exit_price = entry_price - sl
                    exit_reason = "SL"
                else:
                    exit_index = max_j - 1
                    exit_price = prices[min(max_j - 1, n - 1)]
                    exit_reason = "TIME"
        else:  # SELL
            high_slice = highs[j:max_j]
            low_slice = lows[j:max_j]
            
            # TP hit
            tp_hits = np.where(low_slice <= entry_price - tp)[0]
            if len(tp_hits) > 0:
                exit_index = j + tp_hits[0]
                exit_price = entry_price - tp
                exit_reason = "TP"
            else:
                # SL hit
                sl_hits = np.where(high_slice >= entry_price + sl)[0]
                if len(sl_hits) > 0:
                    exit_index = j + sl_hits[0]
                    exit_price = entry_price + sl
                    exit_reason = "SL"
                else:
                    exit_index = max_j - 1
                    exit_price = prices[min(max_j - 1, n - 1)]
                    exit_reason = "TIME"

        pnl = exit_price - entry_price if direction == 1 else entry_price - exit_price
        equity += pnl

        exit_idx = min(exit_index, n - 1)

        trades.append({
            "entry_index": entry_index,
            "exit_index": exit_idx,
            "direction": direction,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "reason": exit_reason,
            "entry_time": df["timestamp_m5"].iloc[entry_index],
            "exit_time": df["timestamp_m5"].iloc[exit_idx],
            "entry_year": df["year"].iloc[entry_index],
            "entry_month": df["month"].iloc[entry_index],
            "entry_hour": df["hour"].iloc[entry_index],
            "pLongAtr": pLongAtr,
            "pShortAtr": pShortAtr
        })

        i = exit_idx + 1

    return equity, trades

# ============================================================
# ANALISI TRADE
# ============================================================
def analyze_trades(trades):
    pnls = np.array([t["pnl"] for t in trades])
    wins = pnls[pnls > 0]
    losses = pnls[pnls <= 0]

    total_pnl = pnls.sum()
    winrate = len(wins) / len(trades) if len(trades) > 0 else 0
    avg_win = wins.mean() if len(wins) else 0
    avg_loss = losses.mean() if len(losses) else 0
    profit_factor = wins.sum() / abs(losses.sum()) if len(losses) and losses.sum() != 0 else np.inf

    equity_curve = pnls.cumsum()
    peak = np.maximum.accumulate(equity_curve)
    drawdown = equity_curve - peak
    max_dd = drawdown.min() if len(drawdown) > 0 else 0

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
def analyze_by_group(trades, key):
    df = pd.DataFrame(trades)
    groups = df.groupby(key)

    rows = []
    for k, g in groups:
        pnls = g["pnl"].values
        wins = pnls[pnls > 0]
        losses = pnls[pnls <= 0]

        profit_factor = wins.sum() / abs(losses.sum()) if len(losses) and losses.sum() != 0 else np.inf
        winrate = len(wins) / len(pnls)
        avg_pnl = pnls.mean()

        rows.append({
            key: k,
            "num_trades": len(pnls),
            "winrate": winrate,
            "profit_factor": profit_factor,
            "avg_pnl": avg_pnl
        })

    return pd.DataFrame(rows).sort_values(key)

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    start_time = time.time()
    
    print("Loading data...")
    df = pd.read_csv(CSV_TEST)
    df["timestamp_m5"] = pd.to_datetime(df["timestamp_m5"])
    df["year"] = df["timestamp_m5"].dt.year
    df["month"] = df["timestamp_m5"].dt.month
    df["hour"] = df["timestamp_m5"].dt.hour

    print(f"Data loaded: {len(df)} rows")
    print("Running backtest...")
    equity, trades = run_backtest(df)
    print(f"Backtest completed: {len(trades)} trades")
    
    stats = analyze_trades(trades)

    print("\n=== RISULTATI BACKTEST ENSEMBLE ATR ===")
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
    
    # Calcolo del tempo totale
    end_time = time.time()
    elapsed_seconds = int(end_time - start_time)
    minutes = elapsed_seconds // 60
    seconds = elapsed_seconds % 60
    print(f"\n⏱️  Tempo totale di esecuzione: {minutes}m {seconds}s")