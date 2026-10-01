import { Candle } from "../services/marketdata.service.js";

export class RangeExpansion {
    private prevRange: number | undefined;

    private setRange(candle: Candle) {
        return candle.highPrice - candle.lowPrice;
    }

    next(candle: Candle): number | undefined {
        const range = this.setRange(candle);

        if (this.prevRange === undefined || this.prevRange === 0) {
            this.prevRange = range;
            return undefined;
        }

        const expansion = ((range - this.prevRange) / this.prevRange) * 100;
        this.prevRange = range;
        return expansion;
    }

    fill(values: Candle[], prevCandle: Candle) {
        this.prevRange = this.setRange(prevCandle);
        values.forEach(v => {
            this.next(v);
        });
    }
}