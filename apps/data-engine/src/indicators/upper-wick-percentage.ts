import { Candle } from "../services/marketdata.service.js";

export class UpperWickPercentage {
    next(candle: Candle): number {
        const range = candle.highPrice - candle.lowPrice || 1e-9;
        const upper = candle.highPrice - Math.max(candle.openPrice, candle.closePrice);
        const val = (upper / range) * 100;
        return val;
    }
}