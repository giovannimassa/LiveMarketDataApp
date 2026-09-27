import pandas as pd
import numpy as np
import lightgbm as lgb

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

print("Loading data...")
df = pd.read_csv(CSV_TEST)
print(f"Data shape: {df.shape}")
print(f"Columns: {len(df.columns)}")

print("Loading models...")
model_long_atr = lgb.Booster(model_file=MODEL_LONG_ATR_PATH)
model_short_atr = lgb.Booster(model_file=MODEL_SHORT_ATR_PATH)
print("Models loaded successfully!")

print("Testing prediction on first row...")
x = df.iloc[0:1][FEATURE_COLUMNS].values
print(f"Input shape: {x.shape}")
p_long = float(model_long_atr.predict(x)[0])
p_short = float(model_short_atr.predict(x)[0])
print(f"Prediction long: {p_long}, short: {p_short}")

print("\nTest completed successfully!")
