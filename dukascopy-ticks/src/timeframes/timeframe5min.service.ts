import { Timeframe } from "dukascopy-node";
import { TimeframeBase } from "./timeframe-base.js";

export class Timeframe5minService extends TimeframeBase {
    timeframe(): Timeframe {
        return Timeframe.m5;
    }
}