import { inject, injectable } from "inversify";
import { Logger } from "../utils/logger.js";
import { DateHelper } from "../utils/dateHelper.js";
import { Candle } from "./marketdata.service.js";
import { Sma } from "../indicators/sma.js";
import { EMA } from "../indicators/ema.js";
import { BollingerBands } from "../indicators/bbands.js";
import { RSI } from "../indicators/rsi.js";
import { MACD, MacdAtrNormalized } from "../indicators/macd.js";
import { ATR } from "../indicators/atr.js";
import { SlopeEMA } from "../indicators/slope-ema.js";
import { DistanceEMA } from "../indicators/distance-ema.js";
import { ROC } from "../indicators/roc.js";
import { Stochastic } from "../indicators/stochastic.js";
import { OBV } from "../indicators/obv.js";
import { VolumeZScore } from "../indicators/volume-zscore.js";
import { VolumeAtrRatio } from "../indicators/volume-atr-ratio.js";
import { FVG, FvgSizeNormalized } from "../indicators/fvg.js";
import { LogReturn } from "../indicators/log-return.js";
import { RollingVolatility } from "../indicators/rolling-volatility.js";
import { RollingVolatilityAtrNormalized, RollingVolatilitySlope } from "../indicators/rolling-volatility-extended.js";
import { BodySizePercentage } from "../indicators/body-size-percentage.js";
import { UpperWickPercentage } from "../indicators/upper-wick-percentage.js";
import { LowerWickPercentage } from "../indicators/lower-wick-percentage.js";
import { RangeExpansion } from "../indicators/range-expansion.js";
import { CandleFactory } from "../factories/candle-factory.js";
import { MarketItem } from "../models/marketitem.model.js";
import { MarketItemFactory } from "../factories/marketitemtf5min.factory.js";

@injectable()
export class IndicatorService {

    private sma20!: Sma;
    private sma50!: Sma;
    private ema20!: EMA;
    private ema50!: EMA;
    private ema100!: EMA;
    private ema200!: EMA;
    private bbands20!: BollingerBands;
    private rsi14!: RSI;
    private atr14!: ATR;
    private macd!: MACD;
    private macdNorm!: MacdAtrNormalized;
    private slopeEma!: SlopeEMA;
    private distanceEma!: DistanceEMA;
    private roc!: ROC;
    private stoch!: Stochastic;
    private obv!: OBV;
    private volumeZScore!: VolumeZScore;
    private volumeAtrRatio!: VolumeAtrRatio;
    private fvg!: FVG;
    private fvgSizeAtrNorm!: FvgSizeNormalized;
    private bodySizePerc!: BodySizePercentage;
    private upperWickPerc!: UpperWickPercentage;
    private lowerWickPerc!: LowerWickPercentage;
    private rangeExp!: RangeExpansion;
    private logReturn!: LogReturn;
    private rollingVolatility!: RollingVolatility;
    private rollingVolatilityAtrNorm!: RollingVolatilityAtrNormalized;
    private rollingVolatilitySlope!: RollingVolatilitySlope;

    constructor(
        @inject(Logger) private logger: Logger,
        @inject(DateHelper) private dateHelper: DateHelper,
    ) {
        this.initIndicators();
    }

    private initIndicators() {
        this.sma20 = new Sma(20);
        this.sma50 = new Sma(50);
        this.ema20 = new EMA(20);
        this.ema50 = new EMA(50);
        this.ema100 = new EMA(100);
        this.ema200 = new EMA(200);
        this.bbands20 = new BollingerBands(20, 2);
        this.rsi14 = new RSI(14);
        this.atr14 = new ATR(14);
        this.macd = new MACD(12, 26, 9)
        this.macdNorm = new MacdAtrNormalized();
        this.slopeEma = new SlopeEMA(20, 10);
        this.distanceEma = new DistanceEMA(20);
        this.roc = new ROC(10);
        this.stoch = new Stochastic(14, 3, 3);
        this.obv = new OBV();
        this.volumeZScore = new VolumeZScore(20);
        this.volumeAtrRatio = new VolumeAtrRatio();
        this.fvg = new FVG();
        this.fvgSizeAtrNorm = new FvgSizeNormalized();
        this.bodySizePerc = new BodySizePercentage();
        this.upperWickPerc = new UpperWickPercentage();
        this.lowerWickPerc = new LowerWickPercentage();
        this.rangeExp = new RangeExpansion();
        this.logReturn = new LogReturn();
        this.rollingVolatility = new RollingVolatility(20);
        this.rollingVolatilityAtrNorm = new RollingVolatilityAtrNormalized(20, 14);
        this.rollingVolatilitySlope = new RollingVolatilitySlope(20, 10);
    }

    // Inizializza gli indicatori partendo da valori già calcolati
    fill(marketItems : MarketItem[]) {
        
        // if (marketItems.length < this.minFillValuesNumber) {
        //     throw new Error(`Number of values used for filling are less than ${this.minFillValuesNumber}`);
        // }

        const allCandleList = marketItems.map(item => CandleFactory.createFromMarketItem(item));
        const allClosePriceList = marketItems.map(item => item.closePrice);
        
        this.ema20.fill(allClosePriceList.slice(1), marketItems.map(item => item.ema20)[0]);
        this.ema50.fill(allClosePriceList.slice(1), marketItems.map(item => item.ema50)[0]);
        this.ema100.fill(allClosePriceList.slice(1), marketItems.map(item => item.ema100)[0]);
        this.ema200.fill(allClosePriceList.slice(1), marketItems.map(item => item.ema200)[0]);
        
        this.atr14.fill(allCandleList.slice(1), marketItems.map(item => item.atr14)[0], allClosePriceList[0]);

        this.bbands20.fill(allClosePriceList);

        this.distanceEma.fill(allClosePriceList.slice(1), marketItems.map(item => item.ema20)[0]);
        this.fvg.fill(allCandleList);
        this.logReturn.fill(allClosePriceList.slice(1), allClosePriceList[0]);

        this.macd.fill(
            allClosePriceList.slice(1),
            marketItems.map(item => item.macdFast)[0],
            marketItems.map(item => item.macdSlow)[0],
            marketItems.map(item => item.macdSignal)[0]
        );

        this.obv.fill(allCandleList.slice(1), marketItems.map(item => item.obv)[0], allClosePriceList[0]);

        this.rangeExp.fill(allCandleList.slice(1), allCandleList[0]);

        this.roc.fill(allClosePriceList);

        this.rollingVolatility.fill(allClosePriceList);
        this.rollingVolatilityAtrNorm.fill(allCandleList.slice(1), allClosePriceList.slice(1), marketItems.map(item => item.atr14)[0], allClosePriceList[0]);
        this.rollingVolatilitySlope.fill(allClosePriceList);

        this.rsi14.fill(allClosePriceList);

        this.slopeEma.fill(allCandleList.slice(1), marketItems.map(item => item.ema20)[0]);

        this.sma20.fill(allClosePriceList);
        this.sma50.fill(allClosePriceList);

        this.stoch.fill(allCandleList);
    }

    // Calcola e assegna il nuovo valore degli indicatori
    next(candle: Candle): MarketItem {
        let newMarketItem = MarketItemFactory.createFromMarketItem(
            this.dateHelper.convertToISOString(candle.timestamp), 
            candle.openPrice,
            candle.highPrice,
            candle.lowPrice,
            candle.closePrice,
            candle.volume || 0
        );

        newMarketItem.sma20 = this.sma20.next(candle.closePrice);
        newMarketItem.sma50 = this.sma50.next(candle.closePrice);
        newMarketItem.ema20 = this.ema20.next(candle.closePrice);
        newMarketItem.ema50 = this.ema50.next(candle.closePrice);
        newMarketItem.ema100 = this.ema100.next(candle.closePrice);
        newMarketItem.ema200 = this.ema200.next(candle.closePrice);
        newMarketItem.bbands20 = this.bbands20.next(candle.closePrice)?.middle;
        newMarketItem.rsi14 = this.rsi14.next(candle.closePrice);
        newMarketItem.atr14 = this.atr14.next(candle);
        
        var macd = this.macd.next(candle.closePrice);
        newMarketItem.macdFast = macd?.fast;
        newMarketItem.macdSlow = macd?.slow;
        newMarketItem.macdSignal = macd?.signal;
        newMarketItem.macdNorm = this.macdNorm.next(macd?.histogram, newMarketItem.atr14);
        
        newMarketItem.slopeEma = this.slopeEma.next(candle.closePrice);
        newMarketItem.distanceEma = this.distanceEma.next(candle.closePrice);
        newMarketItem.roc = this.roc.next(candle.closePrice);
        newMarketItem.stoch = this.stoch.next(candle)?.k;
        newMarketItem.obv = this.obv.next(candle);
        newMarketItem.volumeZScore = this.volumeZScore.next(candle);
        newMarketItem.volumeAtrRatio = this.volumeAtrRatio.next(candle, newMarketItem.atr14);
        var fvgValue = this.fvg.next(candle);
        newMarketItem.fvgBullish = fvgValue?.isBullish ? 1 : 0;
        newMarketItem.fvgBearish = fvgValue?.isBearish ? 1 : 0;
        newMarketItem.fvgSize = fvgValue?.size;
        newMarketItem.fvgSizeAtrNorm = this.fvgSizeAtrNorm.next(newMarketItem.fvgSize, newMarketItem.atr14);
        newMarketItem.bodySizePerc = this.bodySizePerc.next(candle);
        newMarketItem.upperWickPerc = this.upperWickPerc.next(candle);
        newMarketItem.lowerWickPerc = this.lowerWickPerc.next(candle);
        newMarketItem.rangeExp = this.rangeExp.next(candle);
        newMarketItem.logReturn = this.logReturn.next(candle.closePrice);
        newMarketItem.rollingVolatility = this.rollingVolatility.next(newMarketItem.logReturn);
        newMarketItem.rollingVolatilityAtrNorm = this.rollingVolatilityAtrNorm.next(candle, newMarketItem.logReturn);
        newMarketItem.rollingVolatilitySlope = this.rollingVolatilitySlope.next(newMarketItem.logReturn);

        return newMarketItem;
    }

    isValid(marketItem: MarketItem): boolean {

        return true;
    }
}