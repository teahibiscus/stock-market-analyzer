const assert = require("node:assert/strict");
const test = require("node:test");

const {
  createApiProcessManager,
  resolveApiLaunch,
} = require("../src/processManager.cjs");

test("resolves the repository Python API command", () => {
  assert.deepEqual(
    resolveApiLaunch({
      platform: "win32",
      projectRoot: "C:\\repo",
      environment: {},
    }),
    {
      command: "C:\\repo\\.venv\\Scripts\\python.exe",
      args: ["-m", "stock_market_analyzer.app.main"],
    },
  );
});

test("reuses an API that is already healthy", async () => {
  let spawned = false;
  const manager = createApiProcessManager({
    fetchImpl: async () => ({ ok: true }),
    spawnImpl: () => {
      spawned = true;
    },
  });

  await manager.start();

  assert.equal(spawned, false);
  assert.equal(manager.ownsProcess(), false);
});

test("spawns the API and waits until health succeeds", async () => {
  let attempts = 0;
  let launch;
  const child = {
    exitCode: null,
    kill: () => true,
    once: () => {},
  };
  const manager = createApiProcessManager({
    command: "python",
    args: ["-m", "stock_market_analyzer.app.main"],
    fetchImpl: async () => ({ ok: ++attempts >= 3 }),
    spawnImpl: (command, args, options) => {
      launch = { command, args, options };
      return child;
    },
    sleepImpl: async () => {},
    timeoutMs: 1_000,
  });

  await manager.start();

  assert.equal(attempts, 3);
  assert.equal(launch.command, "python");
  assert.deepEqual(launch.args, ["-m", "stock_market_analyzer.app.main"]);
  assert.equal(manager.ownsProcess(), true);
});

test("times out and stops the child when health never succeeds", async () => {
  let stopped = false;
  const child = {
    exitCode: null,
    kill: () => {
      stopped = true;
      return true;
    },
    once: () => {},
  };
  let now = 0;
  const manager = createApiProcessManager({
    fetchImpl: async () => {
      throw new Error("not ready");
    },
    spawnImpl: () => child,
    sleepImpl: async () => {
      now += 100;
    },
    nowImpl: () => now,
    timeoutMs: 200,
  });

  await assert.rejects(manager.start(), /did not become healthy/);
  assert.equal(stopped, true);
  assert.equal(manager.ownsProcess(), false);
});

test("stops only a child process owned by the shell", async () => {
  let stopCount = 0;
  const child = {
    exitCode: null,
    kill: () => {
      stopCount += 1;
      return true;
    },
    once: () => {},
  };
  let checks = 0;
  const manager = createApiProcessManager({
    fetchImpl: async () => ({ ok: ++checks > 1 }),
    spawnImpl: () => child,
    sleepImpl: async () => {},
    timeoutMs: 1_000,
  });

  await manager.start();
  manager.stop();
  manager.stop();

  assert.equal(stopCount, 1);
  assert.equal(manager.ownsProcess(), false);
});
