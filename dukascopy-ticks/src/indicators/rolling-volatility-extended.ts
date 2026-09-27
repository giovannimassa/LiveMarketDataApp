import { RollingVolatility } from "./rolling-volatility.js";
import { ATR } from "./atr.js";
import { Candle } from "../services/marketdata.service.js";
import { CircularBuffer } from "../utils/circular-buffer.js";

export class RollingVolatilityAtrNormalized {
    private volPeriod: number;
    private atrPeriod: number;
    private volatility: RollingVolatility;
    private atr: ATR;

    constructor(volPeriod: number, atrPeriod: number) {
        this.volPeriod = volPeriod;
        this.atrPeriod = atrPeriod;
        this.volatility = new RollingVolatility(volPeriod);
        this.atr = new ATR(atrPeriod);
    }

    next(candle: Candle, logReturn: number | undefined): number | undefined {
        const v = this.volatility.next(logReturn);
        const a = this.atr.next(candle);
        if (v === undefined || a === undefined || a === 0) return undefined;
        const val = v / a;
        return val;
    }

    fill(candles: Candle[], closePrices: number[], lastAtr: number | undefined, prevClose: number) {
        this.atr = new ATR(this.atrPeriod);
        this.volatility = new RollingVolatility(this.volPeriod);

        this.atr.fill(candles, lastAtr, prevClose);
        this.volatility.fill(closePrices);
    }
}

export class RollingVolatilitySlope {
    private volPeriod: number;
    private slopeWindow: number;
    private volatility: RollingVolatility;
    private buffer: CircularBuffer<number>;

    constructor(volPeriod: number, slopeWindow: number) {
        this.volPeriod = volPeriod;
        this.slopeWindow = slopeWindow;
        this.volatility = new RollingVolatility(volPeriod);
        this.buffer = new CircularBuffer<number>(slopeWindow);
    }

    next(logReturn: number | undefined): number | undefined {
        const v = this.volatility.next(logReturn);
        if (v === undefined) return undefined;

        this.buffer.push(v);
        if (!this.buffer.isFull()) return undefined;

        const arr = this.buffer.toArray() as number[];
        const n = arr.length;
        const xMean = (n - 1) / 2;
        const yMean = arr.reduce((a, b) => a + b, 0) / n;

        let num = 0;
        let den = 0;
        for (let i = 0; i < n; i++) {
            num += (i - xMean) * (arr[i] - yMean);
            den += (i - xMean) ** 2;
        }

        if (den === 0) return 0;
        const val = num / den;
        return val;
    }

    fill(values: number[]) {
        this.volatility = new RollingVolatility(this.volPeriod);
        this.buffer = new CircularBuffer<number>(this.slopeWindow);

        values.forEach(v => {
            this.next(v);
        });
    }
}