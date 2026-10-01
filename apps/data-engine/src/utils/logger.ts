import { injectable } from "inversify";
import { AppConfig } from "../config/app.config.js";
import { LogLevel } from "./loglevel.js";
import winston, { createLogger, format } from "winston";

@injectable()
export class Logger {

  private logger: winston.Logger;

  constructor() {
    const logFormat = format.printf(({ timestamp, level, message, stack, meta }) => {
      const metaString = meta ? `\n INPUT: ${JSON.stringify(meta, null, 2)}` : '';
      // const stackString = stack ? `\nSTACK TRACE:\n${stack}` : '';
      return `${timestamp} [${level.toUpperCase()}]: ${stack || message} ${metaString}`;
    });

    const logLevel = this.printLogLevel(this.getLogLevelConfig());

    this.logger = createLogger({
      level: logLevel,
      format: format.combine(
        format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
        format.errors({ stack: true }),
        // format.splat(),
        logFormat
      ),
      transports: [
        new winston.transports.Console({ level: 'verbose', forceConsole: true, handleExceptions: true }),
        new winston.transports.File({ filename: 'error.log', level: 'error', handleExceptions: true }),
        new winston.transports.File({ filename: 'info.log', level: 'info', handleExceptions: false }),
      ],
    });
  }

  private printLogLevel(logLevel: LogLevel): string {
    switch (logLevel) {
        case LogLevel.VERBOSE:
            return 'verbose';
        case LogLevel.INFO:
            return 'info';
        case LogLevel.WARN:
            return 'warn';
        case LogLevel.ERROR:
            return 'error';
        default:
            return 'info';
    }
  }

  private printLog(logLevel: LogLevel, ...msg: any): string {
    return `[${new Date().toISOString()}][${this.printLogLevel(logLevel)}] - ${msg}`;
  }

  private getLogLevelConfig(): LogLevel {
    const logLevel = AppConfig.logLevel() as LogLevel;
    return logLevel;
  }

  async verbose(...msg: any): Promise<void> {
    // const logLevel = this.getLogLevelConfig();
    // if (logLevel <= LogLevel.VERBOSE) {
    //   console.log(this.printLog(LogLevel.VERBOSE, msg));
    // }
    this.logger.verbose(msg);
  }

  async info(...msg: any): Promise<void> {
    // const logLevel = this.getLogLevelConfig();
    // if (logLevel <= LogLevel.INFO) {
    //   console.log(this.printLog(LogLevel.INFO, msg));
    // }
    this.logger.info(msg);
  }
  
  async warn(...msg: any): Promise<void> {
    // const logLevel = this.getLogLevelConfig();
    // if (logLevel <= LogLevel.WARN) {
    //   console.log(this.printLog(LogLevel.WARN, msg));
    // }
    this.logger.warn(msg);
  }

  async error(msg: any, errorInfo?: any): Promise<void> {
    // const logLevel = this.getLogLevelConfig();
    // if (logLevel <= LogLevel.ERROR) {
    //   console.log(this.printLog(LogLevel.ERROR, msg));
    // }
    this.logger.error(msg, { meta: errorInfo });
  }
}