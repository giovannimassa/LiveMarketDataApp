# Install PM2
npm install pm2 -g

# Set PM2 env vars
setx PM2_HOME "C:\Users\giova\.pm2"
setx PM2_NO_DAEMON "1"

# Create DB
python "..\database\eurusd_create_database.py"

# Start Node polling (every 5 minutes)
pm2 start "..\dukascopy-ticks\dist\main.js" --name forex-polling --cron "*/1 * * * *"

# Start Python signal engine (every 5 minutes)
pm2 start "..\signal-engine\signal_engine.py" --name signal-engine --cron "*/1 * * * *" --interpreter python3

# Install log rotation
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 30

Write-Host "PM2 services installed successfully."
