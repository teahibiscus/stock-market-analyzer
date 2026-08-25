const assert = require("node:assert/strict");
const test = require("node:test");

const { terminateOwnedChild } = require("../src/childProcess.cjs");

test("terminates the owned Windows process tree", () => {
  let invocation;
  terminateOwnedChild(
    { exitCode: null, pid: 42, kill: () => assert.fail("unexpected fallback") },
    {
      platform: "win32",
      spawnSyncImpl: (command, args) => {
        invocation = { command, args };
      },
    },
  );

  assert.deepEqual(invocation, {
    command: "taskkill",
    args: ["/pid", "42", "/T", "/F"],
  });
});

test("uses SIGTERM for an owned POSIX child", () => {
  let signal;
  terminateOwnedChild(
    {
      exitCode: null,
      pid: 42,
      kill: (nextSignal) => {
        signal = nextSignal;
      },
    },
    { platform: "linux" },
  );

  assert.equal(signal, "SIGTERM");
});
