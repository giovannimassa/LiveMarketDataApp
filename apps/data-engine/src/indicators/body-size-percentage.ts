import { Candle } from "../services/marketdata.service.js";

export class BodySizePercentage {
    next(candle: Candle): number {
        const range = candle.highPrice - candle.lowPrice || 1e-9;
        const body = Math.abs(candle.closePrice - candle.openPrice);
        const val = (body / range) * 100;
        return val;
    }
}