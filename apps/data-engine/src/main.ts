import "reflect-metadata";
import { EurUsdWorker } from "./workers/eurusd.worker.js";
import { baseContainer, eurusdContainer, testContainer } from "./core/container.js";
import { Logger } from "./utils/logger.js";
import { AppConfig } from "./config/app.config.js";
import { TestWorker } from "./workers/test.worker.js";
import { AggregatorService } from "./services/aggregator.services.js";

AppConfig.initialize();

const testWorker = testContainer.get(TestWorker);
const logger = baseContainer.get(Logger);
const worker = eurusdContainer.get(EurUsdWorker);
const aggregator = baseContainer.get(AggregatorService);


async function loop() {
  logger.info("Starting worker ...");
  const result = await worker.run();
  const seconds = 5;
  logger.info(`Worker execution completed with result: ${result}. Next execution in ${seconds} seconds...`);
  setTimeout(loop, seconds * 1000);
}


await loop();
//await worker.run();
//await testWorker.test();
// aggregator.aggregate(
//   "2025-01-01T00:00:00Z",
//   "2026-05-31T23:59:59Z",
//   AggregationTo.CSV,
//   AggregationDataFor.TRAINING
// );