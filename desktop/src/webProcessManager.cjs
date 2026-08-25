"use strict";

const path = require("node:path");
const { spawn } = require("node:child_process");
const { terminateOwnedChild } = require("./childProcess.cjs");

const DEFAULT_FRONTEND_URL = "http://127.0.0.1:3000";

function resolveWebLaunch({
  isPackaged,
  platform = process.platform,
  projectRoot = path.resolve(__dirname, "..", ".."),
  executablePath = process.execPath,
  resourcesPath = process.resourcesPath,
  environment = process.env,
}) {
  if (!isPackaged) {
    return {
      command: platform === "win32" ? "npm.cmd" : "npm",
      args: ["run", "dev", "--workspace", "frontend"],
      options: {
        cwd: projectRoot,
        env: environment,
        stdio: "inherit",
        windowsHide: true,
      },
    };
  }

  const serverPath =
    platform === "win32"
      ? path.win32.join(resourcesPath, "frontend", "server.js")
      : path.join(resourcesPath, "frontend", "server.js");
  return {
    command: executablePath,
    args: [serverPath],
    options: {
      cwd: path.dirname(serverPath),
      env: {
        ...environment,
        ELECTRON_RUN_AS_NODE: "1",
        HOSTNAME: "127.0.0.1",
        PORT: "3000",
      },
      stdio: "inherit",
      windowsHide: true,
    },
  };
}

function createWebProcessManager({
  frontendUrl = process.env.SMA_FRONTEND_URL ?? DEFAULT_FRONTEND_URL,
  isPackaged = false,
  launchOptions = {},
  spawnImpl = spawn,
  fetchImpl = globalThis.fetch,
  sleepImpl = (milliseconds) =>
    new Promise((resolve) => setTimeout(resolve, milliseconds)),
  nowImpl = Date.now,
  pollIntervalMs = 250,
  timeoutMs = 30_000,
} = {}) {
  const launch = resolveWebLaunch({ isPackaged, ...launchOptions });
  let child = null;

  async function isHealthy() {
    try {
      const response = await fetchImpl(frontendUrl, {
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

    child = spawnImpl(launch.command, launch.args, launch.options);
    const startedAt = nowImpl();

    while (true) {
      if (child?.exitCode !== null) {
        const exitCode = child?.exitCode;
        child = null;
        throw new Error(
          `Next.js exited before becoming healthy (code ${exitCode}).`,
        );
      }
      if (await isHealthy()) {
        return;
      }
      if (nowImpl() - startedAt >= timeoutMs) {
        stop();
        throw new Error(
          `Next.js did not become healthy within ${timeoutMs}ms.`,
        );
      }
      await sleepImpl(pollIntervalMs);
    }
  }

  return { ownsProcess, start, stop };
}

module.exports = { createWebProcessManager, resolveWebLaunch };
