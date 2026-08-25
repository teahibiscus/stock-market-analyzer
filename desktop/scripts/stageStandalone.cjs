"use strict";

const fs = require("node:fs");
const path = require("node:path");

function stageStandalone({
  projectRoot = path.resolve(__dirname, "..", ".."),
  outputRoot = path.join(projectRoot, "desktop", "dist", "frontend"),
} = {}) {
  const frontendRoot = path.join(projectRoot, "frontend");
  const standaloneRoot = path.join(
    frontendRoot,
    ".next",
    "standalone",
    "frontend",
  );
  const staticRoot = path.join(frontendRoot, ".next", "static");
  const publicRoot = path.join(frontendRoot, "public");

  if (!fs.existsSync(path.join(standaloneRoot, "server.js"))) {
    throw new Error(
      "Next.js standalone output is missing. Run the frontend build first.",
    );
  }

  fs.rmSync(outputRoot, { recursive: true, force: true });
  fs.mkdirSync(path.dirname(outputRoot), { recursive: true });
  fs.cpSync(standaloneRoot, outputRoot, { recursive: true });
  fs.cpSync(staticRoot, path.join(outputRoot, ".next", "static"), {
    recursive: true,
  });
  if (fs.existsSync(publicRoot)) {
    fs.cpSync(publicRoot, path.join(outputRoot, "public"), { recursive: true });
  }
  return outputRoot;
}

if (require.main === module) {
  console.log(`Staged Next.js standalone output at ${stageStandalone()}`);
}

module.exports = { stageStandalone };
