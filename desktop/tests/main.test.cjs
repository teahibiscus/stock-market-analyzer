const assert = require("node:assert/strict");
const test = require("node:test");

const {
  DEFAULT_FRONTEND_URL,
  bootstrapDesktop,
  buildWindowOptions,
  createMainWindow,
} = require("../src/main.cjs");

test("uses the local Next.js development URL by default", () => {
  assert.equal(DEFAULT_FRONTEND_URL, "http://127.0.0.1:3000");
});

test("creates a hardened desktop renderer", () => {
  const options = buildWindowOptions("C:\\app\\preload.cjs");

  assert.equal(options.show, false);
  assert.equal(options.webPreferences.contextIsolation, true);
  assert.equal(options.webPreferences.nodeIntegration, false);
  assert.equal(options.webPreferences.sandbox, true);
  assert.equal(options.webPreferences.preload, "C:\\app\\preload.cjs");
});

test("loads the frontend and reveals the window when ready", async () => {
  const events = new Map();
  const handlers = {};

  class FakeBrowserWindow {
    constructor(options) {
      this.options = options;
      this.webContents = {
        on: (event, handler) => {
          handlers[event] = handler;
        },
        setWindowOpenHandler: (handler) => {
          handlers.windowOpen = handler;
        },
      };
    }

    once(event, handler) {
      events.set(event, handler);
    }

    async loadURL(url) {
      this.loadedUrl = url;
    }

    show() {
      this.shown = true;
    }
  }

  const window = await createMainWindow({
    BrowserWindow: FakeBrowserWindow,
    frontendUrl: "http://127.0.0.1:3000/chart/1",
    preloadPath: "C:\\app\\preload.cjs",
  });

  assert.equal(window.loadedUrl, "http://127.0.0.1:3000/chart/1");
  assert.equal(window.shown, undefined);

  events.get("ready-to-show")();
  assert.equal(window.shown, true);
  assert.deepEqual(handlers.windowOpen(), { action: "deny" });
});

test("starts the local API before creating a desktop window", async () => {
  const calls = [];
  const app = {
    on: () => {},
    quit: () => {},
  };
  const apiManager = {
    start: async () => calls.push("api"),
    stop: () => calls.push("stop"),
  };
  const webManager = {
    start: async () => calls.push("web"),
    stop: () => calls.push("stop-web"),
  };

  await bootstrapDesktop({
    app,
    BrowserWindow: { getAllWindows: () => [] },
    apiManager,
    webManager,
    createWindow: async () => calls.push("window"),
  });

  assert.deepEqual(calls, ["api", "web", "window"]);
});
