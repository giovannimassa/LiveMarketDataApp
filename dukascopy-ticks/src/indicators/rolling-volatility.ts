import { CircularBuffer } from "../utils/circular-buffer.js";

export class RollingVolatility {
    private period: number;
    private buffer: CircularBuffer<number>;

    constructor(period: number) {
        this.period = period;
        this.buffer = new CircularBuffer<number>(period);
    }

    next(logReturn: number | undefined): number | undefined {
        this.buffer.push(logReturn ?? 0);
        if (!this.buffer.isFull()) return undefined;

        const arr = this.buffer.toArray() as number[];
        const mean = arr.reduce((a, b) => a + b, 0) / this.period;
        const variance = arr.reduce((s, v) => s + (v - mean) ** 2, 0) / this.period;
        const val = Math.sqrt(variance);
        return val;
    }

    fill(values: number[]) {
        this.buffer = new CircularBuffer(this.period);
        values.forEach(v => {
            this.next(v);
        });
    }
}