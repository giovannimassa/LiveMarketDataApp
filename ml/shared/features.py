import os
import numpy as np
import pandas as pd

TIMEFRAMES = ["m5", "m15", "h1"]

# slopeEmaAtr e distanceEmaAtr sono derivate da add_derived_features
TIMEFRAME_FEATURES = [
    "rsi14", "atr14", "macdNorm", "slopeEmaAtr", "distanceEmaAtr", "roc", "stoch",
    "volumeZScore", "volumeAtrRatio", "fvgBullish", "fvgBearish", "fvgSizeAtrNorm",
    "bodySizePerc", "upperWickPerc", "lowerWickPerc", "rangeExp", "logReturn",
    "rollingVolatility", "rollingVolatilityAtrNorm", "rollingVolatilitySlope",
]

TIME_FEATURES = ["hour_sin", "hour_cos", "dayOfWeek", "sessionLondon", "sessionNY"]

FEATURE_COLUMNS = [f"{name}_{tf}" for tf in TIMEFRAMES for name in TIMEFRAME_FEATURES] + TIME_FEATURES

# Elenco dei modelli addestrati prima della revisione delle feature
FEATURE_COLUMNS_LEGACY = [
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

# Registro degli elenchi di feature selezionabili da CLI/env (vedi get_feature_columns)
FEATURE_SETS = {
    "new": FEATURE_COLUMNS,
    "legacy": FEATURE_COLUMNS_LEGACY,
}


def get_feature_columns(name: str | None = None) -> list:
    """Risolve l'elenco feature da usare: argomento esplicito, poi env FEATURE_SET, poi 'new'."""
    name = name or os.environ.get("FEATURE_SET", "new")
    if name not in FEATURE_SETS:
        raise ValueError(f"FEATURE_SET sconosciuto: {name!r}. Valori validi: {list(FEATURE_SETS)}")
    return FEATURE_SETS[name]


def model_suffix(name: str | None = None) -> str:
    """Suffisso per i file modello: vuoto per il set 'new', altrimenti '_<nome>'."""
    name = name or os.environ.get("FEATURE_SET", "new")
    return "" if name == "new" else f"_{name}"


def add_true_atr(df: pd.DataFrame, period: int = 14, tf: str = "m5") -> pd.DataFrame:
    """Aggiunge atr_true_<tf>: ATR di Wilder ricalcolato dagli OHLC, perche' atr14 nel dataset e' gonfiato."""
    df = df.copy()
    prev_close = df[f"close_{tf}"].shift(1)
    tr = np.maximum(
        df[f"high_{tf}"] - df[f"low_{tf}"],
        np.maximum((df[f"high_{tf}"] - prev_close).abs(), (df[f"low_{tf}"] - prev_close).abs()),
    )
    tr.iloc[0] = df[f"high_{tf}"].iloc[0] - df[f"low_{tf}"].iloc[0]
    df[f"atr_true_{tf}"] = tr.ewm(alpha=1 / period, adjust=False).mean()
    return df


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Nel DB le colonne sono TEXT, serve la conversione numerica
    for tf in TIMEFRAMES:
        for name in ("atr14", "slopeEma", "distanceEma"):
            df[f"{name}_{tf}"] = pd.to_numeric(df[f"{name}_{tf}"], errors="coerce")

        atr = df[f"atr14_{tf}"].replace(0, np.nan)
        df[f"slopeEmaAtr_{tf}"] = df[f"slopeEma_{tf}"] / atr
        df[f"distanceEmaAtr_{tf}"] = df[f"distanceEma_{tf}"] / atr

    ts = pd.to_datetime(df["timestamp_m5"], utc=True)
    hour = ts.dt.hour + ts.dt.minute / 60
    df["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    df["dayOfWeek"] = ts.dt.dayofweek
    # Orari UTC approssimati, senza correzione per l'ora legale
    df["sessionLondon"] = ((ts.dt.hour >= 7) & (ts.dt.hour < 16)).astype(int)
    df["sessionNY"] = ((ts.dt.hour >= 12) & (ts.dt.hour < 21)).astype(int)

    return df