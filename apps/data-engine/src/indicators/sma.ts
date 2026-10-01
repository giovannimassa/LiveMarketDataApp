import { CircularBuffer } from "../utils/circular-buffer.js";

export class Sma {
    private buffer: CircularBuffer<number | undefined>;
    private sum: number;
    private period: number;

    constructor(period: number) {
        this.sum = 0;
        this.period = period;
        this.buffer = new CircularBuffer(period);
    }

    /**
     * Aggiorna l'SMA con un nuovo valore.
     * Restituisce:
     *  - undefined finché non ci sono abbastanza valori
     *  - il valore SMA quando il buffer è pieno
     */
    next(value: number): number | undefined {
        if (this.buffer.isFull()) {
            // Rimuovi il valore più vecchio dalla somma
            const old = this.buffer.pop();
            if (old !== null && old !== undefined) {
                this.sum -= old;
            }
        }

        // Aggiungi il nuovo valore
        this.buffer.push(value);
        this.sum += value;

        // Se non abbiamo ancora abbastanza valori → SMA non disponibile
        if (!this.buffer.isFull()) {
            return undefined;
        }

        // SMA = somma / period
        const val = this.sum / this.period;
        return val;
    }

    /**
     * Restituisce l'ultima SMA calcolata (se disponibile)
     */
    getCurrent(): number | undefined {
        if (!this.buffer.isFull()) return undefined;
        return this.sum / this.period;
    }

    /**
     * Restituisce il valore del periodo
     */
    getPeriod(): number {
        return this.period;
    }

    /**
     * Restituisce i valori attualmente nel buffer (debug)
     */
    getValues(): (number | undefined)[] {
        return this.buffer.toArray();
    }

    fill(values: number[]) {
        this.sum = 0;
        this.buffer = new CircularBuffer(this.period);
        values.forEach(v => {
            this.next(v);
        });
    }
}