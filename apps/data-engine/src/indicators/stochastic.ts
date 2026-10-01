import { Candle } from "../services/marketdata.service.js";
import { CircularBuffer } from "../utils/circular-buffer.js";

export interface StochResult {
    k: number;
    d: number;
}

export class Stochastic {
    private period: number;
    private smoothK: number;
    private smoothD: number;
    private buffer: CircularBuffer<Candle>;
    private kBuffer: CircularBuffer<number>;

    constructor(period = 14, smoothK = 3, smoothD = 3) {
        this.period = period;
        this.smoothK = smoothK;
        this.smoothD = smoothD;
        this.buffer = new CircularBuffer<Candle>(period);
        this.kBuffer = new CircularBuffer<number>(smoothK);
    }

    next(candle: Candle): StochResult | undefined {
        this.buffer.push(candle);
        if (!this.buffer.isFull()) return undefined;

        const arr = this.buffer.toArray() as Candle[];
        const highs = arr.map(c => c.highPrice);
        const lows = arr.map(c => c.lowPrice);

        const highest = Math.max(...highs);
        const lowest = Math.min(...lows);

        if (highest === lowest) return undefined;

        const kRaw = ((candle.closePrice - lowest) / (highest - lowest)) * 100;

        this.kBuffer.push(kRaw);
        if (!this.kBuffer.isFull()) return undefined;

        const kArr = this.kBuffer.toArray() as number[];
        const k = kArr.reduce((a, b) => a + b, 0) / this.smoothK;

        // D = SMA di K
        const dArr = kArr.slice(-this.smoothD);
        const d = dArr.reduce((a, b) => a + b, 0) / dArr.length;

        return {
            k: k,
            d: d
        };
    }

    getPeriod(): number {
        return this.period;
    }

    getValues(): Candle[] {
        return this.buffer.toArray() as Candle[];
    }

    fill(candles: Candle[]) {
        this.buffer = new CircularBuffer<Candle>(this.period);
        this.kBuffer = new CircularBuffer<number>(this.smoothK);
        candles.forEach(c => {
            this.next(c);
        });
    }
}