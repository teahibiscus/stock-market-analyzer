"use strict";

const path = require("node:path");
const { createApiProcessManager } = require("./processManager.cjs");
const { createWebProcessManager } = require("./webProcessManager.cjs");
const { createWindowManager } = require("./windowManager.cjs");

const DEFAULT_FRONTEND_URL = "http://127.0.0.1:3000";

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

async function createMainWindow({
  BrowserWindow,
  frontendUrl = DEFAULT_FRONTEND_URL,
  preloadPath = path.join(__dirname, "preload.cjs"),
}) {
  const window = new BrowserWindow(buildWindowOptions(preloadPath));
  const trustedOrigin = new URL(frontendUrl).origin;

  window.once("ready-to-show", () => window.show());
  window.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  window.webContents.on("will-navigate", (event, url) => {
    if (new URL(url).origin !== trustedOrigin) {
      event.preventDefault();
    }
  });

  await window.loadURL(frontendUrl);
  return window;
}

async function bootstrapDesktop({
  app,
  BrowserWindow,
  apiManager,
  webManager,
  frontendUrl = DEFAULT_FRONTEND_URL,
  createWindow = (options) => createMainWindow(options),
}) {
  await apiManager.start();
  await webManager.start();
  await createWindow({ BrowserWindow, frontendUrl });

  app.on("activate", async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      await createWindow({ BrowserWindow, frontendUrl });
    }
  });

  app.on("before-quit", () => {
    webManager.stop();
    apiManager.stop();
  });
  app.on("window-all-closed", () => {
    if (process.platform !== "darwin") {
      app.quit();
    }
  });
}

async function runElectronApp() {
  const { app, BrowserWindow } = require("electron");
  const frontendUrl = process.env.SMA_FRONTEND_URL ?? DEFAULT_FRONTEND_URL;
  const apiManager = createApiProcessManager();
  const webManager = createWebProcessManager({
    frontendUrl,
    isPackaged: app.isPackaged,
  });
  const windowManager = createWindowManager({ BrowserWindow, frontendUrl });

  await app.whenReady();
  try {
    await bootstrapDesktop({
      app,
      BrowserWindow,
      apiManager,
      webManager,
      frontendUrl,
      createWindow: () => windowManager.open("/"),
    });
  } catch (error) {
    webManager.stop();
    apiManager.stop();
    console.error(error);
    app.quit();
  }
}

if (require.main === module) {
  void runElectronApp();
}

module.exports = {
  DEFAULT_FRONTEND_URL,
  bootstrapDesktop,
  buildWindowOptions,
  createMainWindow,
  runElectronApp,
};
