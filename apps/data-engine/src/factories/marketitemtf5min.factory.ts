import { MarketItem } from "../models/marketitem.model.js";

export class MarketItemFactory {
    static createFromMarketItem(timestamp: string, openPrice: number, highPrice: number, lowPrice: number, closePrice: number, volume: number): MarketItem {
        return {
            timestamp: timestamp,
            openPrice: openPrice,
            highPrice: highPrice,
            lowPrice: lowPrice,
            closePrice: closePrice,
            volume: volume,
            sma20: undefined,
            sma50: undefined,
            ema20: undefined,
            ema50: undefined,
            ema100: undefined,
            ema200: undefined,
            bbands20: undefined,
            rsi14: undefined,
            atr14: undefined,
            macdSignal: undefined,
            macdFast: undefined,
            macdSlow: undefined,
            macdNorm: undefined,
            slopeEma: undefined,
            distanceEma: undefined,
            roc: undefined,
            stoch: undefined,
            obv: undefined,
            volumeZScore: undefined,
            volumeAtrRatio: undefined,
            fvgBullish: undefined,
            fvgBearish: undefined,
            fvgSize: undefined,
            fvgSizeAtrNorm: undefined,
            bodySizePerc: undefined,
            upperWickPerc: undefined,
            lowerWickPerc: undefined,
            rangeExp: undefined,
            logReturn: undefined,
            rollingVolatility: undefined,
            rollingVolatilityAtrNorm: undefined,
            rollingVolatilitySlope: undefined
        };
    }
}