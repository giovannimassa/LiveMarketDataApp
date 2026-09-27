import { injectable } from "inversify";

export interface IPairConfig {
  symbol: string;
}

@injectable()
export class EurUsdConfig implements IPairConfig {
  symbol = "eurusd";
}