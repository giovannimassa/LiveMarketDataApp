import { Timeframe } from "dukascopy-node";
import { TimeframeBase } from "./timeframe-base.js";

export class Timeframe1HourService extends TimeframeBase {
    timeframe(): Timeframe {
        return Timeframe.h1;
    }
}