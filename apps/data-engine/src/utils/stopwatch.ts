export class Stopwatch {
    private _startTime: bigint;
    private _elapsed: bigint;
    private _running: boolean;
    
    constructor() {
        this._startTime = 0n;   // Tempo di avvio in nanosecondi
        this._elapsed = 0n;     // Tempo accumulato in nanosecondi
        this._running = false;  // Stato
    }

    // Avvia o riprende il cronometro
    start() {
        if (!this._running) {
            this._startTime = process.hrtime.bigint();
            this._running = true;
        }
    }

    // Ferma il cronometro e accumula il tempo
    stop() {
        if (this._running) {
            const now = process.hrtime.bigint();
            this._elapsed += now - this._startTime;
            this._running = false;
        }
    }

    // Resetta il cronometro
    reset() {
        this._elapsed = 0n;
        this._startTime = 0n;
        this._running = false;
    }

    // Tempo totale in millisecondi
    elapsedMilliseconds() {
        let total = this._elapsed;
        if (this._running) {
            total += process.hrtime.bigint() - this._startTime;
        }
        return Number(total) / 1_000_000; // ns → ms
    }

    // Tempo totale in secondi
    elapsedSeconds() {
        return this.elapsedMilliseconds() / 1000;
    }

    // Restituisce il tempo formattato hh:mm:ss.SSS
    formatted() {
        const totalMs = this.elapsedMilliseconds();
        const hours = Math.floor(totalMs / 3600000);
        const minutes = Math.floor((totalMs % 3600000) / 60000);
        const seconds = Math.floor((totalMs % 60000) / 1000);
        const milliseconds = Math.floor(totalMs % 1000);

        // Formattazione con zeri iniziali
        const hh = String(hours).padStart(2, '0');
        const mm = String(minutes).padStart(2, '0');
        const ss = String(seconds).padStart(2, '0');
        const ms = String(milliseconds).padStart(3, '0');

        return `${hh}:${mm}:${ss}.${ms}`;
    }

    // Stato
    isRunning() {
        return this._running;
    }
}