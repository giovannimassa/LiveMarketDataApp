import { CircularBuffer } from "../utils/circular-buffer.js";

export class RSI{
    private prev: number | undefined;
    private avgGain: number | undefined;
    private avgLoss: number | undefined;
    private period: number;
    private buffer: CircularBuffer<number>;

    constructor(period: number) {
        this.period = period;
        this.buffer = new CircularBuffer(period + 1);
    }

    next(value: number): number | undefined {
        if (this.prev === undefined) {
            this.prev = value;
            return undefined;
        }

        const change = value - this.prev;
        this.prev = value;

        this.buffer.push(change);

        if (!this.buffer.isFull()) return undefined;

        const arr = this.buffer.toArray() as number[];

        if (this.avgGain === undefined) {
            const gains = arr.filter(x => x > 0);
            const losses = arr.filter(x => x < 0).map(x => -x);

            this.avgGain = gains.reduce((a, b) => a + b, 0) / this.period;
            this.avgLoss = losses.reduce((a, b) => a + b, 0) / this.period;
        } else {
            const gain = change > 0 ? change : 0;
            const loss = change < 0 ? -change : 0;

            this.avgGain = (this.avgGain * (this.period - 1) + gain) / this.period;
            this.avgLoss = (this.avgLoss! * (this.period - 1) + loss) / this.period;
        }

        if (this.avgLoss === 0) return 100;

        const rs = this.avgGain / this.avgLoss;
        const val = 100 - 100 / (1 + rs);
        return val;
    }

    fill(values: number[]) {
        this.buffer = new CircularBuffer(this.period + 1);
        values.forEach(v => {
            this.next(v);
        });
    }
}