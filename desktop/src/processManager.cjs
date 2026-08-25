"use strict";

const path = require("node:path");
const { spawn } = require("node:child_process");
const { terminateOwnedChild } = require("./childProcess.cjs");

const DEFAULT_API_URL = "http://127.0.0.1:8000";

function resolveApiLaunch({
  platform = process.platform,
  projectRoot = path.resolve(__dirname, "..", ".."),
  environment = process.env,
} = {}) {
  const defaultPython =
    platform === "win32"
      ? path.win32.join(projectRoot, ".venv", "Scripts", "python.exe")
      : path.join(projectRoot, ".venv", "bin", "python");

  return {
    command: environment.SMA_PYTHON_EXECUTABLE ?? defaultPython,
    args: ["-m", "stock_market_analyzer.app.main"],
  };
}

function createApiProcessManager({
  apiUrl = process.env.SMA_API_URL ?? DEFAULT_API_URL,
  projectRoot = path.resolve(__dirname, "..", ".."),
  command,
  args,
  environment = process.env,
  spawnImpl = spawn,
  fetchImpl = globalThis.fetch,
  sleepImpl = (milliseconds) =>
    new Promise((resolve) => setTimeout(resolve, milliseconds)),
  nowImpl = Date.now,
  pollIntervalMs = 250,
  timeoutMs = 15_000,
} = {}) {
  const launch = resolveApiLaunch({ projectRoot, environment });
  const resolvedCommand = command ?? launch.command;
  const resolvedArgs = args ?? launch.args;
  const healthUrl = new URL("/health", apiUrl).toString();
  let child = null;

  async function isHealthy() {
    try {
      const response = await fetchImpl(healthUrl, {
        signal: AbortSignal.timeout(1_000),
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  function ownsProcess() {
    return child !== null;
  }

  function stop() {
    if (child === null) {
      return;
    }

    const ownedChild = child;
    child = null;
    terminateOwnedChild(ownedChild);
  }

  async function start() {
    if (await isHealthy()) {
      return;
    }

    child = spawnImpl(resolvedCommand, resolvedArgs, {
      cwd: projectRoot,
      env: environment,
      stdio: "inherit",
      windowsHide: true,
    });

    const startedAt = nowImpl();
    while (true) {
      if (child?.exitCode !== null) {
        const exitCode = child?.exitCode;
        child = null;
        throw new Error(
          `Local API exited before becoming healthy (code ${exitCode}).`,
        );
      }
      if (await isHealthy()) {
        return;
      }
      if (nowImpl() - startedAt >= timeoutMs) {
        stop();
        throw new Error(
          `Local API did not become healthy within ${timeoutMs}ms.`,
        );
      }
      await sleepImpl(pollIntervalMs);
    }
  }

  return { ownsProcess, start, stop };
}

module.exports = {
  DEFAULT_API_URL,
  createApiProcessManager,
  resolveApiLaunch,
};
