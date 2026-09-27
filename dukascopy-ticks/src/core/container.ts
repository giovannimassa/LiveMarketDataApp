import "reflect-metadata";
import { Container } from "inversify";

import { MarketDataService } from "../services/marketdata.service.js";
import { EurUsdWorker } from "../workers/eurusd.worker.js";
import { Logger } from "../utils/logger.js";
import { DateHelper } from "../utils/dateHelper.js";
import { DatabaseService } from "../database/database.service.js";
import { IndicatorService } from "../services/indicator.service.js";
import { IPairConfig } from "../config/pair.config.js";
import { TYPES } from "./types.js";
import { TestWorker } from "../workers/test.worker.js";
import { Timeframe5minService } from "../timeframes/timeframe5min.service.js";
import { Timeframe15minService } from "../timeframes/timeframe15min.service.js";
import { Timeframe1HourService } from "../timeframes/timeframe1hour.service.js";
import { AggregatorService } from "../services/aggregator.services.js";
import { LabelClassificationService } from "../services/label-classification.service.js";

const baseContainer = new Container();

baseContainer.bind(MarketDataService).toSelf().inSingletonScope();
baseContainer.bind(Logger).toSelf().inSingletonScope();
baseContainer.bind(DateHelper).toSelf().inSingletonScope();
baseContainer.bind(DatabaseService).toSelf().inSingletonScope();
baseContainer.bind(Timeframe5minService).toSelf().inSingletonScope();
baseContainer.bind(Timeframe15minService).toSelf().inSingletonScope();
baseContainer.bind(Timeframe1HourService).toSelf().inSingletonScope();
baseContainer.bind(IndicatorService).toSelf().inSingletonScope();
baseContainer.bind(AggregatorService).toSelf().inSingletonScope();
baseContainer.bind(LabelClassificationService).toSelf().inSingletonScope();


const eurusdContainer = new Container();
eurusdContainer.parent = baseContainer;

eurusdContainer.bind(EurUsdWorker).toSelf().inSingletonScope();
eurusdContainer.bind<IPairConfig>(TYPES.PairConfig).toConstantValue({
    symbol: "eurusd",
});

const testContainer = new Container();
testContainer.parent = baseContainer;

testContainer.bind(TestWorker).toSelf().inSingletonScope();
testContainer.bind<IPairConfig>(TYPES.PairConfig).toConstantValue({
    symbol: "eurusd",
});

export { baseContainer, eurusdContainer, testContainer };