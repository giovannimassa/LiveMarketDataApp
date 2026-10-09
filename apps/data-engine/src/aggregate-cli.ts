import "reflect-metadata";
import { eurusdContainer } from "./core/container.js";
import { AppConfig } from "./config/app.config.js";
import { AggregationDataFor, AggregationTo, AggregatorService } from "./services/aggregator.services.js";

// Uso: node dist/aggregate-cli.js <timestampStart> <timestampEnd> <outputCsv>
// Genera sempre le label (modalita' training), come i CSV usati da ml/.
const [start, end, output] = process.argv.slice(2);
if (!start || !end || !output) {
    throw new Error("Uso: node dist/aggregate-cli.js <timestampStart> <timestampEnd> <outputCsv>");
}

AppConfig.initialize();
const aggregator = eurusdContainer.get(AggregatorService);
aggregator.aggregate(start, end, AggregationTo.CSV, AggregationDataFor.TRAINING, output);
