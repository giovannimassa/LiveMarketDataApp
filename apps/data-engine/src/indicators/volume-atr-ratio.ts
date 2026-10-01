import { Candle } from "../services/marketdata.service.js";

export class VolumeAtrRatio {

    /**
     * Calcola il Volume ATR Ratio in modo incrementale
     * @param candle candela OHLCV
     * @returns numero oppure undefined se ATR non è ancora disponibile
     */
    next(candle: Candle, atr: number | undefined): number | undefined {

        if (atr === undefined || atr === 0) {
            return undefined;
        }

        const val = candle.volume / atr;
        return val;
    }
}