var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
var __param = (this && this.__param) || function (paramIndex, decorator) {
    return function (target, key) { decorator(target, key, paramIndex); }
};
// import { TYPES } from "../core/types.js";import { TYPES } from "../core/types.js";
import { inject, injectable } from 'inversify';
import { MarketDataService } from "../services/marketdata.service.js";
import { Logger } from '../utils/logger.js';
let EurUsdWorker = class EurUsdWorker {
    constructor(marketData, logger) {
        this.marketData = marketData;
        this.logger = logger;
    }
    async run() {
        const pair = process.env.PAIR || "eurusd";
        const timeframe = process.env.TIMEFRAME || "m5";
        const now = new Date();
        const date = {
            year: now.getUTCFullYear(),
            month: now.getUTCMonth(),
            day: now.getUTCDate()
        };
        this.logger.info(`Scarico ${pair} timeframe ${timeframe}`);
        try {
            const data = await this.marketData.getLiveData(pair, timeframe, 1);
            this.logger.success(`Dati scaricati: ${data}`);
        }
        catch (err) {
            this.logger.error("Errore durante il download", err);
        }
    }
};
EurUsdWorker = __decorate([
    injectable(),
    __param(0, inject(MarketDataService)),
    __param(1, inject(Logger)),
    __metadata("design:paramtypes", [MarketDataService,
        Logger])
], EurUsdWorker);
export { EurUsdWorker };
