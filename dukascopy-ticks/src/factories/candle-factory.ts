import { MarketItem } from "../models/marketitem.model.js";
import { Candle } from "../services/marketdata.service.js";

export class CandleFactory {

    static createFromMarketItem(marketItem: MarketItem): Candle {
        return {
            closePrice: marketItem.closePrice,
            highPrice: marketItem.highPrice,
            lowPrice: marketItem.lowPrice,
            openPrice: marketItem.openPrice,
            timestamp: new Date(marketItem.timestamp).getMilliseconds(),
            volume: marketItem.volume
        };
    }
}