import { CircularBuffer } from "../utils/circular-buffer.js";

export class ROC {
    private period: number;
    private buffer: CircularBuffer<number>;
    
    constructor(period: number) {
        this.period = period;
        this.buffer = new CircularBuffer<number>(period + 1);
    }

    next(price: number): number | undefined {
        this.buffer.push(price);
        if (this.buffer.length() < this.period + 1) return undefined;

        const arr = this.buffer.toArray() as number[];
        const priceN = arr[0]; // prezzo di N periodi fa
        if (priceN === 0) return undefined;

        const val = ((price - priceN) / priceN) * 100;
        return val;
    }

    getPeriod(): number {
        return this.period;
    }

    getValues(): (number | undefined)[] {
        return this.buffer.toArray();
    }

    fill(values: number[]) {
        this.buffer = new CircularBuffer(this.period + 1);
        values.forEach(v => {
            this.next(v);
        });
    }
}