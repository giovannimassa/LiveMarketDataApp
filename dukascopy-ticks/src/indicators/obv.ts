import { Candle } from "../services/marketdata.service.js";

export class OBV {
    private prevClose: number | undefined;
    private obv: number | undefined;

    next(candle: Candle): number | undefined {
        if (this.prevClose === undefined) {
            this.prevClose = candle.closePrice;
            if (this.obv === undefined) {
                this.obv = 0;
            }
            return this.obv;
        }

        if (candle.closePrice > this.prevClose) {
            if (this.obv === undefined) {
                this.obv = 0;
            }
            this.obv += candle.volume;
        }
        else if (candle.closePrice < this.prevClose) {
            if (this.obv === undefined) {
                this.obv = 0;
            }
            this.obv -= candle.volume;
        }

        this.prevClose = candle.closePrice;
        if (this.obv === undefined) {
            this.obv = 0;
        }

        return this.obv;
    }

    fill(values: Candle[], lastObv: number | undefined, prevClose: number) {
        this.obv = lastObv;
        this.prevClose = prevClose;
        values.forEach(v => {
            this.next(v);
        });
    }
}