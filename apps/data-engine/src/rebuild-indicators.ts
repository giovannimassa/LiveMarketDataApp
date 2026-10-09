import "reflect-metadata";
import Database from "better-sqlite3";
import { Timeframe } from "dukascopy-node";
import { baseContainer, eurusdContainer } from "./core/container.js";
import { AppConfig } from "./config/app.config.js";
import { DatabaseService } from "./database/database.service.js";
import { IndicatorService } from "./services/indicator.service.js";
import { Candle } from "./services/marketdata.service.js";
import { MarketItem } from "./models/marketitem.model.js";
import { Logger } from "./utils/logger.js";

// Ricalcola gli indicatori partendo dalle candele grezze di un database esistente (SOURCE_DATABASE_PATH)
// e li scrive nel database di destinazione (DATABASE_PATH o quello di default), che deve avere le tabelle vuote.
const BATCH_SIZE = 20000;

const sourcePath = process.env.SOURCE_DATABASE_PATH;
if (!sourcePath) {
    throw new Error("Imposta SOURCE_DATABASE_PATH con il percorso del database da cui leggere le candele");
}

AppConfig.initialize();
const logger = baseContainer.get(Logger);
const target = eurusdContainer.get(DatabaseService);
const source = new Database(sourcePath, { readonly: true, fileMustExist: true });

for (const timeframe of [Timeframe.m5, Timeframe.m15, Timeframe.h1]) {
    if (target.getCountMarketData(timeframe) > 0) {
        throw new Error(`La tabella di destinazione ${timeframe} non e' vuota`);
    }

    // Istanza transient: ogni timeframe ha il proprio stato degli indicatori
    const indicators = eurusdContainer.get(IndicatorService);
    const rows = source
        .prepare(`SELECT timestamp, openPrice, highPrice, lowPrice, closePrice, volume FROM eurusd${timeframe} ORDER BY timestamp ASC`)
        .iterate() as Iterable<any>;

    let batch: MarketItem[] = [];
    let saved = 0;
    let duplicates = 0;
    let lastTimestamp = "";

    const flush = () => {
        target.runInTransaction(() => batch.forEach(item => target.saveMarketData(timeframe, item)));
        saved += batch.length;
        batch = [];
        logger.info(`[rebuild][${timeframe}] salvate ${saved} righe`);
    };

    for (const row of rows) {
        if (row.timestamp === lastTimestamp) {
            duplicates++;
            continue;
        }
        lastTimestamp = row.timestamp;

        const candle: Candle = {
            timestamp: Date.parse(row.timestamp),
            openPrice: Number(row.openPrice),
            highPrice: Number(row.highPrice),
            lowPrice: Number(row.lowPrice),
            closePrice: Number(row.closePrice),
            volume: Number(row.volume)
        };
        batch.push(indicators.next(candle));
        if (batch.length >= BATCH_SIZE) flush();
    }
    if (batch.length > 0) flush();

    logger.info(`[rebuild][${timeframe}] completato: ${saved} righe, ${duplicates} duplicati scartati`);
}

source.close();
