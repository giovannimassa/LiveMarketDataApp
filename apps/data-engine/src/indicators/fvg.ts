import { Candle } from "../services/marketdata.service.js";
import { CircularBuffer } from "../utils/circular-buffer.js";

export interface FVGResult {
    isBullish: boolean;
    isBearish: boolean;
    size: number;
}

export class FVG {
    private fvgCandles: number = 3;
    private buffer: CircularBuffer<Candle>;

    constructor() {
        this.buffer = new CircularBuffer<Candle>(this.fvgCandles);
    }

    next(candle: Candle): FVGResult | undefined {
        this.buffer.push(candle);
        if (!this.buffer.isFull()) return undefined;

        const [c1, c2, c3] = this.buffer.toArray() as Candle[];

        const bullishGap = c1.highPrice < c3.lowPrice;
        const bearishGap = c1.lowPrice > c3.highPrice;

        if (!bullishGap && !bearishGap) {
            return { isBullish: false, isBearish: false, size: 0 };
        }

        const size = bullishGap
            ? c3.lowPrice - c1.highPrice
            : c1.lowPrice - c3.highPrice;

        return {
            isBullish: bullishGap,
            isBearish: bearishGap,
            size: Math.abs(size)
        };
    }

    getValues(): (Candle | undefined)[] {
        return this.buffer.toArray();
    }

    fill(values: Candle[]) {
        this.buffer = new CircularBuffer(this.fvgCandles);
        values.forEach(v => {
            this.next(v);
        });
    }
}

export class FvgSizeNormalized {

    next(fvgSize: number | undefined, atr: number | undefined): number | undefined {

        if (fvgSize === undefined || atr === undefined || atr === 0) return 0;
        return fvgSize / atr;
    }
}