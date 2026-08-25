"use strict";

const { spawnSync } = require("node:child_process");

function terminateOwnedChild(
  child,
  { platform = process.platform, spawnSyncImpl = spawnSync } = {},
) {
  if (child.exitCode !== null) {
    return;
  }

  if (platform === "win32" && Number.isInteger(child.pid)) {
    spawnSyncImpl("taskkill", ["/pid", String(child.pid), "/T", "/F"], {
      stdio: "ignore",
      windowsHide: true,
    });
    return;
  }

  child.kill("SIGTERM");
}

module.exports = { terminateOwnedChild };
