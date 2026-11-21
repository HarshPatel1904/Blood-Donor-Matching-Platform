import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(__dirname, "..");
const viteBin = path.join(frontendDir, "node_modules", "vite", "bin", "vite.js");

const PORTALS = [
  { name: "donor", port: 5173 },
  { name: "individual", port: 5174 },
  { name: "hospital", port: 5175 },
  { name: "admin", port: 5176 },
];

const children = [];

function prefixLines(stream, label, writeFn) {
  let buffer = "";
  stream.on("data", (chunk) => {
    buffer += chunk.toString();
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      writeFn(`[${label}] ${line}\n`);
    }
  });
  stream.on("end", () => {
    if (buffer) {
      writeFn(`[${label}] ${buffer}\n`);
    }
  });
}

function shutdown(signal) {
  for (const child of children) {
    if (!child.killed) {
      child.kill(signal);
    }
  }
}

for (const portal of PORTALS) {
  const child = spawn(
    process.execPath,
    [viteBin, "--port", String(portal.port), "--strictPort"],
    {
      cwd: frontendDir,
      stdio: ["ignore", "pipe", "pipe"],
    }
  );
  const tag = `${portal.name}:${portal.port}`;
  prefixLines(child.stdout, tag, (text) => process.stdout.write(text));
  prefixLines(child.stderr, tag, (text) => process.stderr.write(text));

  child.on("exit", (code) => {
    if (code !== 0 && code !== null) {
      console.error(`[${tag}] exited with code ${code}`);
    }
  });

  children.push(child);
}

console.log("Starting all 4 role portals:");
console.log("  Donor           -> http://localhost:5173");
console.log("  Individual      -> http://localhost:5174");
console.log("  Hospital Staff  -> http://localhost:5175");
console.log("  Admin (Direct)  -> http://localhost:5176");

process.on("SIGINT", () => {
  shutdown("SIGINT");
  process.exit(0);
});

process.on("SIGTERM", () => {
  shutdown("SIGTERM");
  process.exit(0);
});
