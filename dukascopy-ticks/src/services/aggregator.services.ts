import { inject, injectable } from "inversify";
import { DatabaseService } from "../database/database.service.js";
import { Timeframe } from "dukascopy-node";
import { AggregatedData } from "../models/aggregated-data.model.js";
import * as fs from 'fs';
import { stringify } from "csv-stringify";
import { Logger } from "../utils/logger.js";
import { Stopwatch } from "../utils/stopwatch.js";
import { DateHelper } from "../utils/dateHelper.js";
import { LabelClassificationService } from "./label-classification.service.js";
import { MarketItemString } from "../models/marketitem-string.model.js";

@injectable()
export class AggregatorService {

    private OUTPUT_CSV: string = "eurusd_aggregated.csv";

    constructor(
        @inject(Logger) private logger: Logger,
        @inject(DatabaseService) private database: DatabaseService,
        @inject(DateHelper) private dateHelper: DateHelper,
        @inject(LabelClassificationService) private labelClassificationService: LabelClassificationService,
    ) {}

    private findClosest15M(m15: MarketItemString[], timestamp5Min: Date): MarketItemString | undefined {
        const minute = timestamp5Min.getMinutes();
        if (minute === 0 || minute === 5) {
            const hour = timestamp5Min.getHours();
            timestamp5Min.setHours(hour - 1);
            timestamp5Min.setMinutes(45);
        }
        else if (minute === 10 || minute === 15 || minute === 20) {
            timestamp5Min.setMinutes(0);
        }
        else if (minute === 25 || minute === 30 || minute === 35) {
            timestamp5Min.setMinutes(15);
        }
        else if (minute === 40 || minute === 45 || minute === 50) {
            timestamp5Min.setMinutes(30);
        }
        else if (minute === 55) {
            timestamp5Min.setMinutes(45);
        }
        return m15.find(row => row.timestamp === this.dateHelper.convertToISOString(timestamp5Min.getTime()));
        // return this.database.getMarketDataByTimestamp(Timeframe.m15, this.dateHelper.convertToISOString(timestamp5Min.getTime()));
    }

    private findClosest1H(h1: MarketItemString[], timestamp5Min: Date): MarketItemString | undefined {
        const minute = timestamp5Min.getMinutes();
        timestamp5Min.setMinutes(0);
        if (minute !== 55) {
            const hour = timestamp5Min.getHours();
            timestamp5Min.setHours(hour - 1);
        }

        return h1.find(row => row.timestamp === this.dateHelper.convertToISOString(timestamp5Min.getTime()));
        // return this.database.getMarketDataByTimestamp(Timeframe.h1, this.dateHelper.convertToISOString(timestamp5Min.getTime()));
    }

    // Estrae tutti gli indicatori da una riga e li rinomina col timeframe in input
    private extractIndicators(row: any, timeframe: Timeframe) {
        if (row === undefined) return undefined;

        const out:Record<string, any> = {};
        for (const key of Object.keys(row)) {
            if (row[key] === undefined || row[key] === null) {
                return undefined;
            }

            if (this.isKeyToExclude(key)) {
                continue;
            }

            out[`${key}_${String(timeframe)}`] = row[key].toString();
        }
        return out;
    }

    private isKeyToExclude(key: string) {
        if (key === "timestamp" ||
            key === "openPrice" ||
            key === "highPrice" ||
            key === "lowPrice" ||
            key === "closePrice" ||
            key === "volume" ||
            key === "macdSignal" ||
            key === "macdFast" ||
            key === "macdSlow"
        ) return true;
        return false;
    }

    // Il database non ha le colonne per il salvataggio delle labels.
    // Usare la versione CSV per salvare le labels.
    // Il database è utile solo per aggregare i dati dei vari timeframe e salvarli in un unico record.
    private aggregateToDatabase(m5: MarketItemString[], m15: MarketItemString[], h1: MarketItemString[]) {

        for (const row5 of m5) {
            
            let item = this.aggregateTimeframes(row5, m15, h1);
            if (item === null) continue;

            const completeItem = {
                ...item
            } as AggregatedData;
            this.database.saveAggregateData(completeItem);
        }
    }

    private aggregatoToCSV(m5: MarketItemString[], m15: MarketItemString[], h1: MarketItemString[], aggregationDataFor: AggregationDataFor) {
        // Percorso del file CSV
        // const outputPath = path.join(__dirname, this.OUTPUT_CSV);

        let labelsData1 = null;
        let labelsData2 = null;

        // Generiamo le label solo se stiamo aggregando i dati per il training, altrimenti per il test non servono
        if (aggregationDataFor !== AggregationDataFor.TEST) {
            labelsData1 = this.labelClassificationService.generateBinaryTargets(m5, 20, 0.002, 1.0);
            labelsData2 = this.labelClassificationService.generateBinaryTargets(m5, 10, 0.0005, 0.5);

            if (labelsData1 === null || labelsData2 === null) {
                this.logger.error("Errore nella generazione delle label: array di lunghezza diversa o senza valori");
                return;
            }
        }

        // Creiamo lo stream di scrittura
        const writableStream = fs.createWriteStream(this.OUTPUT_CSV);
        // Configurazione di csv-stringify
        const stringifier = stringify({
            header: true // aggiunge l'intestazione
        });

        stringifier.on('error', (err) => {
            this.logger.error(err);
        });

        writableStream.on('error', (err) => {
            this.logger.error(err);
        });

        // Colleghiamo lo stringifier allo stream di scrittura PRIMA di scrivere i dati
        stringifier.pipe(writableStream);

        let lableIndex = 0;
        let rowCountAvailable = 0;
        let rowCountUnavailable = 0;
        for (const row5 of m5) {
            
            const item = this.aggregateTimeframes(row5, m15, h1);
            if (item === null)
            {
                rowCountUnavailable++;
                continue;
            }

            rowCountAvailable++;

            let completeItem: any = {
                ...item
            };

            if (labelsData1 !== null && labelsData2 !== null) {
                const label1 = labelsData1[lableIndex];
                const label2 = labelsData2[lableIndex];
                completeItem = {
                    ...completeItem,
                    target_long_1: label1.targetLong.toString(),
                    target_short_1: label1.targetShort.toString(),
                    target_long_atr_1: label1.targetLongAtr.toString(),
                    target_short_atr_1: label1.targetShortAtr.toString(),
                    target_long_2: label2.targetLong.toString(),
                    target_short_2: label2.targetShort.toString(),
                    target_long_atr_2: label2.targetLongAtr.toString(),
                    target_short_atr_2: label2.targetShortAtr.toString(),
                };
            }

            stringifier.write(completeItem);
            lableIndex++;
        }

        this.logger.info(`Dati disponibili: ${rowCountAvailable}, Dati mancanti: ${rowCountUnavailable}`);

        stringifier.end();
    }

    private aggregateTimeframes(rowM5: MarketItemString, m15: MarketItemString[], h1: MarketItemString[]) {
        const ts = new Date(rowM5.timestamp);
        // const stopwatch2 = new Stopwatch();
        // stopwatch2.start();
        const rowM15 = this.findClosest15M(m15, ts);
        const rowM1h = this.findClosest1H(h1, ts);
        // stopwatch2.stop();
        
        if (!rowM15 || !rowM1h) {
            this.logger.warn(`Dati mancanti per il timestamp: ${rowM5.timestamp}`);
            return null;
        }

        const indicators5m  = this.extractIndicators(rowM5,  Timeframe.m5);
        const indicators15m = this.extractIndicators(rowM15, Timeframe.m15);
        const indicators1h = this.extractIndicators(rowM1h, Timeframe.h1);

        if (indicators5m === undefined || indicators15m === undefined || indicators1h === undefined) {
            this.logger.warn(`Dati mancanti per il timestamp: ${rowM5.timestamp} - estrazione indicatori non riuscito`);
            return null;
        }

        const base = {
            timestamp_m5: rowM5.timestamp,
            open_m5: rowM5.openPrice,
            close_m5: rowM5.closePrice,
            high_m5: rowM5.highPrice,
            low_m5: rowM5.lowPrice,
            volume_m5: rowM5.volume,
        };

        const item = {
            ...base,
            ...indicators5m,
            ...indicators15m,
            ...indicators1h
        };

        // this.logger.verbose(`Dati 15min: ${JSON.stringify(item)}`);
        return item;
    }

    aggregate(timestampStart: string, timestampEnd: string, aggregationTo: AggregationTo, aggregationDataFor: AggregationDataFor) {
        const stopwatch = new Stopwatch();
        stopwatch.start();

        const m5  = this.database.getMarketDataByTimestampRangeAsString(Timeframe.m5, timestampStart, timestampEnd);
        const m15 = this.database.getMarketDataByTimestampRangeAsString(Timeframe.m15, timestampStart, timestampEnd);
        const h1  = this.database.getMarketDataByTimestampRangeAsString(Timeframe.h1, timestampStart, timestampEnd);

        switch (aggregationTo) {
            case AggregationTo.CSV:
                this.aggregatoToCSV(m5, m15, h1, aggregationDataFor);
                break;
            case AggregationTo.DATABASE:
                this.aggregateToDatabase(m5, m15, h1);
                break;
        }

        stopwatch.stop();
        this.logger.info(`Aggregazione completata in ${stopwatch.formatted()}!`);
    }
}


export enum AggregationTo {
    CSV = "csv",
    DATABASE = "database"
}

export enum AggregationDataFor {
    TRAINING = "training",
    TEST = "test"
}