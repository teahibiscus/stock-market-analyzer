const assert = require("node:assert/strict");
const test = require("node:test");

const { createWindowManager } = require("../src/windowManager.cjs");

test("opens independent URL-addressable chart windows", async () => {
  const windows = [];

  class FakeBrowserWindow {
    constructor(options) {
      this.options = options;
      this.events = {};
      this.webContents = {
        on: () => {},
        setWindowOpenHandler: (handler) => {
          this.openHandler = handler;
        },
      };
      windows.push(this);
    }

    once(event, handler) {
      this.events[event] = handler;
    }

    on(event, handler) {
      this.events[event] = handler;
    }

    async loadURL(url) {
      this.url = url;
    }

    show() {}
  }

  const manager = createWindowManager({
    BrowserWindow: FakeBrowserWindow,
    frontendUrl: "http://127.0.0.1:3000",
    preloadPath: "C:\\app\\preload.cjs",
  });

  await manager.openChart({
    instrumentId: "instrument 1",
    interval: "5m",
    period: "5d",
    volume: false,
  });
  await manager.openChart({
    instrumentId: "instrument-2",
    interval: "1d",
    period: "1y",
    volume: true,
  });

  assert.equal(windows.length, 2);
  assert.equal(
    windows[0].url,
    "http://127.0.0.1:3000/chart/instrument%201?interval=5m&period=5d&volume=0",
  );
  assert.equal(manager.count(), 2);

  windows[0].events.closed();
  assert.equal(manager.count(), 1);
});

test("denies untrusted child-window origins", async () => {
  let window;
  class FakeBrowserWindow {
    constructor() {
      window = this;
      this.webContents = {
        on: () => {},
        setWindowOpenHandler: (handler) => {
          this.openHandler = handler;
        },
      };
    }
    once() {}
    on() {}
    async loadURL() {}
  }

  const manager = createWindowManager({
    BrowserWindow: FakeBrowserWindow,
    frontendUrl: "http://127.0.0.1:3000",
  });
  await manager.open("/");

  assert.deepEqual(window.openHandler({ url: "https://example.com" }), {
    action: "deny",
  });
  assert.throws(
    () => manager.open("https://example.com"),
    /Untrusted window URL/,
  );
});
