module.exports = {
  apps: [
    {
      name: "financial-data-polling",
      script: ".\\apps\\data-engine\\dist\\main.js",
      //cron_restart: "*/1 * * * *",
      watch: false,
      autorestart: true,
      env: {
        PM2_NO_DAEMON: "1"
      }
    },
    {
      name: "signal-engine",
      script: ".\\apps\\signal-engine\\signal_engine.py",
      interpreter: process.env.PYTHON_INTERPRETER || "python",
      //cron_restart: "*/5 * * * * *", // Restart every 5 seconds
      watch: false,
      autorestart: true,
      env: {
        PM2_NO_DAEMON: "1"
      }
    }
  ]
};
