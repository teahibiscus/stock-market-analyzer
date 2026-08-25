"use strict";

const path = require("node:path");

function buildWindowOptions(preloadPath) {
  return {
    width: 1440,
    height: 900,
    minWidth: 960,
    minHeight: 640,
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      preload: preloadPath,
    },
  };
}

function createWindowManager({
  BrowserWindow,
  frontendUrl,
  preloadPath = path.join(__dirname, "preload.cjs"),
}) {
  const trustedOrigin = new URL(frontendUrl).origin;
  const windows = new Set();

  function open(urlOrPath = "/") {
    const url = new URL(urlOrPath, frontendUrl);
    if (url.origin !== trustedOrigin) {
      throw new Error(`Untrusted window URL: ${url.toString()}`);
    }

    const window = new BrowserWindow(buildWindowOptions(preloadPath));
    windows.add(window);
    window.once("ready-to-show", () => window.show());
    window.on("closed", () => windows.delete(window));
    window.webContents.setWindowOpenHandler(({ url: childUrl }) => {
      if (new URL(childUrl).origin === trustedOrigin) {
        void open(childUrl);
      }
      return { action: "deny" };
    });
    window.webContents.on("will-navigate", (event, nextUrl) => {
      if (new URL(nextUrl).origin !== trustedOrigin) {
        event.preventDefault();
      }
    });

    return Promise.resolve(window.loadURL(url.toString())).then(() => window);
  }

  function openChart({ instrumentId, interval, period, volume }) {
    const url = new URL(
      `/chart/${encodeURIComponent(instrumentId)}`,
      frontendUrl,
    );
    url.searchParams.set("interval", interval);
    url.searchParams.set("period", period);
    url.searchParams.set("volume", volume ? "1" : "0");
    return open(url.toString());
  }

  return {
    count: () => windows.size,
    open,
    openChart,
  };
}

module.exports = { buildWindowOptions, createWindowManager };
