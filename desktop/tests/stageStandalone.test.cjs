const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const { stageStandalone } = require("../scripts/stageStandalone.cjs");

test("stages the standalone server and static assets for desktop resources", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "sma-standalone-"));
  fs.mkdirSync(path.join(root, "frontend", ".next", "standalone", "frontend"), {
    recursive: true,
  });
  fs.mkdirSync(path.join(root, "frontend", ".next", "static"), {
    recursive: true,
  });
  fs.writeFileSync(
    path.join(root, "frontend", ".next", "standalone", "frontend", "server.js"),
    "server",
  );
  fs.writeFileSync(
    path.join(root, "frontend", ".next", "static", "asset.js"),
    "asset",
  );

  const output = stageStandalone({ projectRoot: root });

  assert.equal(
    fs.readFileSync(path.join(output, "server.js"), "utf8"),
    "server",
  );
  assert.equal(
    fs.readFileSync(path.join(output, ".next", "static", "asset.js"), "utf8"),
    "asset",
  );
  fs.rmSync(root, { recursive: true, force: true });
});
