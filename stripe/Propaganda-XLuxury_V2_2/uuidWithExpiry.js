// uuidWithExpiry.js  (CommonJS)
const { v4: uuidv4 } = require("uuid");
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

/**
 * Example fingerprint from your screenshot (replace with your live values).
 * You can also pass a different object to generateUUIDWithExpiry().
 */
const exampleFingerprint = {
  userAgent:
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  platform: "Win32",
  language: "en-US",
  timezone: "America/New_York",
  screen: { width: 1920, height: 1080, colorDepth: 24 },
  cookieEnabled: true,
  devToolsOpen: false,
};

/* -------------------- Fingerprint hashing (stable) -------------------- */

/**
 * Canonicalize object to a stable JSON string:
 * - recursively sort keys
 * - stringify primitives consistently
 */
function canonicalize(value) {
  if (Array.isArray(value)) {
    return `[${value.map(canonicalize).join(",")}]`;
  }
  if (value && typeof value === "object") {
    const keys = Object.keys(value).sort();
    return `{${keys.map((k) => `"${k}":${canonicalize(value[k])}`).join(",")}}`;
  }
  // primitives
  if (typeof value === "string") return JSON.stringify(value);
  if (typeof value === "number" && !Number.isFinite(value))
    return JSON.stringify(String(value));
  if (typeof value === "number") return String(value);
  if (typeof value === "boolean") return value ? "true" : "false";
  if (value === null || value === undefined) return "null";
  return JSON.stringify(String(value));
}

/** Return SHA-256 hex of the canonicalized fingerprint */
function fingerprintHash(fp) {
  const canonical = canonicalize(fp);
  return crypto.createHash("sha256").update(canonical).digest("hex");
}

/* -------------------- UUID + expiry helpers -------------------- */

const DAY_MS = 24 * 60 * 60 * 1000;

/**
 * Generate a random UUID v4 with 7-day expiry (default), bound to a fingerprint hash.
 * @param {object} fp fingerprint object
 * @param {number} days validity window in days (default 7)
 */
function generateUUIDWithExpiry(fp, days = 7) {
  const uuid = uuidv4(); // true v4 random
  const issuedAt = Date.now();
  const expiresAt = issuedAt + days * DAY_MS;

  return {
    uuid,
    issuedAt,
    expiresAt,
    fingerprintHash: fingerprintHash(fp),
    daysValid: days,
    version: 1,
  };
}

/**
 * Validate the stored token
 * @param {object} token stored object { uuid, issuedAt, expiresAt, fingerprintHash, ... }
 * @param {object} [currentFp] optional fingerprint to also verify binding
 * @returns {boolean}
 */
function isValid(token, currentFp) {
  if (!token || typeof token !== "object") return false;
  if (typeof token.expiresAt !== "number") return false;
  if (Date.now() >= token.expiresAt) return false;

  if (currentFp) {
    const currentHash = fingerprintHash(currentFp);
    if (currentHash !== token.fingerprintHash) return false;
  }
  return true;
}

/* -------------------- Simple CLI / demo -------------------- */
/**
 * Usage:
 *   node uuidWithExpiry.js new               -> create/overwrite ./uuid_store.json
 *   node uuidWithExpiry.js validate          -> validate against exampleFingerprint
 *   node uuidWithExpiry.js validate --loose  -> validate time only (ignore fingerprint)
 *   node uuidWithExpiry.js show              -> print current store
 */

const STORE_PATH = path.join(__dirname, "uuid_store.json");

function saveToken(token, filePath = STORE_PATH) {
  fs.writeFileSync(filePath, JSON.stringify(token, null, 2));
}

function loadToken(filePath = STORE_PATH) {
  if (!fs.existsSync(filePath)) return null;
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return null;
  }
}

function main() {
  const cmd = (process.argv[2] || "").toLowerCase();
  if (cmd === "new") {
    const token = generateUUIDWithExpiry(exampleFingerprint, 7);
    saveToken(token);
    console.log("Created new UUID token (7-day validity):");
    console.log(token);
    return;
  }
  if (cmd === "validate") {
    const loose = process.argv.includes("--loose");
    const token = loadToken();
    if (!token) {
      console.error("No token found. Run: node uuidWithExpiry.js new");
      process.exit(1);
    }
    const ok = isValid(token, loose ? undefined : exampleFingerprint);
    console.log(ok ? "VALID ✅" : "INVALID ❌");
    if (!ok) {
      console.log("Stored token:", token);
      if (!loose) {
        console.log(
          "Tip: try loose validation with: node uuidWithExpiry.js validate --loose"
        );
      }
    }
    return;
  }
  if (cmd === "show") {
    console.log(loadToken() || "(no store)");
    return;
  }

  // default help
  console.log(`
Commands:
  node uuidWithExpiry.js new
  node uuidWithExpiry.js validate
  node uuidWithExpiry.js validate --loose
  node uuidWithExpiry.js show
`);
}

if (require.main === module) {
  main();
}

module.exports = { generateUUIDWithExpiry, isValid, fingerprintHash, canonicalize };
