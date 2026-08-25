const assert = require("node:assert/strict");
const test = require("node:test");

const {
  createWebProcessManager,
  resolveWebLaunch,
} = require("../src/webProcessManager.cjs");

test("uses the Next development server from the repository", () => {
  const launch = resolveWebLaunch({
    isPackaged: false,
    platform: "win32",
    projectRoot: "C:\\repo",
    environment: {},
  });

  assert.equal(launch.command, "npm.cmd");
  assert.deepEqual(launch.args, ["run", "dev", "--workspace", "frontend"]);
  assert.equal(launch.options.cwd, "C:\\repo");
});

test("uses the bundled standalone server when packaged", () => {
  const launch = resolveWebLaunch({
    isPackaged: true,
    platform: "win32",
    executablePath: "C:\\app\\StockMarketAnalyzer.exe",
    resourcesPath: "C:\\app\\resources",
    environment: {},
  });

  assert.equal(launch.command, "C:\\app\\StockMarketAnalyzer.exe");
  assert.deepEqual(launch.args, ["C:\\app\\resources\\frontend\\server.js"]);
  assert.equal(launch.options.env.ELECTRON_RUN_AS_NODE, "1");
  assert.equal(launch.options.env.PORT, "3000");
  assert.equal(launch.options.env.HOSTNAME, "127.0.0.1");
});

test("starts Next only when the frontend is unavailable", async () => {
  let checks = 0;
  let spawned = false;
  const child = { exitCode: null, kill: () => true };
  const manager = createWebProcessManager({
    fetchImpl: async () => ({ ok: ++checks > 1 }),
    spawnImpl: () => {
      spawned = true;
      return child;
    },
    sleepImpl: async () => {},
  });

  await manager.start();

  assert.equal(spawned, true);
  assert.equal(manager.ownsProcess(), true);
  manager.stop();
});
