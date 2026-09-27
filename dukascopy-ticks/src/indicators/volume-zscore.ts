import { Candle } from "../services/marketdata.service.js";
import { CircularBuffer } from "../utils/circular-buffer.js";

export class VolumeZScore {
    private period: number;
    private buffer: CircularBuffer<number>;

    constructor(period: number) {
        this.period = period;
        this.buffer = new CircularBuffer<number>(period);
    }

    next(candle: Candle): number | undefined {
        this.buffer.push(candle.volume);
        if (!this.buffer.isFull()) return undefined;

        const arr = this.buffer.toArray() as number[];
        const mean = arr.reduce((a, b) => a + b, 0) / this.period;
        const variance = arr.reduce((s, v) => s + (v - mean) ** 2, 0) / this.period;
        const std = Math.sqrt(variance);
        if (std === 0) return 0;

        const val = (candle.volume - mean) / std;
        return val;
    }

    fill(candles: Candle[]) {
        this.buffer = new CircularBuffer<number>(this.period);
        candles.forEach(c => {
            this.next(c);
        });
    }
}