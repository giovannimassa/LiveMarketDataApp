import { inject, injectable } from "inversify";
import { Candle, MarketDataService } from "../services/marketdata.service.js";
import { IPairConfig } from "../config/pair.config.js";
import { Logger } from "../utils/logger.js";
import { DateHelper } from "../utils/dateHelper.js";
import { DatabaseService } from "../database/database.service.js";
import { TYPES } from "../core/types.js";
import { AppConfig } from "../config/app.config.js";
import { OrderBy } from "../database/common.js";
import { Stopwatch } from "../utils/stopwatch.js";
import { Timeframe } from "dukascopy-node";
import { IndicatorService } from "../services/indicator.service.js";
import { MarketItem } from "../models/marketitem.model.js";

@injectable()
export abstract class TimeframeBase {

    private logPrefix: string;

    constructor(
        @inject(TYPES.PairConfig) private pairConfig: IPairConfig,
        @inject(Logger) private logger: Logger,
        @inject(DateHelper) private dateHelper: DateHelper,
        @inject(MarketDataService) private marketData: MarketDataService,
        @inject(DatabaseService) private database: DatabaseService,
        @inject(IndicatorService) private indicatorService: IndicatorService,
    ) {
        this.logPrefix = `[${pairConfig.symbol}][TF:${this.timeframe()}]`;

        // Impedisce l'istanza diretta
        if (new.target === TimeframeBase) {
            throw new Error("Timeframe è una classe astratta e non può essere istanziata direttamente.");
        }
    }

    private async downloadAndStoreHistoricalData(dateFrom: Date) {
    
        this.logger.info(`${this.logPrefix}Download historical data since ${dateFrom.toISOString()} ...`);
        
        let dateFromCopy = new Date(dateFrom.getTime());
        let dateTo = new Date(dateFromCopy.getTime());
        dateTo.setHours(dateTo.getHours() + 1);

        this.logger.verbose(`${this.logPrefix}Get last live data for ${this.pairConfig.symbol} ...`);
        let liveCandleList = await this.marketData.getLiveData(this.pairConfig.symbol, this.timeframe(), 1);
        let lastLiveCandle = liveCandleList[0];
        this.logger.verbose(`${this.logPrefix}Live data completed!`);

        // =========== STEP 1: Download dati storici - START ===========
        // Scarico i dati storici fino a 1 ora prima dell'ultimo dato live disponibile.
        // Il range dell'ora in cui si trova il dato live deve essere recuperato tramite l'API live.
        this.logger.verbose(`${this.logPrefix}STEP 1 - START: Download historical data...`);
        let lastLiveDate = new Date(lastLiveCandle.timestamp);
        lastLiveDate.setHours(lastLiveDate.getHours() - 1);
        
        let isFirstHourToCalculate = true; // indica l'elaborazione dei dati della prima ora in considerazione
        while (dateTo <= lastLiveDate) {
            const stopwatch = new Stopwatch();
            stopwatch.start();

            // Scarico i dati per quella certa ora, li scorro e li salvo nel DB
            const dataList = await this.marketData.getHistoricalData(this.pairConfig.symbol, this.timeframe(), dateFromCopy, dateTo);
            for (const item of dataList) {
                
                // Se è il primo ciclo, controllo se il dato è più recente dell'ultimo dato salvato,
                // altrimenti rischiamo di inserire dati già presenti nel DB
                if (isFirstHourToCalculate) {
                    // Se sono già presenti dati nel DB scarto tra quelli scaricati tutti quelli che hanno una data precedente o uguale
                    // all'ultimo dato salvato nel DB
                    const lastMarketDataSaved = this.database.getLastMarketData(this.timeframe());
                    if (lastMarketDataSaved !== undefined && new Date(item.timestamp).getTime() <= new Date(lastMarketDataSaved.timestamp).getTime()) {
                        continue;
                    }
                }

                this.calculateIndicatorsAndSave(item);
            }

            // Aggiorno le date del nuovo range da scaricare: sposto di un'ora in avanti
            dateFromCopy = new Date(dateTo.getTime());
            dateTo.setHours(dateTo.getHours() + 1);

            // Aggiorno la data dell'ultimo dato live disponibile perchè il dato live
            // potrebbe essere aggiornato durante il processo di download dei dati storici
            liveCandleList = await this.marketData.getLiveData(this.pairConfig.symbol, this.timeframe(), 1);
            lastLiveCandle = liveCandleList[0];
            if (lastLiveCandle !== undefined) {
                lastLiveDate = new Date(lastLiveCandle.timestamp);
                lastLiveDate.setHours(lastLiveDate.getHours() - 1);
            }
            isFirstHourToCalculate = false;

            stopwatch.stop();
            this.logger.verbose(`${this.logPrefix}Download data -> dateFrom: ${dateFromCopy.toISOString()} - dateTo: ${dateTo.toISOString()} - lastLiveDate: ${lastLiveDate.toISOString()} in "${stopwatch.formatted()}"!`);

            await sleep(AppConfig.sleepBetweenHistoricalDataRequests());
        }
        this.logger.verbose(`${this.logPrefix}STEP 1 - END: Download data completed!`);
        // =========== STEP 1: Download dati storici - END ===========

        // =========== STEP 2: Allineamento dato live - START ===========
        // Una volta scaricati tutti i dati storici controllo se nel range orario del dato live ci sono dati da inserire nel DB
        // Prendo le ultime 20 candele disponibili compresa quella live
        const lastLiveCandleList = await this.marketData.getLiveData(this.pairConfig.symbol, this.timeframe(), 20);
        this.logger.verbose(`${this.logPrefix}STEP 2 - START: Aligning live data with saved data...`);
        for (const liveCandle of lastLiveCandleList) {
        
            const liveCandleDate = new Date(liveCandle.timestamp);
            const lastMarketDataSaved = this.database.getLastMarketData(this.timeframe());
            
            // Salvo tutte le candele che ho scaricato fino alla candela live,
            // ma prima controllo se una di questa è stata già salvata nel DB
            if (lastMarketDataSaved !== undefined && liveCandleDate.getTime() > new Date(lastMarketDataSaved.timestamp).getTime()) {
                this.calculateIndicatorsAndSave(liveCandle);
            }
        }
        this.logger.verbose(`${this.logPrefix}STEP 2 - END: Aligning live data with saved data completed!`);
        // =========== STEP 2: Allineamento dato live - END ===========

        this.logger.info(`${this.logPrefix}Download historical data: task completed!`);
    }

    private async isSavedDataAlignedWithLiveData(): Promise<boolean> {
        
        const lastMarketDataSaved = this.database.getLastMarketData(this.timeframe());
        if (lastMarketDataSaved === undefined) return false;
        
        const liveData = await this.marketData.getLiveData(this.pairConfig.symbol, this.timeframe(), 1);
        const lastLiveCandle = liveData[0];

        // Se il dato live non è disponibile, non posso allineare i dati salvati nel DB con quelli live, quindi ritorno false
        if (lastLiveCandle === undefined) {
            this.logger.warn(`${this.logPrefix}Live data not available!`);
            return false;
        }

        const lastMarketDataSavedDate = new Date(lastMarketDataSaved.timestamp);
        const lastLiveCandleDate = new Date(lastLiveCandle.timestamp);

        const liveCandleTime = lastLiveCandleDate.getTime();
        const marketDateTime = lastMarketDataSavedDate.getTime();

        if (liveCandleTime - marketDateTime > 5 * 60 * 1000) {
            this.logger.warn(`${this.logPrefix}Dati non allineati! Ultimo dato salvato: ${lastMarketDataSaved.timestamp}, ultimo dato live: ${this.dateHelper.convertToISOString(lastLiveCandle.timestamp)}`);
            return false;
        }

        return true;
    }

    // Allinea il database con i dati mancanti. Il database in questo caso ha già dei dati presenti
    private async checkAndAlignDatabase() {
        if (!(await this.isSavedDataAlignedWithLiveData())) {
            const stopwatch = new Stopwatch();
            stopwatch.start();
            
            this.logger.info(`${this.logPrefix}Saved data into DB are not aligned with live data! Align database with historical missing data ...`);
            
            // Inizializziamo gli indicatori con gli ultimi dati inseriti a DB
            this.resetAndInitIndicators();
            
            // database saved data
            const lastSaved = this.database.getLastMarketData(this.timeframe());
            if (lastSaved === undefined) return;
            const lastSavedDate = new Date(lastSaved.timestamp);
            
            let dateFrom = new Date(lastSavedDate.getFullYear(), lastSavedDate.getMonth(), lastSavedDate.getDate(), lastSavedDate.getHours(), 0, 0, 0);

            await this.downloadAndStoreHistoricalData(dateFrom);

            stopwatch.stop();

            this.logger.info(`${this.logPrefix}Database aligned in "${stopwatch.formatted()}"!`);
        }
    }

    // Controlla, scarica e salva tutti i dati necessari a partire da un certo anno
    private async checkDownloadAndStoreAllHistoricalData() {
        if (!this.hasDataSaved()) {
            const stopwatch = new Stopwatch();
            stopwatch.start();
            
            this.logger.info(`${this.logPrefix}Timeframe ${this.timeframe()} has no data! Download and store historical data. Fill database with all data...`);
            const startDateForDownloading = AppConfig.startDateForDownloading();
            
            // Scarico a partire da "startDateForDownloading"
            let dateFrom = new Date(startDateForDownloading);
            this.logger.info(`${this.logPrefix}Data downloaded from ${dateFrom.toISOString()}`);
            await this.downloadAndStoreHistoricalData(dateFrom);

            stopwatch.stop();
            
            this.logger.info(`${this.logPrefix}Download and store historical data completed in "${stopwatch.formatted()}"!`);
        }
    }

    private async saveLastLiveCandle(): Promise<MarketItem | undefined> {
        
        const liveCandles = await this.marketData.getLiveData(this.pairConfig.symbol, this.timeframe(), 1);
        const lastLiveCandle = liveCandles[0];

        const lastMarketDataSaved = this.database.getLastMarketData(this.timeframe());
        if (lastLiveCandle === undefined || lastMarketDataSaved === undefined) return;

        this.logger.verbose(`${this.logPrefix}last live candle: ${new Date(lastLiveCandle.timestamp).toISOString()} - last market data saved: ${new Date(lastMarketDataSaved.timestamp).toISOString()}`);

        // Controllo se il dato live è già presente nel DB, in questo caso non lo salvo nuovamente
        if (new Date(lastLiveCandle.timestamp).getTime() <= new Date(lastMarketDataSaved.timestamp).getTime()) {
            return lastMarketDataSaved;
        }

        // Salvo il nuovo dato live e calcolo gli indicatori
        const newMarketItem = this.calculateIndicatorsAndSave(lastLiveCandle);

        this.logger.verbose(`${this.logPrefix}Calculate and saved last live candle: ${JSON.stringify(lastLiveCandle)}`);

        return newMarketItem;
    }

    // Inizializza gli indicatori con gli ultimi dati presenti nel database
    private resetAndInitIndicators() {
        const stopwatch = new Stopwatch();
        stopwatch.start();

        this.logger.info(`${this.logPrefix}Allineamento indicatori in corso ...`);
        const lastMarketDataList = this.database.getMarketDataList(this.timeframe(), 250, OrderBy.DESC).reverse();
        this.indicatorService.fill(lastMarketDataList);

        stopwatch.stop();
        this.logger.info(`${this.logPrefix}Allineamento indicatori completato in ${stopwatch.formatted()}!`);
    }

    // Calcola gli indicatori della candela corrente e salva il nuovo MarketItem nel database
    private calculateIndicatorsAndSave(candle: Candle): MarketItem {
        const newMarketItem = this.indicatorService.next(candle);
        this.database.saveMarketData(this.timeframe(), newMarketItem);
        return newMarketItem;
    }

    private hasDataSaved(): boolean {
        return this.database.getCountMarketData(this.timeframe()) > 0;
    }

    abstract timeframe(): Timeframe;

    //##########################################################################################
    //########### FUNZIONE PRINCIPALE CHE GESTISCE TUTTO L'ALGORITMO DI CALCOLO DATI ###########
    //##########################################################################################
    async calculateTimeframe(): Promise<MarketItem | undefined> {
        let marketItem = undefined;
        try {
            /* Check if Timeframe 5min has no data */
            await this.checkDownloadAndStoreAllHistoricalData();

            /* Check if timeframe saved data are aligned with live */
            await this.checkAndAlignDatabase();

            /* Save last live candle */
            marketItem = await this.saveLastLiveCandle();

        } catch (error: any) {
            this.logger.error(error);
            return undefined;
        }
        
        return marketItem;
    }
}

function sleep(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
