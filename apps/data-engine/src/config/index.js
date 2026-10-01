const fs = require('fs');
const path = require('path');
const { getRealTimeRates } = require('dukascopy-node');

const CSV_FILE = path.join(__dirname, 'data.csv');
const ERROR_LOG_FILE = path.join(__dirname, 'error.log');

async function fetchCandles() {
  try {
    const now = new Date();
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);

    // Get real-time rates for EUR/USD, 1-minute timeframe, last candle only
    const data = await getRealTimeRates({
      instrument: 'eurusd',
      // dates: { from: oneHourAgo, to: now },
      timeframe: 'm1',
      format: 'json',
	    last: 1
    });

    if (!data || data.length === 0) return;

    // Prendi l’ultima candela
    const lastCandle = data[0];
    const newRow = `${new Date(lastCandle.timestamp).toISOString()},${lastCandle.open},${lastCandle.high},${lastCandle.low},${lastCandle.close},${lastCandle.volume}`;

    // Controlla ultima riga del CSV
    let lastRow = null;
    let lines = [];
    if (fs.existsSync(CSV_FILE)) {
      lines = fs.readFileSync(CSV_FILE, 'utf8').trim().split('\n');
      lastRow = lines[lines.length - 1];
    }

    if (lastRow !== newRow) {
      if (lines.length == 0) {
        fs.appendFileSync(CSV_FILE, newRow);
      }
      else {
        fs.appendFileSync(CSV_FILE, '\n' + newRow);
        //console.log('Nuova candela aggiunta:', newRow);
      }
    } else {
      //console.log('Candela già presente, nessun inserimento.');
	  
	  if (lines.length > 500) {
        const trimmed = lines.slice(lines.length - 500); // mantieni ultime 500
        fs.writeFileSync(CSV_FILE, trimmed.join('\n') + '\n');
        //console.log(`File CSV ridotto a ${trimmed.length} righe (vecchie cancellate).`);
      }
    }
  } catch (err) {
    console.error('Errore:', err.message);
    fs.appendFileSync(ERROR_LOG_FILE, `[${new Date().toISOString()}] ${err.stack}\n`);
  }
}

// Polling ogni 5 minuti
setInterval(fetchCandles, 10 * 1000);

// Avvio immediato
// fetchCandles();