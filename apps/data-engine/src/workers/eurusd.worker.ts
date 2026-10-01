import { inject, injectable } from 'inversify';
import { Logger } from '../utils/logger.js';
import { Timeframe5minService } from '../timeframes/timeframe5min.service.js';
import { Timeframe15minService } from '../timeframes/timeframe15min.service.js';
import { Timeframe1HourService } from '../timeframes/timeframe1hour.service.js';
import { Stopwatch } from '../utils/stopwatch.js';
import { DatabaseService } from '../database/database.service.js';
import { MarketItem } from '../models/marketitem.model.js';
import { Timeframe } from 'dukascopy-node';

@injectable()
export class EurUsdWorker {
  
  constructor(
    @inject(Logger) private logger: Logger,
    @inject(DatabaseService) private database: DatabaseService,
    @inject(Timeframe5minService) private timeframe5minService: Timeframe5minService,
    @inject(Timeframe15minService) private timeframe15minService: Timeframe15minService,
    @inject(Timeframe1HourService) private timeframe1HourService: Timeframe1HourService,
  ) {}
  
  async run(): Promise<number> {
    this.logger.info(`[EurUsdWorker] - worker run...`);
    
    const stopWatch = new Stopwatch();
    stopWatch.start();

    const results = Promise.all([
      this.timeframe5minService.calculateTimeframe(),
      this.timeframe15minService.calculateTimeframe(),
      this.timeframe1HourService.calculateTimeframe()
    ]);

    const timeframe5Min = (await results)[0];
    const timeframe15Min = (await results)[1];
    const timeframe1Hour = (await results)[2];

    const lastSaved = this.database.getLastAggregateData();
    this.logger.info(`[EurUsdWorker] - ultimo timestamp: ${lastSaved?.timestamp_m5}, live tf m5 timestamp: ${timeframe5Min?.timestamp}`);
    // Controllo se il timestamp del timeframe a 5 minuti è cambiato rispetto all'ultimo salvataggio.
    if (lastSaved?.timestamp_m5 !== timeframe5Min?.timestamp) {
      // Salva l'ultimo dato live come aggregato nel database.
      // Questo permette di avere un record unico con i dati dei vari timeframe, utile per l'analisi e/o predizione.
      this.saveAggregateData(timeframe5Min, timeframe15Min, timeframe1Hour);
    }

    stopWatch.stop();
    this.logger.info(`[EurUsdWorker] - worker completed in ${stopWatch.formatted()}!`);
    return 0;
  }

  private saveAggregateData(tf5Min: MarketItem | undefined, tf15Min: MarketItem | undefined, tf1Hour: MarketItem | undefined ) {
    try {
      const m5Date = tf5Min?.timestamp;
      const m15Date = tf15Min?.timestamp;
      const h1Date = tf1Hour?.timestamp;

      this.logger.verbose(`[EurUsdWorker] - saveAggregateData - m5Date: ${m5Date}, m15Date: ${m15Date}, h1Date: ${h1Date}`);
  
      // Salvo i dati aggregati solo se ho il dato calcolato per tutti e tre i timeframe
      if (m5Date && m15Date && h1Date) {
        this.database.saveAggregateData({
          timestamp_m5: tf5Min?.timestamp,
          open_m5: tf5Min?.openPrice,
          close_m5: tf5Min?.closePrice,
          high_m5: tf5Min?.highPrice,
          low_m5: tf5Min?.lowPrice,
          volume_m5: tf5Min?.volume?.toString(),
          sma20_m5: tf5Min?.sma20?.toFixed(5),
          sma50_m5: tf5Min?.sma50?.toFixed(5),
          ema20_m5: tf5Min?.ema20?.toFixed(5),
          ema50_m5: tf5Min?.ema50?.toFixed(5),
          ema100_m5: tf5Min?.ema100?.toFixed(5),
          ema200_m5: tf5Min?.ema200?.toFixed(5),
          bbands20_m5: tf5Min?.bbands20?.toFixed(5),
          rsi14_m5: tf5Min?.rsi14?.toFixed(2),
          atr14_m5: tf5Min?.atr14?.toFixed(6),
          macdNorm_m5: tf5Min?.macdNorm?.toFixed(6),
          slopeEma_m5: tf5Min?.slopeEma?.toFixed(8),
          distanceEma_m5: tf5Min?.distanceEma?.toFixed(6),
          roc_m5: tf5Min?.roc?.toFixed(4),
          stoch_m5: tf5Min?.stoch?.toFixed(2),
          obv_m5: tf5Min?.obv?.toFixed(2),
          volumeZScore_m5: tf5Min?.volumeZScore?.toFixed(4),
          volumeAtrRatio_m5: tf5Min?.volumeAtrRatio?.toFixed(6),
          fvgBullish_m5: tf5Min?.fvgBullish?.toFixed(5),
          fvgBearish_m5: tf5Min?.fvgBearish?.toFixed(5),
          fvgSize_m5: tf5Min?.fvgSize?.toFixed(6),
          fvgSizeAtrNorm_m5: tf5Min?.fvgSizeAtrNorm?.toFixed(6),
          bodySizePerc_m5: tf5Min?.bodySizePerc?.toFixed(2),
          upperWickPerc_m5: tf5Min?.upperWickPerc?.toFixed(2),
          lowerWickPerc_m5: tf5Min?.lowerWickPerc?.toFixed(2),
          rangeExp_m5: tf5Min?.rangeExp?.toFixed(3),
          logReturn_m5: tf5Min?.logReturn?.toFixed(8),
          rollingVolatility_m5: tf5Min?.rollingVolatility?.toFixed(6),
          rollingVolatilityAtrNorm_m5: tf5Min?.rollingVolatilityAtrNorm?.toFixed(6),
          rollingVolatilitySlope_m5: tf5Min?.rollingVolatilitySlope?.toFixed(8),
          sma20_m15: tf15Min?.sma20?.toFixed(5),
          sma50_m15: tf15Min?.sma50?.toFixed(5),
          ema20_m15: tf15Min?.ema20?.toFixed(5),
          ema50_m15: tf15Min?.ema50?.toFixed(5),
          ema100_m15: tf15Min?.ema100?.toFixed(5),
          ema200_m15: tf15Min?.ema200?.toFixed(5),
          bbands20_m15: tf15Min?.bbands20?.toFixed(5),
          rsi14_m15: tf15Min?.rsi14?.toFixed(2),
          atr14_m15: tf15Min?.atr14?.toFixed(6),
          macdNorm_m15: tf15Min?.macdNorm?.toFixed(6),
          slopeEma_m15: tf15Min?.slopeEma?.toFixed(8),
          distanceEma_m15: tf15Min?.distanceEma?.toFixed(6),
          roc_m15: tf15Min?.roc?.toFixed(4),
          stoch_m15: tf15Min?.stoch?.toFixed(2),
          obv_m15: tf15Min?.obv?.toFixed(2),
          volumeZScore_m15: tf15Min?.volumeZScore?.toFixed(4),
          volumeAtrRatio_m15: tf15Min?.volumeAtrRatio?.toFixed(6),
          fvgBullish_m15: tf15Min?.fvgBullish?.toString(),
          fvgBearish_m15: tf15Min?.fvgBearish?.toString(),
          fvgSize_m15: tf15Min?.fvgSize?.toFixed(6),
          fvgSizeAtrNorm_m15: tf15Min?.fvgSizeAtrNorm?.toFixed(6),
          bodySizePerc_m15: tf15Min?.bodySizePerc?.toFixed(2),
          upperWickPerc_m15: tf15Min?.upperWickPerc?.toFixed(2),
          lowerWickPerc_m15: tf15Min?.lowerWickPerc?.toFixed(2),
          rangeExp_m15: tf15Min?.rangeExp?.toFixed(3),
          logReturn_m15: tf15Min?.logReturn?.toFixed(8),
          rollingVolatility_m15: tf15Min?.rollingVolatility?.toFixed(6),
          rollingVolatilityAtrNorm_m15: tf15Min?.rollingVolatilityAtrNorm?.toFixed(6),
          rollingVolatilitySlope_m15: tf15Min?.rollingVolatilitySlope?.toFixed(8),
          sma20_h1: tf1Hour?.sma20?.toFixed(5),
          sma50_h1: tf1Hour?.sma50?.toFixed(5),
          ema20_h1: tf1Hour?.ema20?.toFixed(5),
          ema50_h1: tf1Hour?.ema50?.toFixed(5),
          ema100_h1: tf1Hour?.ema100?.toFixed(5),
          ema200_h1: tf1Hour?.ema200?.toFixed(5),
          bbands20_h1: tf1Hour?.bbands20?.toFixed(5),
          rsi14_h1: tf1Hour?.rsi14?.toFixed(2),
          atr14_h1: tf1Hour?.atr14?.toFixed(6),
          macdNorm_h1: tf1Hour?.macdNorm?.toFixed(6),
          slopeEma_h1: tf1Hour?.slopeEma?.toFixed(8),
          distanceEma_h1: tf1Hour?.distanceEma?.toFixed(6),
          roc_h1: tf1Hour?.roc?.toFixed(4),
          stoch_h1: tf1Hour?.stoch?.toFixed(2),
          obv_h1: tf1Hour?.obv?.toFixed(2),
          volumeZScore_h1: tf1Hour?.volumeZScore?.toFixed(4),
          volumeAtrRatio_h1: tf1Hour?.volumeAtrRatio?.toFixed(6),
          fvgBullish_h1: tf1Hour?.fvgBullish?.toFixed(5),
          fvgBearish_h1: tf1Hour?.fvgBearish?.toFixed(5),
          fvgSize_h1: tf1Hour?.fvgSize?.toFixed(6),
          fvgSizeAtrNorm_h1: tf1Hour?.fvgSizeAtrNorm?.toFixed(6),
          bodySizePerc_h1: tf1Hour?.bodySizePerc?.toFixed(2),
          upperWickPerc_h1: tf1Hour?.upperWickPerc?.toFixed(2),
          lowerWickPerc_h1: tf1Hour?.lowerWickPerc?.toFixed(2),
          rangeExp_h1: tf1Hour?.rangeExp?.toFixed(3),
          logReturn_h1: tf1Hour?.logReturn?.toFixed(8),
          rollingVolatility_h1: tf1Hour?.rollingVolatility?.toFixed(6),
          rollingVolatilityAtrNorm_h1: tf1Hour?.rollingVolatilityAtrNorm?.toFixed(6),
          rollingVolatilitySlope_h1: tf1Hour?.rollingVolatilitySlope?.toFixed(8)
        });
      }
    }
    catch (error: any) {
      this.logger.error(error, { method: "saveAggregateData" });
    }
  }
}