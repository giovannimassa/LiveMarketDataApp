export class LogReturn {
    private prevClose: number | undefined;

    next(close: number): number | undefined {
        if (this.prevClose === undefined) {
            this.prevClose = close;
            return undefined;
        }

        const ret = Math.log(close / this.prevClose);
        this.prevClose = close;
        return ret;
    }

    fill(values: number[], prevClose: number) {
        this.prevClose = prevClose;
        values.forEach(v => {
            this.next(v);
        });
    }
}