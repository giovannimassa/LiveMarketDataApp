import "reflect-metadata";
import { inject, injectable } from "inversify";
import Database from "better-sqlite3";
import path from "path";
import fs from "fs";
import { IPairConfig } from "../config/pair.config.js";
import { TYPES } from "../core/types.js";
import { Logger } from "../utils/logger.js";
import { AppConfig } from "../config/app.config.js";
import { OrderBy } from "./common.js";
import { Timeframe } from "dukascopy-node";
import { MarketItem } from "../models/marketitem.model.js";
import { AggregatedData } from "../models/aggregated-data.model.js";
import { MarketItemString } from "../models/marketitem-string.model.js";

abstract class DatabaseServiceBase {

  constructor(
    @inject(Logger) protected logger: Logger
  ) {}

  protected log(...msg: any) {
    if (AppConfig.isDatabaseLogEnabled()) {
      this.logger.info("[DB] " + msg);
    }
  }
}

@injectable()
export class DatabaseService extends DatabaseServiceBase {

  // private tf5minTableName: string;
  // private tf15minTableName: string;

  private timeframeTables: Array<string>;
  private timeframes: Array<string>;
  private db: Database.Database;

  constructor(
    @inject(Logger) logger: Logger,
    @inject(TYPES.PairConfig) private pairConfig: IPairConfig,
  ) {
    super(logger);

    this.log("Load database...");
    this.timeframeTables = new Array<string>();
    this.timeframeTables.push(
      `${this.getTableName(Timeframe.m5)}`,
      `${this.getTableName(Timeframe.m15)}`,
      `${this.getTableName(Timeframe.h1)}`
    );

    this.timeframes = new Array<string>();
    this.timeframes.push(
      `${Timeframe.m5}`,
      `${Timeframe.m15}`,
      `${Timeframe.h1}`
    );

    // this.tf5minTableName = `${this.pairConfig.symbol}-${Timeframe.m5}`;
    // this.tf15minTableName = `${this.pairConfig.symbol}-${Timeframe.m15}`;

    // const dbPath = path.join(process.cwd(), "data", `${this.pairConfig.symbol}-data.db`);
    const dbPath = AppConfig.databasePath();

    this.log("database path: " + dbPath);

    // if (!fs.existsSync("data")) {
    //   fs.mkdirSync("data");
    // }

    this.db = new Database(dbPath);

    this.createTables();
  }

  private getTableName(timeframe: Timeframe) {
    return `${this.pairConfig.symbol}${timeframe}`;
  }

  private getMarketDataRecord(row: any): MarketItem {
    return {
      timestamp: row.timestamp,
      openPrice: parseFloat(row.openPrice),
      highPrice: parseFloat(row.highPrice),
      lowPrice: parseFloat(row.lowPrice),
      closePrice: parseFloat(row.closePrice),
      volume: parseFloat(row.volume),
      sma20: parseFloat(row.sma20),
      sma50: parseFloat(row.sma50),
      ema20: parseFloat(row.ema20),
      ema50: parseFloat(row.ema50),
      ema100: parseFloat(row.ema100),
      ema200: parseFloat(row.ema200),
      bbands20: parseFloat(row.bbands20),
      rsi14: parseFloat(row.rsi14),
      atr14: parseFloat(row.atr14),
      macdSignal: parseFloat(row.macdSignal),
      macdFast: parseFloat(row.macdFast),
      macdSlow: parseFloat(row.macdSlow),
      macdNorm: parseFloat(row.macdNorm),
      slopeEma: parseFloat(row.slopeEma),
      distanceEma: parseFloat(row.distanceEma),
      roc: parseFloat(row.roc),
      stoch: parseFloat(row.stoch),
      obv: parseInt(row.obv),
      volumeZScore: parseFloat(row.volumeZScore),
      volumeAtrRatio: parseFloat(row.volumeAtrRatio),
      fvgBullish: parseInt(row.fvgBullish),
      fvgBearish: parseInt(row.fvgBearish),
      fvgSize: parseFloat(row.fvgSize),
      fvgSizeAtrNorm: parseFloat(row.fvgSizeAtrNorm),
      bodySizePerc: parseInt(row.bodySizePerc),
      upperWickPerc: parseInt(row.upperWickPerc),
      lowerWickPerc: parseInt(row.lowerWickPerc),
      rangeExp: parseFloat(row.rangeExp),
      logReturn: parseFloat(row.logReturn),
      rollingVolatility: parseFloat(row.rollingVolatility),
      rollingVolatilityAtrNorm: parseFloat(row.rollingVolatilityAtrNorm),
      rollingVolatilitySlope: parseFloat(row.rollingVolatilitySlope)
    };
  }

  private getAggregatedDataRecord(row: any): AggregatedData {
    return {
      timestamp_m5: row.timestamp_m5,
      open_m5: parseFloat(row.open_m5),
      close_m5: parseFloat(row.close_m5),
      high_m5: parseFloat(row.high_m5),
      low_m5: parseFloat(row.low_m5),
      volume_m5: row.volume_m5 !== undefined && row.volume_m5 !== null ? String(row.volume_m5) : undefined,
      sma20_m5: row.sma20_m5 !== undefined && row.sma20_m5 !== null ? String(row.sma20_m5) : undefined,
      sma50_m5: row.sma50_m5 !== undefined && row.sma50_m5 !== null ? String(row.sma50_m5) : undefined,
      ema20_m5: row.ema20_m5 !== undefined && row.ema20_m5 !== null ? String(row.ema20_m5) : undefined,
      ema50_m5: row.ema50_m5 !== undefined && row.ema50_m5 !== null ? String(row.ema50_m5) : undefined,
      ema100_m5: row.ema100_m5 !== undefined && row.ema100_m5 !== null ? String(row.ema100_m5) : undefined,
      ema200_m5: row.ema200_m5 !== undefined && row.ema200_m5 !== null ? String(row.ema200_m5) : undefined,
      bbands20_m5: row.bbands20_m5 !== undefined && row.bbands20_m5 !== null ? String(row.bbands20_m5) : undefined,
      rsi14_m5: row.rsi14_m5 !== undefined && row.rsi14_m5 !== null ? String(row.rsi14_m5) : undefined,
      atr14_m5: row.atr14_m5 !== undefined && row.atr14_m5 !== null ? String(row.atr14_m5) : undefined,
      macdNorm_m5: row.macdNorm_m5 !== undefined && row.macdNorm_m5 !== null ? String(row.macdNorm_m5) : undefined,
      slopeEma_m5: row.slopeEma_m5 !== undefined && row.slopeEma_m5 !== null ? String(row.slopeEma_m5) : undefined,
      distanceEma_m5: row.distanceEma_m5 !== undefined && row.distanceEma_m5 !== null ? String(row.distanceEma_m5) : undefined,
      roc_m5: row.roc_m5 !== undefined && row.roc_m5 !== null ? String(row.roc_m5) : undefined,
      stoch_m5: row.stoch_m5 !== undefined && row.stoch_m5 !== null ? String(row.stoch_m5) : undefined,
      obv_m5: row.obv_m5 !== undefined && row.obv_m5 !== null ? String(row.obv_m5) : undefined,
      volumeZScore_m5: row.volumeZScore_m5 !== undefined && row.volumeZScore_m5 !== null ? String(row.volumeZScore_m5) : undefined,
      volumeAtrRatio_m5: row.volumeAtrRatio_m5 !== undefined && row.volumeAtrRatio_m5 !== null ? String(row.volumeAtrRatio_m5) : undefined,
      fvgBullish_m5: row.fvgBullish_m5 !== undefined && row.fvgBullish_m5 !== null ? String(row.fvgBullish_m5) : undefined,
      fvgBearish_m5: row.fvgBearish_m5 !== undefined && row.fvgBearish_m5 !== null ? String(row.fvgBearish_m5) : undefined,
      fvgSize_m5: row.fvgSize_m5 !== undefined && row.fvgSize_m5 !== null ? String(row.fvgSize_m5) : undefined,
      fvgSizeAtrNorm_m5: row.fvgSizeAtrNorm_m5 !== undefined && row.fvgSizeAtrNorm_m5 !== null ? String(row.fvgSizeAtrNorm_m5) : undefined,
      bodySizePerc_m5: row.bodySizePerc_m5 !== undefined && row.bodySizePerc_m5 !== null ? String(row.bodySizePerc_m5) : undefined,
      upperWickPerc_m5: row.upperWickPerc_m5 !== undefined && row.upperWickPerc_m5 !== null ? String(row.upperWickPerc_m5) : undefined,
      lowerWickPerc_m5: row.lowerWickPerc_m5 !== undefined && row.lowerWickPerc_m5 !== null ? String(row.lowerWickPerc_m5) : undefined,
      rangeExp_m5: row.rangeExp_m5 !== undefined && row.rangeExp_m5 !== null ? String(row.rangeExp_m5) : undefined,
      logReturn_m5: row.logReturn_m5 !== undefined && row.logReturn_m5 !== null ? String(row.logReturn_m5) : undefined,
      rollingVolatility_m5: row.rollingVolatility_m5 !== undefined && row.rollingVolatility_m5 !== null ? String(row.rollingVolatility_m5) : undefined,
      rollingVolatilityAtrNorm_m5: row.rollingVolatilityAtrNorm_m5 !== undefined && row.rollingVolatilityAtrNorm_m5 !== null ? String(row.rollingVolatilityAtrNorm_m5) : undefined,
      rollingVolatilitySlope_m5: row.rollingVolatilitySlope_m5 !== undefined && row.rollingVolatilitySlope_m5 !== null ? String(row.rollingVolatilitySlope_m5) : undefined,
      sma20_m15: row.sma20_m15 !== undefined && row.sma20_m15 !== null ? String(row.sma20_m15) : undefined,
      sma50_m15: row.sma50_m15 !== undefined && row.sma50_m15 !== null ? String(row.sma50_m15) : undefined,
      ema20_m15: row.ema20_m15 !== undefined && row.ema20_m15 !== null ? String(row.ema20_m15) : undefined,
      ema50_m15: row.ema50_m15 !== undefined && row.ema50_m15 !== null ? String(row.ema50_m15) : undefined,
      ema100_m15: row.ema100_m15 !== undefined && row.ema100_m15 !== null ? String(row.ema100_m15) : undefined,
      ema200_m15: row.ema200_m15 !== undefined && row.ema200_m15 !== null ? String(row.ema200_m15) : undefined,
      bbands20_m15: row.bbands20_m15 !== undefined && row.bbands20_m15 !== null ? String(row.bbands20_m15) : undefined,
      rsi14_m15: row.rsi14_m15 !== undefined && row.rsi14_m15 !== null ? String(row.rsi14_m15) : undefined,
      atr14_m15: row.atr14_m15 !== undefined && row.atr14_m15 !== null ? String(row.atr14_m15) : undefined,
      macdNorm_m15: row.macdNorm_m15 !== undefined && row.macdNorm_m15 !== null ? String(row.macdNorm_m15) : undefined,
      slopeEma_m15: row.slopeEma_m15 !== undefined && row.slopeEma_m15 !== null ? String(row.slopeEma_m15) : undefined,
      distanceEma_m15: row.distanceEma_m15 !== undefined && row.distanceEma_m15 !== null ? String(row.distanceEma_m15) : undefined,
      roc_m15: row.roc_m15 !== undefined && row.roc_m15 !== null ? String(row.roc_m15) : undefined,
      stoch_m15: row.stoch_m15 !== undefined && row.stoch_m15 !== null ? String(row.stoch_m15) : undefined,
      obv_m15: row.obv_m15 !== undefined && row.obv_m15 !== null ? String(row.obv_m15) : undefined,
      volumeZScore_m15: row.volumeZScore_m15 !== undefined && row.volumeZScore_m15 !== null ? String(row.volumeZScore_m15) : undefined,
      volumeAtrRatio_m15: row.volumeAtrRatio_m15 !== undefined && row.volumeAtrRatio_m15 !== null ? String(row.volumeAtrRatio_m15) : undefined,
      fvgBullish_m15: row.fvgBullish_m15 !== undefined && row.fvgBullish_m15 !== null ? String(row.fvgBullish_m15) : undefined,
      fvgBearish_m15: row.fvgBearish_m15 !== undefined && row.fvgBearish_m15 !== null ? String(row.fvgBearish_m15) : undefined,
      fvgSize_m15: row.fvgSize_m15 !== undefined && row.fvgSize_m15 !== null ? String(row.fvgSize_m15) : undefined,
      fvgSizeAtrNorm_m15: row.fvgSizeAtrNorm_m15 !== undefined && row.fvgSizeAtrNorm_m15 !== null ? String(row.fvgSizeAtrNorm_m15) : undefined,
      bodySizePerc_m15: row.bodySizePerc_m15 !== undefined && row.bodySizePerc_m15 !== null ? String(row.bodySizePerc_m15) : undefined,
      upperWickPerc_m15: row.upperWickPerc_m15 !== undefined && row.upperWickPerc_m15 !== null ? String(row.upperWickPerc_m15) : undefined,
      lowerWickPerc_m15: row.lowerWickPerc_m15 !== undefined && row.lowerWickPerc_m15 !== null ? String(row.lowerWickPerc_m15) : undefined,
      rangeExp_m15: row.rangeExp_m15 !== undefined && row.rangeExp_m15 !== null ? String(row.rangeExp_m15) : undefined,
      logReturn_m15: row.logReturn_m15 !== undefined && row.logReturn_m15 !== null ? String(row.logReturn_m15) : undefined,
      rollingVolatility_m15: row.rollingVolatility_m15 !== undefined && row.rollingVolatility_m15 !== null ? String(row.rollingVolatility_m15) : undefined,
      rollingVolatilityAtrNorm_m15: row.rollingVolatilityAtrNorm_m15 !== undefined && row.rollingVolatilityAtrNorm_m15 !== null ? String(row.rollingVolatilityAtrNorm_m15) : undefined,
      rollingVolatilitySlope_m15: row.rollingVolatilitySlope_m15 !== undefined && row.rollingVolatilitySlope_m15 !== null ? String(row.rollingVolatilitySlope_m15) : undefined,
      sma20_h1: row.sma20_h1 !== undefined && row.sma20_h1 !== null ? String(row.sma20_h1) : undefined,
      sma50_h1: row.sma50_h1 !== undefined && row.sma50_h1 !== null ? String(row.sma50_h1) : undefined,
      ema20_h1: row.ema20_h1 !== undefined && row.ema20_h1 !== null ? String(row.ema20_h1) : undefined,
      ema50_h1: row.ema50_h1 !== undefined && row.ema50_h1 !== null ? String(row.ema50_h1) : undefined,
      ema100_h1: row.ema100_h1 !== undefined && row.ema100_h1 !== null ? String(row.ema100_h1) : undefined,
      ema200_h1: row.ema200_h1 !== undefined && row.ema200_h1 !== null ? String(row.ema200_h1) : undefined,
      bbands20_h1: row.bbands20_h1 !== undefined && row.bbands20_h1 !== null ? String(row.bbands20_h1) : undefined,
      rsi14_h1: row.rsi14_h1 !== undefined && row.rsi14_h1 !== null ? String(row.rsi14_h1) : undefined,
      atr14_h1: row.atr14_h1 !== undefined && row.atr14_h1 !== null ? String(row.atr14_h1) : undefined,
      macdNorm_h1: row.macdNorm_h1 !== undefined && row.macdNorm_h1 !== null ? String(row.macdNorm_h1) : undefined,
      slopeEma_h1: row.slopeEma_h1 !== undefined && row.slopeEma_h1 !== null ? String(row.slopeEma_h1) : undefined,
      distanceEma_h1: row.distanceEma_h1 !== undefined && row.distanceEma_h1 !== null ? String(row.distanceEma_h1) : undefined,
      roc_h1: row.roc_h1 !== undefined && row.roc_h1 !== null ? String(row.roc_h1) : undefined,
      stoch_h1: row.stoch_h1 !== undefined && row.stoch_h1 !== null ? String(row.stoch_h1) : undefined,
      obv_h1: row.obv_h1 !== undefined && row.obv_h1 !== null ? String(row.obv_h1) : undefined,
      volumeZScore_h1: row.volumeZScore_h1 !== undefined && row.volumeZScore_h1 !== null ? String(row.volumeZScore_h1) : undefined,
      volumeAtrRatio_h1: row.volumeAtrRatio_h1 !== undefined && row.volumeAtrRatio_h1 !== null ? String(row.volumeAtrRatio_h1) : undefined,
      fvgBullish_h1: row.fvgBullish_h1 !== undefined && row.fvgBullish_h1 !== null ? String(row.fvgBullish_h1) : undefined,
      fvgBearish_h1: row.fvgBearish_h1 !== undefined && row.fvgBearish_h1 !== null ? String(row.fvgBearish_h1) : undefined,
      fvgSize_h1: row.fvgSize_h1 !== undefined && row.fvgSize_h1 !== null ? String(row.fvgSize_h1) : undefined,
      fvgSizeAtrNorm_h1: row.fvgSizeAtrNorm_h1 !== undefined && row.fvgSizeAtrNorm_h1 !== null ? String(row.fvgSizeAtrNorm_h1) : undefined,
      bodySizePerc_h1: row.bodySizePerc_h1 !== undefined && row.bodySizePerc_h1 !== null ? String(row.bodySizePerc_h1) : undefined,
      upperWickPerc_h1: row.upperWickPerc_h1 !== undefined && row.upperWickPerc_h1 !== null ? String(row.upperWickPerc_h1) : undefined,
      lowerWickPerc_h1: row.lowerWickPerc_h1 !== undefined && row.lowerWickPerc_h1 !== null ? String(row.lowerWickPerc_h1) : undefined,
      rangeExp_h1: row.rangeExp_h1 !== undefined && row.rangeExp_h1 !== null ? String(row.rangeExp_h1) : undefined,
      logReturn_h1: row.logReturn_h1 !== undefined && row.logReturn_h1 !== null ? String(row.logReturn_h1) : undefined,
      rollingVolatility_h1: row.rollingVolatility_h1 !== undefined && row.rollingVolatility_h1 !== null ? String(row.rollingVolatility_h1) : undefined,
      rollingVolatilityAtrNorm_h1: row.rollingVolatilityAtrNorm_h1 !== undefined && row.rollingVolatilityAtrNorm_h1 !== null ? String(row.rollingVolatilityAtrNorm_h1) : undefined,
      rollingVolatilitySlope_h1: row.rollingVolatilitySlope_h1 !== undefined && row.rollingVolatilitySlope_h1 !== null ? String(row.rollingVolatilitySlope_h1) : undefined
    };
  }

  private createTables() {

    this.timeframeTables.forEach(t => {

      const sql = `
        CREATE TABLE IF NOT EXISTS ${t} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            openPrice TEXT NOT NULL,
            highPrice TEXT NOT NULL,
            lowPrice TEXT NOT NULL,
            closePrice TEXT NOT NULL,
            volume TEXT NOT NULL,
            sma20 TEXT,
            sma50 TEXT,
            ema20 TEXT,
            ema50 TEXT,
            ema100 TEXT,
            ema200 TEXT,
            bbands20 TEXT,
            rsi14 TEXT,
            atr14 TEXT,
            macdSignal TEXT,
            macdFast TEXT,
            macdSlow TEXT,
            macdNorm TEXT,
            slopeEma TEXT,
            distanceEma TEXT,
            roc TEXT,
            stoch TEXT,
            obv INTEGER,
            volumeZScore TEXT,
            volumeAtrRatio TEXT,
            fvgBullish INTEGER,
            fvgBearish INTEGER,
            fvgSize TEXT,
            fvgSizeAtrNorm TEXT,
            bodySizePerc INTEGER,
            upperWickPerc INTEGER,
            lowerWickPerc INTEGER,
            rangeExp TEXT,
            logReturn TEXT,
            rollingVolatility TEXT,
            rollingVolatilityAtrNorm TEXT,
            rollingVolatilitySlope TEXT
          );`;
        
        this.log(sql);
        
        this.db.exec(sql);
    });
    
    this.createAggregateTable();
  }

  createAggregateTable() {
    
      let sql = `CREATE TABLE IF NOT EXISTS aggregationData (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp_m5 TEXT NOT NULL,
                  open_m5 REAL NOT NULL,
                  close_m5 REAL NOT NULL,
                  high_m5 REAL NOT NULL,
                  low_m5 REAL NOT NULL,
                  volume_m5 REAL NOT NULL,`;
      
      this.timeframes.forEach((t, i) => {
        sql = `${sql}
                sma20_${t} TEXT,
                sma50_${t} TEXT,
                ema20_${t} TEXT,
                ema50_${t} TEXT,
                ema100_${t} TEXT,
                ema200_${t} TEXT,
                bbands20_${t} TEXT,
                rsi14_${t} TEXT,
                atr14_${t} TEXT,
                macdNorm_${t} TEXT,
                slopeEma_${t} TEXT,
                distanceEma_${t} TEXT,
                roc_${t} TEXT,
                stoch_${t} TEXT,
                obv_${t} INTEGER,
                volumeZScore_${t} TEXT,
                volumeAtrRatio_${t} TEXT,
                fvgBullish_${t} INTEGER,
                fvgBearish_${t} INTEGER,
                fvgSize_${t} TEXT,
                fvgSizeAtrNorm_${t} TEXT,
                bodySizePerc_${t} INTEGER,
                upperWickPerc_${t} INTEGER,
                lowerWickPerc_${t} INTEGER,
                rangeExp_${t} TEXT,
                logReturn_${t} TEXT,
                rollingVolatility_${t} TEXT,
                rollingVolatilityAtrNorm_${t} TEXT,
                rollingVolatilitySlope_${t} TEXT,`;
      });

      sql = sql.slice(0, -1); // Rimuove l'ultima virgola
      sql = `${sql});`;
      this.log(sql);
      this.db.exec(sql);
  }

  saveMarketData(timeframe: Timeframe, row: MarketItem) {
    
    const sql = `
      INSERT INTO ${this.getTableName(timeframe)}
      (timestamp, openPrice, highPrice, lowPrice, closePrice, volume, sma20, sma50, ema20, ema50, ema100, ema200, bbands20, rsi14, atr14, macdSignal,
       macdFast, macdSlow, macdNorm, slopeEma, distanceEma, roc, stoch, obv, volumeZScore, volumeAtrRatio, fvgBullish, fvgBearish, fvgSize,
       fvgSizeAtrNorm, bodySizePerc, upperWickPerc, lowerWickPerc, rangeExp, logReturn, rollingVolatility, rollingVolatilityAtrNorm, rollingVolatilitySlope)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;
    const stmt = this.db.prepare(sql);
    
    this.log(sql);
    
    stmt.run(row.timestamp, row.openPrice, row.highPrice, row.lowPrice, row.closePrice, row.volume,
      row.sma20?.toFixed(5),
      row.sma50?.toFixed(5),
      row.ema20?.toFixed(5),
      row.ema50?.toFixed(5),
      row.ema100?.toFixed(5),
      row.ema200?.toFixed(5),
      row.bbands20?.toFixed(5),
      row.rsi14?.toFixed(2),
      row.atr14?.toFixed(6),
      row.macdSignal?.toFixed(6),
      row.macdFast?.toFixed(6),
      row.macdSlow?.toFixed(6),
      row.macdNorm?.toFixed(6),
      row.slopeEma?.toFixed(8),
      row.distanceEma?.toFixed(6),
      row.roc?.toFixed(4),
      row.stoch?.toFixed(2),
      row.obv?.toFixed(2),
      row.volumeZScore?.toFixed(4),
      row.volumeAtrRatio?.toFixed(6),
      row.fvgBullish,
      row.fvgBearish,
      row.fvgSize?.toFixed(6),
      row.fvgSizeAtrNorm?.toFixed(6),
      row.bodySizePerc?.toFixed(2),
      row.upperWickPerc?.toFixed(2),
      row.lowerWickPerc?.toFixed(2),
      row.rangeExp?.toFixed(3),
      row.logReturn?.toFixed(8),
      row.rollingVolatility?.toFixed(6),
      row.rollingVolatilityAtrNorm?.toFixed(6),
      row.rollingVolatilitySlope?.toFixed(8));
  }

  getAllMarketData(timeframe: Timeframe): MarketItem[] {

    const sql = `SELECT * FROM ${this.getTableName(timeframe)}`;
    const stmt = this.db.prepare(sql);
    
    this.log(sql);

    const result = stmt.all();
    return result.length !== 0 ? result.map((row: any) => this.getMarketDataRecord(row)) : new Array<MarketItem>();
  }

  getMarketDataList(timeframe: Timeframe, lastNumOfData: number, orderBy: OrderBy): MarketItem[] {

    const sql = `SELECT * FROM ${this.getTableName(timeframe)} ORDER BY timestamp ${orderBy} LIMIT ${lastNumOfData}`;
    const stmt = this.db.prepare(sql);
    
    this.log(sql);

    const result = stmt.all();
    return result.length !== 0 ? result.map((row: any) => this.getMarketDataRecord(row)) : new Array<MarketItem>();
  }

  getMarketDataByTimestampRange(timeframe: Timeframe, timestampStart: string, timestampEnd: string): MarketItem[] {
    
    const sql = `SELECT * FROM ${this.getTableName(timeframe)} WHERE timestamp BETWEEN ? AND ?`;
    const stmt = this.db.prepare(sql);
    
    this.log(sql);

    const result = stmt.all(timestampStart, timestampEnd);
    return result.length !== 0 ? result.map((row: any) => this.getMarketDataRecord(row)) : new Array<MarketItem>();
  }

  getMarketDataByTimestampRangeAsString(timeframe: Timeframe, timestampStart: string, timestampEnd: string): MarketItemString[] {
    
    const sql = `SELECT * FROM ${this.getTableName(timeframe)} WHERE timestamp BETWEEN ? AND ?`;
    const stmt = this.db.prepare(sql);
    
    this.log(sql);

    const result = stmt.all(timestampStart, timestampEnd);
    return result.length !== 0 ? result.map((row: any) => ({
      timestamp: row.timestamp,
      openPrice: row.openPrice,
      highPrice: row.highPrice,
      lowPrice: row.lowPrice,
      closePrice: row.closePrice,
      volume: String(row.volume),
      sma20: row.sma20 !== undefined && row.sma20 !== null ? String(row.sma20) : undefined,
      sma50: row.sma50 !== undefined && row.sma50 !== null ? String(row.sma50) : undefined,
      ema20: row.ema20 !== undefined && row.ema20 !== null ? String(row.ema20) : undefined,
      ema50: row.ema50 !== undefined && row.ema50 !== null ? String(row.ema50) : undefined,
      ema100: row.ema100 !== undefined && row.ema100 !== null ? String(row.ema100) : undefined,
      ema200: row.ema200 !== undefined && row.ema200 !== null ? String(row.ema200) : undefined,
      bbands20: row.bbands20 !== undefined && row.bbands20 !== null ? String(row.bbands20) : undefined,
      rsi14: row.rsi14 !== undefined && row.rsi14 !== null ? String(row.rsi14) : undefined,
      atr14: row.atr14 !== undefined && row.atr14 !== null ? String(row.atr14) : undefined,
      macdSignal: row.macdSignal !== undefined && row.macdSignal !== null ? String(row.macdSignal) : undefined,
      macdFast: row.macdFast !== undefined && row.macdFast !== null ? String(row.macdFast) : undefined,
      macdSlow: row.macdSlow !== undefined && row.macdSlow !== null ? String(row.macdSlow) : undefined,
      macdNorm: row.macdNorm !== undefined && row.macdNorm !== null ? String(row.macdNorm) : undefined,
      slopeEma: row.slopeEma !== undefined && row.slopeEma !== null ? String(row.slopeEma) : undefined,
      distanceEma: row.distanceEma !== undefined && row.distanceEma !== null ? String(row.distanceEma) : undefined,
      roc: row.roc !== undefined && row.roc !== null ? String(row.roc) : undefined,
      stoch: row.stoch !== undefined && row.stoch !== null ? String(row.stoch) : undefined,
      obv: row.obv !== undefined && row.obv !== null ? String(row.obv) : undefined,
      volumeZScore: row.volumeZScore !== undefined && row.volumeZScore !== null ? String(row.volumeZScore) : undefined,
      volumeAtrRatio: row.volumeAtrRatio !== undefined && row.volumeAtrRatio !== null ? String(row.volumeAtrRatio) : undefined,
      fvgBullish: row.fvgBullish !== undefined && row.fvgBullish !== null ? String(row.fvgBullish) : undefined,
      fvgBearish: row.fvgBearish !== undefined && row.fvgBearish !== null ? String(row.fvgBearish) : undefined,
      fvgSize: row.fvgSize !== undefined && row.fvgSize !== null ? String(row.fvgSize) : undefined,
      fvgSizeAtrNorm: row.fvgSizeAtrNorm !== undefined && row.fvgSizeAtrNorm !== null ? String(row.fvgSizeAtrNorm) : undefined,
      bodySizePerc: row.bodySizePerc !== undefined && row.bodySizePerc !== null ? String(row.bodySizePerc) : undefined,
      upperWickPerc: row.upperWickPerc !== undefined && row.upperWickPerc !== null ? String(row.upperWickPerc) : undefined,
      lowerWickPerc: row.lowerWickPerc !== undefined && row.lowerWickPerc !== null ? String(row.lowerWickPerc) : undefined,
      rangeExp: row.rangeExp !== undefined && row.rangeExp !== null ? String(row.rangeExp) : undefined,
      logReturn: row.logReturn !== undefined && row.logReturn !== null ? String(row.logReturn) : undefined,
      rollingVolatility: row.rollingVolatility !== undefined && row.rollingVolatility !== null ? String(row.rollingVolatility) : undefined,
      rollingVolatilityAtrNorm: row.rollingVolatilityAtrNorm !== undefined && row.rollingVolatilityAtrNorm !== null ? String(row.rollingVolatilityAtrNorm) : undefined,
      rollingVolatilitySlope: row.rollingVolatilitySlope !== undefined && row.rollingVolatilitySlope !== null ? String(row.rollingVolatilitySlope) : undefined
    })) : new Array<MarketItemString>();
  }

  getCountMarketData(timeframe: Timeframe): number {

    const sql = `SELECT COUNT(*) as tot FROM ${this.getTableName(timeframe)}`;
    const stmt = this.db.prepare(sql);

    this.log(sql);
  
    return (stmt.get() as any).tot as number;
  }

  getLastMarketData(timeframe: Timeframe): MarketItem | undefined {
    
    const sql = `SELECT * FROM ${this.getTableName(timeframe)} ORDER BY timestamp DESC LIMIT 1`;
    const stmt = this.db.prepare(sql);

    this.log(sql);

    const result = stmt.get();

    return result !== undefined ? this.getMarketDataRecord(result) : undefined;
  }

  saveAggregateData(row: AggregatedData) {
    
    const sql = `
      INSERT INTO aggregationData
      (timestamp_m5,open_m5,close_m5,high_m5,low_m5,volume_m5,sma20_m5,sma50_m5,ema20_m5,ema50_m5,ema100_m5,ema200_m5,bbands20_m5,
       rsi14_m5,atr14_m5,macdNorm_m5,slopeEma_m5,distanceEma_m5,roc_m5,stoch_m5,obv_m5,volumeZScore_m5,volumeAtrRatio_m5,fvgBullish_m5,
       fvgBearish_m5,fvgSize_m5,fvgSizeAtrNorm_m5,bodySizePerc_m5,upperWickPerc_m5,lowerWickPerc_m5,rangeExp_m5,logReturn_m5,
       rollingVolatility_m5,rollingVolatilityAtrNorm_m5,rollingVolatilitySlope_m5,sma20_m15,sma50_m15,ema20_m15,ema50_m15,ema100_m15,
       ema200_m15,bbands20_m15,rsi14_m15,atr14_m15,macdNorm_m15,slopeEma_m15,distanceEma_m15,roc_m15,stoch_m15,obv_m15,volumeZScore_m15,
       volumeAtrRatio_m15,fvgBullish_m15,fvgBearish_m15,fvgSize_m15,fvgSizeAtrNorm_m15,bodySizePerc_m15,upperWickPerc_m15,lowerWickPerc_m15,
       rangeExp_m15,logReturn_m15,rollingVolatility_m15,rollingVolatilityAtrNorm_m15,rollingVolatilitySlope_m15,sma20_h1,sma50_h1,
       ema20_h1,ema50_h1,ema100_h1,ema200_h1,bbands20_h1,rsi14_h1,atr14_h1,macdNorm_h1,slopeEma_h1,distanceEma_h1,roc_h1,stoch_h1,obv_h1,
       volumeZScore_h1,volumeAtrRatio_h1,fvgBullish_h1,fvgBearish_h1,fvgSize_h1,fvgSizeAtrNorm_h1,bodySizePerc_h1,upperWickPerc_h1,
       lowerWickPerc_h1,rangeExp_h1,logReturn_h1,rollingVolatility_h1,rollingVolatilityAtrNorm_h1,rollingVolatilitySlope_h1)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,
              ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,
              ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
      `;
    const stmt = this.db.prepare(sql);
    stmt.run(
      // 5 minutes timeframe
      row.timestamp_m5, row.open_m5, row.close_m5, row.high_m5, row.low_m5, row.volume_m5,
      row.sma20_m5, row.sma50_m5, row.ema20_m5, row.ema50_m5, row.ema100_m5, row.ema200_m5, 
      row.bbands20_m5, row.rsi14_m5, row.atr14_m5, row.macdNorm_m5, row.slopeEma_m5, 
      row.distanceEma_m5, row.roc_m5, row.stoch_m5, row.obv_m5, row.volumeZScore_m5, 
      row.volumeAtrRatio_m5, row.fvgBullish_m5, row.fvgBearish_m5, row.fvgSize_m5, 
      row.fvgSizeAtrNorm_m5, row.bodySizePerc_m5, row.upperWickPerc_m5, row.lowerWickPerc_m5, 
      row.rangeExp_m5, row.logReturn_m5, row.rollingVolatility_m5, 
      row.rollingVolatilityAtrNorm_m5, row.rollingVolatilitySlope_m5,
      // 15 minutes timeframe
      row.sma20_m15, row.sma50_m15, row.ema20_m15, row.ema50_m15, row.ema100_m15, row.ema200_m15, 
      row.bbands20_m15, row.rsi14_m15, row.atr14_m15, row.macdNorm_m15, row.slopeEma_m15, 
      row.distanceEma_m15, row.roc_m15, row.stoch_m15, row.obv_m15, row.volumeZScore_m15, 
      row.volumeAtrRatio_m15, row.fvgBullish_m15, row.fvgBearish_m15, row.fvgSize_m15, 
      row.fvgSizeAtrNorm_m15, row.bodySizePerc_m15, row.upperWickPerc_m15, row.lowerWickPerc_m15, 
      row.rangeExp_m15, row.logReturn_m15, row.rollingVolatility_m15, 
      row.rollingVolatilityAtrNorm_m15, row.rollingVolatilitySlope_m15,
      // 1 hour timeframe
      row.sma20_h1, row.sma50_h1, row.ema20_h1, row.ema50_h1, row.ema100_h1, row.ema200_h1, 
      row.bbands20_h1, row.rsi14_h1, row.atr14_h1, row.macdNorm_h1, row.slopeEma_h1, 
      row.distanceEma_h1, row.roc_h1, row.stoch_h1, row.obv_h1, row.volumeZScore_h1, 
      row.volumeAtrRatio_h1, row.fvgBullish_h1, row.fvgBearish_h1, row.fvgSize_h1, 
      row.fvgSizeAtrNorm_h1, row.bodySizePerc_h1, row.upperWickPerc_h1, row.lowerWickPerc_h1, 
      row.rangeExp_h1, row.logReturn_h1, row.rollingVolatility_h1, 
      row.rollingVolatilityAtrNorm_h1, row.rollingVolatilitySlope_h1
    );
  }

  getLastAggregateData(): AggregatedData | undefined {
    
    const sql = `SELECT * FROM aggregationData ORDER BY timestamp_m5 DESC LIMIT 1`;
    const stmt = this.db.prepare(sql);

    this.log(sql);

    const result = stmt.get();

    return result !== undefined ? this.getAggregatedDataRecord(result) : undefined;
  }
}