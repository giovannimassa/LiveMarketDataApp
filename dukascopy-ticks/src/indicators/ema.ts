import { CircularBuffer } from "../utils/circular-buffer.js";

export class EMA {
    private buffer: CircularBuffer<number | undefined>;
    private period: number;
    private k: number;
    private ema: number | undefined;

    constructor(period: number, lastEma?: number) {
        this.period = period;
        this.buffer = new CircularBuffer(period);
        this.k = 2 / (period + 1);
        this.ema = lastEma;
    }

    next(value: number): number | undefined {
        let val = undefined;
        if (!this.buffer.isFull()) {
            this.buffer.push(value);

            if (this.buffer.isFull()) {
                // SMA iniziale
                const arr = this.buffer.toArray() as number[];
                this.ema = arr.reduce((a, b) => a + b, 0) / this.period;
                val = this.ema;
            }

            return undefined;
        }

        // EMA incrementale
        this.ema = value * this.k + (this.ema as number) * (1 - this.k);
        const valEma = this.ema;
        return valEma;
    }

    getCurrent(): number | undefined {
        throw new Error("Method not implemented.");
    }

    getPeriod(): number {
        return this.period;
    }

    getValues(): (number | undefined)[] {
        return this.buffer.toArray();
    }

    fill(values: number[], lastEma?: number) {
        this.ema = lastEma;
        this.buffer = new CircularBuffer<number>(this.period);
        values.forEach((v, i) => {
            this.next(v);
        });
    }
}