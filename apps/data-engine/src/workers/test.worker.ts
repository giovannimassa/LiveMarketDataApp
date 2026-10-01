import { inject, injectable } from "inversify";
import { DatabaseService } from "../database/database.service.js";
import { Logger } from "../utils/logger.js";
import { OrderBy } from "../database/common.js";
import { MarketDataService } from "../services/marketdata.service.js";
import { IPairConfig } from "../config/pair.config.js";
import { TYPES } from "../core/types.js";
import { CandleFactory } from "../factories/candle-factory.js";
import { Stopwatch } from "../utils/stopwatch.js";
import { IndicatorService } from "../services/indicator.service.js";
import { Timeframe } from "dukascopy-node";
import { Decimal } from "decimal.js";

@injectable()
export class TestWorker {
    constructor(
        @inject(TYPES.PairConfig) private pairConfig: IPairConfig,
        @inject(Logger) private logger: Logger,
        @inject(DatabaseService) private database: DatabaseService,
        @inject(MarketDataService) private marketData: MarketDataService,
        @inject(IndicatorService) private indicatorService: IndicatorService,
    ) {}

    async test(): Promise<number> {

        await this.testGetDataFromDb();

        //await this.testHistoricalData();

        // await this.testBatchHistoricalData();

        // this.testNumberConversion();

        // this.testIndicators();

        // this.testLogging();

        // await this.testSaveDataToDb();

        return 0;
    }

    testNumberConversion() {
        const num = new Decimal(0.00002);
        const formatted = num.toDecimalPlaces(6).toNumber();
        this.logger.verbose(`Formatted number: ${formatted}`); // Output: "Formatted number: 123.46
    }

    testIndicators() {
        const lastMarketDataList = this.database.getMarketDataList(Timeframe.m5, 251, OrderBy.DESC);
        this.indicatorService.fill(lastMarketDataList.slice(1).reverse());
        const candleToTest = lastMarketDataList[0];

        var date = new Date(candleToTest.timestamp);

        var row = this.indicatorService.next(CandleFactory.createFromMarketItem(candleToTest));

        this.logger.info(JSON.stringify(row));
    }

    testLogging() {
        try {
            this.logger.verbose("This is a verbose message");
            this.logger.info("This is an info message");
            this.logger.warn("This is a warning message");
            throw new Error("This is a test error");
        } catch (error: any) {
            this.logger.error(error, { test: "testLogging" });
        }
    }

    async testSaveDataToDb() {
        let dateFrom = new Date("2026-05-01T00:00:00.000Z");
        let dateTo = new Date("2026-05-03T00:00:00.000Z");

        let count = 0; 
        for (let i = 0; i < 10; i++)
        {
            const dataList = await this.marketData.getHistoricalData(this.pairConfig.symbol, "m5", dateFrom, dateTo);
            count += dataList.length;
            dataList.forEach((candle, i) => {
                
                var row = this.indicatorService.next(candle);
                // this.logger.verbose(`${JSON.stringify(simpleRow)}`);
                this.database.saveMarketData(Timeframe.m5, row);
            });

            dateFrom.setHours(dateFrom.getHours() + 1);
            dateTo.setHours(dateTo.getHours() + 1);
        }
    }

    async testGetDataFromDb() {

        const count = this.database.getCountMarketData(Timeframe.m5);
        this.logger.info(`Total market data count for M5: ${count}`);

        // const list = this.database.getMarketDataList(Timeframe.m5, 50, OrderBy.DESC).reverse();
        // list.forEach((element, i) => {
        //     this.logger.verbose(`${i}: ${JSON.stringify(element)}`);
        // });
    }

    async testHistoricalData() {
        let dateFrom = new Date("2020-01-01T00:00:00.000Z");
        let dateTo = new Date("2020-01-10T09:00:00.000Z");

        const stopwatch = new Stopwatch();
        stopwatch.start();

        let count = 0; 
        for (let i = 0; i < 10; i++)
        {
            // this.logger.info(`DateFrom: ${dateFrom.toISOString()} - DateTo: ${dateTo.toISOString()}`);

            const dataList = await this.marketData.getHistoricalData(this.pairConfig.symbol, "m5", dateFrom, dateTo);
            count += dataList.length;
            dataList.forEach((candle, i) => {
                
                var row = this.indicatorService.next(candle);
                this.logger.info(`${JSON.stringify(row, (key, value) => value === undefined ? null : value)}`);
            });

            dateFrom.setHours(dateFrom.getHours() + 1);
            dateTo.setHours(dateTo.getHours() + 1);
        }

        stopwatch.stop();
        this.logger.verbose(`No Batch Time: ${stopwatch.formatted()} - data count: ${count}`);
    }

    async testBatchHistoricalData() {
        let dateFrom = new Date("2026-04-23T08:00:00.000Z");
        let dateTo = new Date("2026-04-23T18:00:00.000Z");
        
        const stopwatch = new Stopwatch();
        stopwatch.start();

        const dataList = await this.marketData.getBatchHistoricalData(this.pairConfig.symbol, "m5", dateFrom, dateTo);
        
        dataList.forEach((candle, i) => {
            var row = this.indicatorService.next(candle);
            // this.logger.info(`${JSON.stringify(row, (key, value) => value === undefined ? null : value)}`);
        });

        stopwatch.stop();
        this.logger.info(`Batch Time: ${stopwatch.formatted()} - data count: ${dataList.length}`);
    }
}