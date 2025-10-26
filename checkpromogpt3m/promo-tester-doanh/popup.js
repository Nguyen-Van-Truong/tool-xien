// ==================== DOM refs ====================
const codesEl       = document.getElementById("codes");
const countEl       = document.getElementById("count");
const delayEl       = document.getElementById("delay");
const timeoutEl     = document.getElementById("timeout");
const initialWaitEl = document.getElementById("initialWait");
const concurrencyEl = document.getElementById("concurrency");
const resultsEl     = document.getElementById("results");
const doneEl        = document.getElementById("done");
const totalEl       = document.getElementById("total");
const baseUrlEl     = document.getElementById("baseUrl");

// ==================== State ====================
let stopFlag = false;
let baseUrl  = "";
let autosaveTimer = null;

// ==================== Patterns ====================
const VALID_PATTERNS = [
  { selector: "aside", textContains: "Hoàn tất việc đổi mã giảm giá" },
  { selector: "#plus-pricing", textContains: "GIẢM 100%" },
  { selector: "#plus-pricing", textContains: "Dùng bản Plus" },
  { selector: "#plus-pricing", textContains: "Bạn có mã khuyến mãi" },
  { selector: "[data-testid='plus-pricing-modal-column']", textContains: "GIẢM 100%" },
  { selector: "[data-testid='plus-pricing-modal-column']", textContains: "Dùng bản Plus" },
  { selector: "[data-testid='plus-pricing-modal-column']", textContains: "Bạn có mã khuyến mãi" }
];
const INVALID_PATTERNS = [
  { selector: "div[role='dialog'], aside, .modal", textContains: "Khuyến mãi không khả dụng" },
  { selector: "div[role='dialog'], aside, .modal", textContains: "không đáp ứng tiêu chí" }
];

// ==================== Utils ====================
function randCode(len = 16) {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  let out = "";
  for (let i = 0; i < len; i++) out += chars[Math.floor(Math.random() * chars.length)];
  return out;
}
function appendResult(code, status, note) {
  const line = document.createElement("div");
  line.innerHTML = `<strong>${code}</strong> — <span class="${status === 'VALID' ? 'ok' : 'bad'}">${status}</span> ${note ? "• " + note : ""}`;
  resultsEl.prepend(line);
  queueAutosave();
}
function downloadCSV(rows) {
  const header = "code,status,note\n";
  const csv = header + rows.map(r =>
    [r.code, r.status, (r.note || "")].map(x => `"${String(x).replace(/"/g, '""')}"`).join(",")
  ).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url  = URL.createObjectURL(blob);
  chrome.downloads.download({ url, filename: `promo_results_${Date.now()}.csv`, saveAs: true });
}
async function loadSettings() {
  const { base } = await chrome.storage.sync.get({ base: "" });
  baseUrl = base || "https://your-test-domain.example/path?promoCode=";
  baseUrlEl.textContent = baseUrl || "chưa cấu hình";
}
function buildUrl(base, code) {
  if (base.includes("{code}")) return base.replace("{code}", encodeURIComponent(code));
  if (/\?promoCode=$/i.test(base)) return base + encodeURIComponent(code);
  const hasQuery = base.includes("?");
  const sep = hasQuery ? "&" : "?";
  return `${base}${sep}promoCode=${encodeURIComponent(code)}`;
}
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function waitForTabComplete(tabId, maxMs = 15000) {
  return new Promise((resolve) => {
    const t = setTimeout(() => { cleanup(); resolve(false); }, maxMs);
    function cleanup(){ chrome.tabs.onUpdated.removeListener(handler); clearTimeout(t); }
    function handler(id, info) {
      if (id === tabId && info.status === "complete") { cleanup(); resolve(true); }
    }
    chrome.tabs.onUpdated.addListener(handler);
  });
}
// => "valid" | "invalid" | "timeout"
async function waitForPromoOutcome(tabId, { initialWaitMs = 5000, observeTimeoutMs = 20000 }) {
  await waitForTabComplete(tabId, 15000);
  await sleep(initialWaitMs);

  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId },
    world: "ISOLATED",
    args: [VALID_PATTERNS, INVALID_PATTERNS, observeTimeoutMs],
    func: (valids, invalids, maxWait) => {
      return new Promise((resolve) => {
        const text = (el) => (el?.textContent || "");
        const matchList = (list) =>
          list.some(p => {
            const el = document.querySelector(p.selector);
            if (!el) return false;
            return p.textContains ? text(el).includes(p.textContains) : true;
          });

        if (matchList(invalids)) return resolve("invalid");
        if (matchList(valids))   return resolve("valid");

        const obs = new MutationObserver(() => {
          if (matchList(invalids)) { obs.disconnect(); resolve("invalid"); }
          else if (matchList(valids)) { obs.disconnect(); resolve("valid"); }
        });
        obs.observe(document.documentElement, { subtree: true, childList: true, characterData: true });

        setTimeout(() => { obs.disconnect(); resolve("timeout"); }, maxWait);
      });
    }
  }).catch(() => [{ result: "timeout" }]);

  return result;
}

// Autosave/restore
function snapshotState() {
  const lines = [...resultsEl.querySelectorAll("div")].map(div => div.innerHTML);
  return {
    codes: codesEl.value,
    delay: delayEl.value,
    timeout: timeoutEl.value,
    initialWait: initialWaitEl.value,
    concurrency: concurrencyEl.value,
    resultsHtml: lines
  };
}
async function restoreState() {
  const key = "ui_state_v2";
  const data = await chrome.storage.local.get(key);
  const st = data[key];
  if (!st) return;
  if (typeof st.codes === "string")   codesEl.value       = st.codes;
  if (st.delay)       delayEl.value       = st.delay;
  if (st.timeout)     timeoutEl.value     = st.timeout;
  if (st.initialWait) initialWaitEl.value = st.initialWait;
  if (st.concurrency) concurrencyEl.value = st.concurrency;
  if (Array.isArray(st.resultsHtml)) {
    resultsEl.innerHTML = "";
    st.resultsHtml.forEach(html => { const div = document.createElement("div"); div.innerHTML = html; resultsEl.appendChild(div); });
  }
}
function queueAutosave() {
  clearTimeout(autosaveTimer);
  autosaveTimer = setTimeout(async () => {
    const key = "ui_state_v2";
    await chrome.storage.local.set({ [key]: snapshotState() });
  }, 250);
}

// ==================== Init ====================
(async () => {
  await loadSettings();
  await restoreState();
})();

document.getElementById("openOptions")?.addEventListener("click", () => chrome.runtime.openOptionsPage());

document.getElementById("stayOpenBtn").addEventListener("click", async () => {
  const url = chrome.runtime.getURL("popup.html");
  await chrome.windows.create({ url, type: "popup", width: 480, height: 800 });
});

// Sinh n mã
document.getElementById("gen").addEventListener("click", () => {
  const n = Math.max(1, Number(countEl.value) || 1);
  const list = []; for (let i = 0; i < n; i++) list.push(randCode(16));
  const old = codesEl.value.trim();
  codesEl.value = (old ? old + "\n" : "") + list.join("\n");
  queueAutosave();
});

// Xoá mã
document.getElementById("clear").addEventListener("click", () => {
  codesEl.value = "";
  queueAutosave();
});

// Xoá TIẾN ĐỘ
document.getElementById("clearResults").addEventListener("click", () => {
  resultsEl.innerHTML = "";
  doneEl.textContent = "0"; totalEl.textContent = "0";
  queueAutosave();
});

// Xuất CSV
document.getElementById("exportCsv").addEventListener("click", () => {
  const lines = [...resultsEl.querySelectorAll("div")].reverse();
  const rows = lines.map(div => {
    const [codePart, rest] = div.textContent.split(" — ");
    const [statusPart, ...noteParts] = (rest || "").split("•");
    return { code: (codePart || "").trim(), status: (statusPart || "").trim(), note: (noteParts.join("•") || "").trim() };
  });
  if (!rows.length) return alert("Chưa có kết quả.");
  downloadCSV(rows);
});

// Dừng
document.getElementById("stop").addEventListener("click", () => stopFlag = true);

// ==================== Worker Pool (đa luồng) ====================
async function processCode(code, opts) {
  const url = buildUrl(baseUrl, code);
  const tab = await chrome.tabs.create({ url, active: false });

  let outcome = "timeout";
  try {
    outcome = await waitForPromoOutcome(tab.id, {
      initialWaitMs: opts.initialWait,
      observeTimeoutMs: opts.timeout
    });
  } catch { outcome = "timeout"; }

  if (outcome === "valid") {
    appendResult(code, "VALID", "popup-match");
    // chrome.tabs.update(tab.id, { pinned: true });
  } else {
    appendResult(code, "INVALID", outcome === "invalid" ? "popup-invalid" : "timeout");
    try { await chrome.tabs.remove(tab.id); } catch {}
  }

  doneEl.textContent = String(Number(doneEl.textContent) + 1);
}

// START với giới hạn số tab song song
document.getElementById("start").addEventListener("click", async () => {
  await loadSettings();
  if (!baseUrl) return alert("Vào Cài đặt để cấu hình Base URL hợp lệ của bạn.");
  stopFlag = false;

  const codes = codesEl.value.split(/\s+/).filter(Boolean);
  if (!codes.length) return alert("Không có mã nào.");

  totalEl.textContent = String(codes.length);
  doneEl.textContent  = "0";

  const delayStart   = Math.max(0, Number(delayEl.value) || 0); // delay giữa việc KHỞI TẠO mỗi job
  const timeout      = Math.max(500, Number(timeoutEl.value) || 20000);
  const initialWait  = Math.max(0, Number(initialWaitEl.value) || 0);
  const concurrency  = Math.max(1, Math.min(20, Number(concurrencyEl.value) || 1)); // an toàn: tối đa 20

  let next = 0;
  let active = 0;

  const opts = { timeout, initialWait };

  return new Promise(async (resolve) => {
    async function launchNext() {
      if (stopFlag) { if (active === 0) resolve(); return; }
      if (next >= codes.length) { if (active === 0) resolve(); return; }

      const code = codes[next++];
      active++;

      // KHỞI TẠO 1 job
      processCode(code, opts).finally(async () => {
        active--;
        if (delayStart) await sleep(delayStart);
        launchNext();
      });
    }

    // Khởi chạy tối đa `concurrency` job đầu
    const first = Math.min(concurrency, codes.length);
    for (let i = 0; i < first; i++) {
      launchNext();
      if (delayStart) await sleep(delayStart);
    }
  });
});

// Autosave khi đổi tham số
[codesEl, delayEl, timeoutEl, initialWaitEl, concurrencyEl]
  .forEach(el => el.addEventListener("input", queueAutosave));
