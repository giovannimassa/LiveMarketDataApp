# LiveMarketDataApp
## Descrizione
App Node.js che calcola gli indicatori di dati di mercato live partendo da uno storico e salvando tutte le info in un DB. I dati di mercato vengono scaricati da **Duckascopy.com**.
Lo starting point dell'applicazione è il **main.js**.

## Services
I principali servizi di questa app sono:
- **TimeframeBase:** è il servizio core che consente di salvare e allineare il DB con i dati storici. Una volta allineato il DB parte in modalità live e calcola gli indicatori per i nuovi dati in ingresso tramite il metodo _calculateTimeframe()_. E' la classe che estenderanno tutti i timeframe dei quali si vuoi ottenere i dati.
- **AggregatorService:** servizio per l'aggregazione dei dati salvati su DB. I dati sono salvati su DB su differenti tabelle, il servizio recupera i dati da queste tabelle, li aggrega ottenendo un'unica informazione dei dati di mercato sui timeframe salvati e li salva in un file CSV. L'aggregazione "live" viene salvata invece su DB direttamente dal worker in esecuzione (es: eurusd.worker). Il dato aggregato live servirà per la predizione.
- **MarketDataService:** gestisce il download dei dati storici e live da Duckascopy.com

## Configuration
La classe **AppConfig** contiene le configurazione di tutta l'applicazione come il database path, log level, etc.

# Machine Learning (ML)
## Descrizione
Contiene gli script in Python per la creazione dei modelli di ML.

# Python Backtest Engine

# Python Signal Engine
## Descrizione
Il servizio che genera il segnale in base all'ultimo dato live dato in pasto al modello ML generato.
Principali caratteristiche:
- rimane in ascolto della tabella SQLite popolata dal tuo servizio Node.js
- rileva quando arriva una nuova candela live (con tutti gli indicatori già calcolati)
- costruisce il vettore delle feature
- carica i modelli LightGBM ATR‑only
- genera il segnale BUY/SELL/HOLD
- salva il trade nella tabella trades con mode='live'

## Architettura
loop infinito:
    leggi ultimo record da live_data
    se last_id > last_processed_id:
        costruisci feature vector
        predici con ensemble ATR
        se segnale != 0:
            salva trade in SQLite
    dormi 1 secondo

## Prerequisiti
- Tabella live_data popolata da Node.js
- Tabella trades con colonna mode
- Modelli LightGBM:
    - model_long_atr.txt
    - model_short_atr.txt

# Installazione
Utilizzeremo PM2 per gestire le applicazioni. Per installare PM2 avviare il seguente comando:
- npm install -g pm2
Il file **ecosystem.config.cjs** servirà come file di config di avvio delle app

# Comandi

Avviare le app con PM2:
- pm2 start ecosystem.config.cjs --no-daemon

Cancellare le app registrate su PM2:
- pm2 delete all

Visualizzare la lista delle app in running:
- pm2 list

# #############################################
# ##### MODIFICHE App Trading Algoritmico #####
# #############################################

1. Individuare e calcolare gli indicatori che non hanno bisogno di storico per il calcolo ma basta il prezzo corrente (no EMA per esempio).
2. Chiedere ad AI quali indicatori, in base a quelli individuati, vanno bene per l'algoritmo scelto (per il momento LightLGB) e se bisogna integrare/rimuovere alcuni o cambiare algoritmo.
3. Migliorare la predizione ML. Capire come fare fine tuning dei parametri dell'algoritmo in base ai dati di traning idividuati.
4. Utilizzo e collegamento ai dati di Metatrader5 invece che Duckascopy. Capire se è la strada giusta oppure trovare un provider diverso. Vedere se si può testare utilizzando API e se sia necessario aprire un conto demo.
5. Chiedere quali statistiche sono utili per il backtesting e aggiungerle allo script.
6. Creare una web app (capire se node va bene o altro linguaggio) per vedere graficamente le statistiche del backtesting.
7. Aggiungere all'app la possibilità di live trading