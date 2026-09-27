import { EMA } from "./ema.js";

export class DistanceEMA {
    private period: number;
    private ema: EMA;

    constructor(period: number) {
        this.period = period;
        this.ema = new EMA(period);
    }

    next(price: number): number | undefined {
        const emaVal = this.ema.next(price);
        if (emaVal === undefined) return undefined;
        const val = price - emaVal;
        return val;
    }
    
    fill(values: number[], lastEma: number | undefined) {

        this.ema = new EMA(this.period);
        this.ema.fill(values, lastEma);
    }
}