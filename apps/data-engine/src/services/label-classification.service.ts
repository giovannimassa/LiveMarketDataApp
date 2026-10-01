import { injectable } from "inversify";
import { MarketItemString } from "../models/marketitem-string.model.js";

@injectable()
export class LabelClassificationService {

    /**
     * Calcola 4 target binari:
     * - targetLong
     * - targetShort
     * - targetLongAtr
     * - targetShortAtr
     */
    generateBinaryTargets(
        candles: MarketItemString[],
        horizon: number = 20, // ≈ 20 minuti su timeframe 5 minuti
        threshold: number = 0.002,   // es: 0.05%
        k: number = 1.0              // ATR multiplier
    ) {
        const n = candles.length;
        const close = candles.map(c => c.closePrice);
        const atr = candles.map(c => c.atr14 ? parseFloat(c.atr14) : null);

        const targetLong: number[] = new Array(n).fill(0);
        const targetShort: number[] = new Array(n).fill(0);
        const targetLongAtr: number[] = new Array(n).fill(0);
        const targetShortAtr: number[] = new Array(n).fill(0);
        const targetLongAtrEma: number[] = new Array(n).fill(0);
        const targetShortAtrEma: number[] = new Array(n).fill(0);

        for (let i = 0; i < n; i++) {
            // fuori range → target = 0
            if (i + horizon >= n) continue;

            const futureReturn = (close[i + horizon] - close[i]) / close[i];

            // -----------------------------
            // RETURN-BASED TARGETS
            // -----------------------------
            targetLong[i] = futureReturn > threshold ? 1 : 0;
            targetShort[i] = futureReturn < -threshold ? 1 : 0;

            const atrValue = atr[i];
            // -----------------------------
            // ATR-ADJUSTED TARGETS
            // -----------------------------
            if (atrValue && atrValue > 0) {
                const moveAtr = (close[i + horizon] - close[i]) / atrValue;

                targetLongAtr[i] = moveAtr > k ? 1 : 0;
                targetShortAtr[i] = moveAtr < -k ? 1 : 0;
            }

            // -----------------------------
            // SLOPE EMA WITH ATR-ADJUSTED TARGETS
            // -----------------------------
            if (atrValue && atrValue > 0) {
                const moveAtr = (close[i + horizon] - close[i]) / atrValue;
                const slopeEma = candles[i].slopeEma;

                if (slopeEma) {
                    const slopeEmaValue = parseFloat(slopeEma);
                    targetLongAtrEma[i] = slopeEmaValue > 0 &&moveAtr > k ? 1 : 0;
                    targetShortAtrEma[i] = slopeEmaValue < 0 && moveAtr < -k ? 1 : 0;
                }
            }
        }

        // Combina tutto in un array di oggetti
        return candles.map((_, i) => ({
            targetLong: targetLong[i],
            targetShort: targetShort[i],
            targetLongAtr: targetLongAtr[i],
            targetShortAtr: targetShortAtr[i],
            targetLongAtrEma: targetLongAtrEma[i],
            targetShortAtrEma: targetShortAtrEma[i]
        }));
    }
}
