import { Config, Format, getHistoricalRates, getRealTimeRates, Instrument, JsonItem, RealTimeRatesConfigJsonItem, Timeframe } from "dukascopy-node";
import { inject, injectable } from "inversify";
import { Logger } from "../utils/logger.js";
import { config } from "node:process";

export interface Candle {
  timestamp: number;
  openPrice: number;
  highPrice: number;
  lowPrice: number;
  closePrice: number;
  volume: number;
}

@injectable()
export class MarketDataService {
  
  constructor(
    @inject(Logger) private logger: Logger,
  ) {}

  async getHistoricalData(pair: string, timeframe: string, dateFrom: Date, dateTo: Date): Promise<Candle[]> {
    try {
      const config: Config = {
        instrument: this.parseInstrument(pair),
        timeframe: this.parseTimeframe(timeframe),
        dates: {
          from: dateFrom,
          to: dateTo,
        },
        format: "json",
        retryCount: 5,
        pauseBetweenRetriesMs: 500
      };

      const data = await getHistoricalRates(config) as JsonItem[];
      return data.map((item: JsonItem) => ({
        timestamp: item.timestamp,
        openPrice: item.open,
        highPrice: item.high,
        lowPrice: item.low,
        closePrice: item.close,
        volume: item.volume || 0
      }));
    }
    catch (error: any) {
      this.logger.error(error, JSON.stringify({
        instrument: this.parseInstrument(pair),
        timeframe: this.parseTimeframe(timeframe),
        dates: {
          from: dateFrom,
          to: dateTo,
        },
        format: "json",
        retryCount: 5,
        pauseBetweenRetriesMs: 500
      }));
      throw error;
    }
  }

  async getBatchHistoricalData(pair: string, timeframe: string, dateFrom: Date, dateTo: Date): Promise<Candle[]> {
    try {
      const config: Config = {
          instrument: this.parseInstrument(pair),
          timeframe: this.parseTimeframe(timeframe),
          dates: {
            from: dateFrom,
            to: dateTo,
          },
          format: "json",
          batchSize: 5,
          pauseBetweenBatchesMs: 1000,
          retryCount: 5,
          pauseBetweenRetriesMs: 500
        };
        
        const data = await getHistoricalRates(config) as JsonItem[];
        return data.map((item: JsonItem) => ({
          timestamp: item.timestamp,
          openPrice: item.open,
          highPrice: item.high,
          lowPrice: item.low,
          closePrice: item.close,
          volume: item.volume || 0
        }));
    }
    catch (error: any) {
      this.logger.error(error, JSON.stringify({
        instrument: this.parseInstrument(pair),
        timeframe: this.parseTimeframe(timeframe),
        dates: {
          from: dateFrom,
          to: dateTo,
        },
        format: "json",
        batchSize: 5,
        pauseBetweenBatchesMs: 1000,
        retryCount: 5,
        pauseBetweenRetriesMs: 500
      }));
      throw error;
    }
  }

  async getLiveData(pair: string, timeframe: string, numberOfCandles: number): Promise<Candle[]> {
    try {
      const data: JsonItem[] = await getRealTimeRates({
        instrument: this.parseInstrument(pair),
        timeframe: this.parseTimeframe(timeframe),
        format: Format.json,
        last: numberOfCandles,
      } as RealTimeRatesConfigJsonItem);
      
      return data.map((item: JsonItem) => ({
        timestamp: item.timestamp,
        openPrice: item.open,
        highPrice: item.high,
        lowPrice: item.low,
        closePrice: item.close,
        volume: item.volume || 0
      }));
    }
    catch (error: any) {
      this.logger.error(error, JSON.stringify({
        instrument: this.parseInstrument(pair),
        timeframe: this.parseTimeframe(timeframe),
        format: "json",
        last: numberOfCandles
      }));
      throw error;
    }
  }

  private parseInstrument(pair: string) : Instrument {
    if (Object.values(Instrument).includes(pair as Instrument)) {
      return pair as Instrument;
    }
    throw new Error(`Invalid instrument: ${pair}`);
  }

  private parseTimeframe(timeframe: string) : Timeframe {
    if (Object.values(Timeframe).includes(timeframe as Timeframe)) {
      return timeframe as Timeframe;
    }
    throw new Error(`Invalid timeframe: ${timeframe}`);
  }
}