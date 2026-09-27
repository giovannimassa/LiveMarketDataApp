#### Configurazione PM2 ####

PM2 è il process manager più usato per mantenere script Node.js sempre attivi, con restart automatico e gestione log integrata.

# Insallazione PM2

- Installa PM2 globalmente

npm install -g pm2

- Avvia lo script (nel nostro caso index.js)

pm2 start app.js --name dukas

--name dukas ci permette di dare un nome al processo.

# Gestione log

PM2 crea automaticamente due file di log:

~/.pm2/logs/dukas-out.log → output standard (console.log).
~/.pm2/logs/dukas-error.log → errori.

Possiamo visualizzarli in tempo reale con:

pm2 logs dukas

# Restart automatico

Se lo script crasha, PM2 lo riavvia da solo. Puoi anche impostare il restart ad ogni reboot del sistema:

pm2 save
pm2 startup

Questo genera un comando da eseguire una volta, che registra PM2 come servizio di sistema.

# Comandi utili

Lista processi:
pm2 list

Stop processo:
pm2 stop dukas

Riavvio:
pm2 restart dukas

Rimozione:
pm2 delete dukas