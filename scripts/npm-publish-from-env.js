#!/usr/bin/env node
"use strict";

const { spawn } = require("node:child_process");
const fs = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");

const repoRoot = path.resolve(__dirname, "..");
const envPath = path.resolve(repoRoot, process.env.APPAUTOACTION_NPM_ENV || ".env");
const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";

function parseDotenv(text = "") {
  const values = {};
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const match = trimmed.match(/^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$/);
    if (!match) continue;
    let value = match[2].trim();
    if ((value.startsWith("\"") && value.endsWith("\"")) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    values[match[1]] = value;
  }
  return values;
}

function registryHost(registry = "") {
  try {
    return new URL(registry).host || "registry.npmjs.org";
  } catch {
    return "registry.npmjs.org";
  }
}

function runNpm(args, env) {
  return new Promise((resolve) => {
    const child = spawn(npmCommand, args, {
      cwd: repoRoot,
      env,
      stdio: ["ignore", "inherit", "inherit"],
    });
    child.on("close", (code) => resolve(Number(code) || 0));
    child.on("error", (error) => {
      console.error(error instanceof Error ? error.message : String(error));
      resolve(1);
    });
  });
}

async function main() {
  const npmArgs = process.argv.slice(2).length ? process.argv.slice(2) : ["publish", "--access", "public"];
  const env = parseDotenv(await fs.readFile(envPath, "utf8"));
  const token = env.NPM_TOKEN || env.NODE_AUTH_TOKEN;
  const registry = env.NPM_CONFIG_REGISTRY || "https://registry.npmjs.org/";
  if (!token) {
    console.error(`No NPM_TOKEN or NODE_AUTH_TOKEN found in ${envPath}`);
    process.exit(1);
  }

  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "appautoaction-npmrc-"));
  const npmrcPath = path.join(tempDir, ".npmrc");
  try {
    const host = registryHost(registry);
    await fs.writeFile(
      npmrcPath,
      [`registry=${registry}`, `//${host}/:_authToken=${token}`, "always-auth=true", ""].join("\n"),
      { mode: 0o600 }
    );
    const code = await runNpm(npmArgs, {
      ...process.env,
      NPM_CONFIG_USERCONFIG: npmrcPath,
      npm_config_userconfig: npmrcPath,
      NODE_AUTH_TOKEN: token,
      NPM_TOKEN: token,
      NPM_CONFIG_REGISTRY: registry,
    });
    process.exit(code);
  } finally {
    await fs.rm(tempDir, { recursive: true, force: true }).catch(() => {});
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
