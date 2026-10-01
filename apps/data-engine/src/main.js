import "reflect-metadata";
import { container } from "./core/container.js";
import { EurUsdWorker } from "./workers/eurusd.worker.js";
console.log("[INFO]", "Starting worker...");
const worker = container.get(EurUsdWorker);
async function loop() {
    await worker.run();
    setTimeout(loop, 60 * 1000);
}
loop();
