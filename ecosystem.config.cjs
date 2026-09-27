module.exports = {
  apps: [
    {
      name: "financial-data-polling",
      script: ".\\dukascopy-ticks\\dist\\main.js",
      //cron_restart: "*/1 * * * *",
      watch: false,
      autorestart: true,
      env: {
        PM2_NO_DAEMON: "1"
      }
    },
    {
      name: "signal-engine",
      script: ".\\signal-engine\\signal_engine.py",
      interpreter: "C:\\Users\\giova\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
      //cron_restart: "*/5 * * * * *", // Restart every 5 seconds
      watch: false,
      autorestart: true,
      env: {
        PM2_NO_DAEMON: "1"
      }
    }
  ]
};
