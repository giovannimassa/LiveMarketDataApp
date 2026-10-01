import { CircularBuffer } from "../utils/circular-buffer.js";
import { Candle } from "../services/marketdata.service.js";

export class ATR {
    private period: number;
    private buffer: CircularBuffer<number>;
    private prevClose: number | undefined;
    private atr: number | undefined;

    constructor(period: number) {
        this.period = period;
        this.buffer = new CircularBuffer<number>(period);
    }

    next(candle: Candle): number | undefined {
        const { highPrice, lowPrice, closePrice } = candle;

        let tr: number;
        if (this.prevClose === undefined) {
            tr = highPrice - lowPrice;
        } else {
            tr = Math.max(
                highPrice - lowPrice,
                Math.abs(highPrice - this.prevClose),
                Math.abs(lowPrice - this.prevClose)
            );
        }

        this.prevClose = closePrice;

        if (!this.buffer.isFull() && this.atr === undefined) {
            this.buffer.push(tr);
            if (!this.buffer.isFull()) return undefined;

            const arr = this.buffer.toArray() as number[];
            this.atr = arr.reduce((a, b) => a + b, 0) / this.period;
        } else {
            this.atr = ((this.atr as number) * (this.period - 1) + tr) / this.period;
        }

        const val = this.atr;
        return val;
    }

    getPeriod(): number {
        return this.period;
    }

    getValues(): (number | undefined)[] {
        return this.buffer.toArray();
    }

    fill(values: Candle[], lastAtr: number | undefined, prevClose: number) {
        this.atr = lastAtr;
        this.prevClose = prevClose;
        this.buffer = new CircularBuffer(this.period);
        values.forEach(v => {
            this.next(v);
        });
    }
}