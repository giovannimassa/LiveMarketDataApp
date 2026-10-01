import { EMA } from "./ema.js";

export interface MACDResult {
    fast: number;
    slow: number;
    macd: number;
    signal: number;
    histogram: number;
}

export class MACD {
    private fastPeriod: number;
    private slowPeriod: number;
    private signalPeriod: number;
    private fast: EMA;
    private slow: EMA;
    private signal: EMA;
    private macdValue: number | undefined;

    constructor(fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
        this.fastPeriod = fastPeriod;
        this.slowPeriod = slowPeriod;
        this.signalPeriod = signalPeriod;
        this.fast = new EMA(this.fastPeriod);
        this.slow = new EMA(this.slowPeriod);
        this.signal = new EMA(this.signalPeriod);
    }

    next(price: number): MACDResult | undefined {
        const fast = this.fast.next(price);
        const slow = this.slow.next(price);

        if (fast === undefined || slow === undefined) return undefined;

        this.macdValue = fast - slow;
        const signal = this.signal.next(this.macdValue);

        if (signal === undefined) return undefined;

        return {
            fast: fast,
            slow: slow,
            macd: this.macdValue,
            signal: signal,
            histogram: this.macdValue - signal
        };
    }

    getCurrent(): number | undefined {
        throw new Error("Method not implemented.");
    }

    fill(values: number[], lastFastEma?: number, lastSlowEma?: number, lastSignalEma?: number) {
        this.fast = new EMA(this.fastPeriod, lastFastEma);
        this.slow = new EMA(this.slowPeriod, lastSlowEma);
        this.signal = new EMA(this.signalPeriod, lastSignalEma);

        values.forEach(v => {
            this.next(v);
        });
    }
}

export class MacdAtrNormalized {
    next(macdHistogram: number | undefined, atr: number | undefined): number | undefined {

        if (macdHistogram === undefined || atr === undefined || atr === 0) return 0;
        const val = macdHistogram / atr;
        return val;
    }
}