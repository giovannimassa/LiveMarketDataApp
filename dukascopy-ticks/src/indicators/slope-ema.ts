import { Candle } from "../services/marketdata.service.js";
import { CircularBuffer } from "../utils/circular-buffer.js";
import { EMA } from "./ema.js";

export class SlopeEMA {
    private emaPeriod: number;
    private ema: EMA;
    private buffer: CircularBuffer<number>;
    private window: number;

    constructor(emaPeriod: number, window: number) {
        this.emaPeriod = emaPeriod;
        this.ema = new EMA(emaPeriod);
        this.window = window;
        this.buffer = new CircularBuffer<number>(window);
    }

    next(price: number): number | undefined {
        const emaVal = this.ema.next(price);
        if (emaVal === undefined) return undefined;

        this.buffer.push(emaVal);
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

    fill(candles: Candle[], lastEma: number | undefined) {
        this.ema = new EMA(this.emaPeriod, lastEma);
        this.buffer = new CircularBuffer<number>(this.window);
        candles.forEach(c => {
            this.next(c.closePrice);
        });
    }
}