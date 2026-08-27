/**
 * Starts Expo with LAN host from .env (for API + Metro) or tunnel when
 * EXPO_CONNECTION=tunnel (fixes Expo Go timeouts on phone hotspot / blocked Node firewall).
 */
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const root = path.join(__dirname, "..");
const envPath = path.join(root, ".env");

function parseEnvFile(filePath) {
  const out = {};
  if (!fs.existsSync(filePath)) return out;
  const text = fs.readFileSync(filePath, "utf8");
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    let val = trimmed.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    out[key] = val;
  }
  return out;
}

const fileEnv = parseEnvFile(envPath);
const host =
  fileEnv.EXPO_PUBLIC_API_HOST?.trim() ||
  process.env.EXPO_PUBLIC_API_HOST?.trim() ||
  "192.168.0.1";

process.env.REACT_NATIVE_PACKAGER_HOSTNAME = host;
process.env.EXPO_PACKAGER_HOSTNAME = host;

const metroPort =
  process.env.EXPO_METRO_PORT?.trim() ||
  fileEnv.EXPO_METRO_PORT?.trim() ||
  "8001";

const connection = (
  process.env.EXPO_CONNECTION?.trim() ||
  fileEnv.EXPO_CONNECTION?.trim() ||
  "lan"
).toLowerCase();

const useTunnel =
  connection === "tunnel" || process.argv.includes("--tunnel");

const passThrough = process.argv
  .slice(2)
  .filter((a) => a !== "--tunnel" && a !== "--lan");

const expoArgs = [
  "expo",
  "start",
  useTunnel ? "--tunnel" : "--lan",
  "--port",
  metroPort,
  ...passThrough,
];

console.log(
  `[start-expo] API host=${host}:${fileEnv.EXPO_PUBLIC_API_PORT || "8000"} mode=${useTunnel ? "tunnel" : "lan"} metro=${metroPort}`
);

const child = spawn("npx", expoArgs, {
  cwd: root,
  stdio: "inherit",
  shell: true,
  env: { ...process.env },
});

child.on("exit", (code) => process.exit(code ?? 0));
