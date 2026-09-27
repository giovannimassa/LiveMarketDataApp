var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
import { Format, getRealTimeRates, Instrument, Timeframe } from "dukascopy-node";
import { injectable } from "inversify";
let MarketDataService = class MarketDataService {
    async getHistoricalData(pair, timeframe) {
        return "";
    }
    async getLiveData(pair, timeframe, numberOfCandles) {
        const data = await getRealTimeRates({
            instrument: this.parseInstrument(pair),
            timeframe: this.parseTimeframe(timeframe),
            format: Format.json,
            last: numberOfCandles
        });
        return data.map(item => [
            item.timestamp,
            item.open,
            item.high,
            item.low,
            item.close,
            item.volume
        ]);
    }
    parseInstrument(pair) {
        if (Object.values(Instrument).includes(pair)) {
            return pair;
        }
        throw new Error(`Invalid instrument: ${pair}`);
    }
    parseTimeframe(timeframe) {
        if (Object.values(Timeframe).includes(timeframe)) {
            return timeframe;
        }
        throw new Error(`Invalid timeframe: ${timeframe}`);
    }
};
MarketDataService = __decorate([
    injectable()
], MarketDataService);
export { MarketDataService };
