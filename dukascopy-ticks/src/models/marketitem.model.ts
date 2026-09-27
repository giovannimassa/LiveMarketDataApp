export interface MarketItem {
  timestamp: string;
  openPrice: number;
  highPrice: number;
  lowPrice: number;
  closePrice: number;
  volume: number;
  sma20: number | undefined;
  sma50: number | undefined;
  ema20: number | undefined;
  ema50: number | undefined;
  ema100: number | undefined;
  ema200: number | undefined;
  bbands20: number | undefined;
  rsi14: number | undefined;
  atr14: number | undefined;
  macdSignal: number | undefined; // Mi serve se devo calcolare il macd a partire da dati già salvati
  macdFast: number | undefined; // Mi serve se devo calcolare il macd a partire da dati già salvati
  macdSlow: number | undefined; // Mi serve se devo calcolare il macd a partire da dati già salvati
  macdNorm: number | undefined;
  slopeEma: number | undefined;
  distanceEma: number | undefined;
  roc: number | undefined;
  stoch: number | undefined;
  obv: number | undefined;
  volumeZScore: number | undefined;
  volumeAtrRatio: number | undefined;
  fvgBullish: number | undefined;
  fvgBearish: number | undefined;
  fvgSize: number | undefined;
  fvgSizeAtrNorm: number | undefined;
  bodySizePerc: number | undefined;
  upperWickPerc: number | undefined;
  lowerWickPerc: number | undefined;
  rangeExp: number | undefined;
  logReturn: number | undefined;
  rollingVolatility: number | undefined;
  rollingVolatilityAtrNorm: number | undefined;
  rollingVolatilitySlope: number | undefined;
}