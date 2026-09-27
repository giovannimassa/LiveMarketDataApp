import { Candle } from "../services/marketdata.service.js";

export class LowerWickPercentage {
    next(candle: Candle): number {
        const range = candle.highPrice - candle.lowPrice || 1e-9;
        const lower = Math.min(candle.openPrice, candle.closePrice) - candle.lowPrice;
        const val = (lower / range) * 100;
        return val;
    }
}