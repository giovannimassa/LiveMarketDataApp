import { CircularBuffer } from "../utils/circular-buffer.js";

export class BollingerBands {
    private stdDev: number;
    private period: number;
    private buffer: CircularBuffer<number>;

    constructor(period: number, stdDev = 2) {
        this.period = period;
        this.buffer = new CircularBuffer(period);
        this.stdDev = stdDev;
    }

    next(value: number) {
        this.buffer.push(value);

        if (!this.buffer.isFull()) return undefined;

        const arr = this.buffer.toArray() as number[];
        const mean = arr.reduce((a, b) => a + b, 0) / this.period;
        const variance = arr.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / this.period;
        const std = Math.sqrt(variance);
        
        return {
            upper: mean + this.stdDev * std,
            middle: mean,
            lower: mean - this.stdDev * std
        };
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

    fill(values: number[]) {

        this.buffer = new CircularBuffer(this.period);
        values.forEach(v => {
            this.next(v);
        });
    }
}