import { LogLevel } from "../utils/loglevel.js";
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

//TODO: lettura da db
export class AppConfig {
    private static _nodeEnv: string;
    private static _logLevel: number;
    private static _isDatabaseLogEnabled: boolean;
    private static _startDateForDownloading: string; // la data di partenza per il download dei dati (ISO format)
    private static _databasePath: string; // il path del database (sqlite)
    private static _sleepBetweenHistoricalDataRequests: number; // il tempo di attesa tra le richieste di dati storici (in millisecondi)

    static initialize() {
        this._nodeEnv = 'development';
        this._logLevel = LogLevel.VERBOSE;
        this._isDatabaseLogEnabled = false;
        this._startDateForDownloading = "2019-10-01T00:00:00.000Z";
        this._sleepBetweenHistoricalDataRequests = 1000; // 1 secondo

        const __filename = fileURLToPath(import.meta.url);
        const __dirname = path.dirname(__filename);

        this._databasePath = process.env.DATABASE_PATH ?? path.join(__dirname, '..', '..', '..', '..', 'database', 'eurusd-data.db');

        if (!fs.existsSync(this._databasePath)) {
            throw new Error(`Database non trovato: ${this._databasePath}`);
        }
    }

    static nodeEnv() {
        return this._nodeEnv;
    }

    static logLevel() {
        return this._logLevel;
    }

    static isDatabaseLogEnabled() {
        return this._isDatabaseLogEnabled;
    }

    static startDateForDownloading() {
        return this._startDateForDownloading;
    }

    static databasePath() {
        return this._databasePath;
    }

    static sleepBetweenHistoricalDataRequests() {
        return this._sleepBetweenHistoricalDataRequests;
    }
}