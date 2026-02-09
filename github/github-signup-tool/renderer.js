/**
 * GitHub Signup Tool - Renderer
 * Frontend logic: parse accounts, handle IPC events, manage UI state
 */

// ==================== State ====================
let accounts = [];
let successList = [];
let failedList = [];
let isRunning = false;
let isWaitingManual = false;

// ==================== DOM Elements ====================
const $ = (sel) => document.querySelector(sel);
const inputAccounts = $('#input-accounts');
const accountCount = $('#account-count');
const btnRun = $('#btn-run');
const btnStop = $('#btn-stop');
const btnCloseAll = $('#btn-close-all');
const btnDone = $('#btn-done');
const btnFail = $('#btn-fail');
const manualControls = $('#manual-controls');
const manualStatusText = $('#manual-status-text');
const progressBar = $('#progress-bar');
const progressText = $('#progress-text');
const resultSuccess = $('#result-success');
const resultFailed = $('#result-failed');
const logContainer = $('#log-container');
const statSuccess = $('#stat-success');
const statFailed = $('#stat-failed');
const statBrowsers = $('#stat-browsers');
const tabCountSuccess = $('#tab-count-success');
const tabCountFailed = $('#tab-count-failed');
const settingsPanel = $('#settings-panel');
const btnSettings = $('#btn-settings');
const btnCloseSettings = $('#btn-close-settings');
const btnSaveSettings = $('#btn-save-settings');
const btnCopy = $('#btn-copy');
const btnSave = $('#btn-save');
const btnRefresh = $('#btn-refresh');
const btnClearLog = $('#btn-clear-log');
const btnDeleteData = $('#btn-delete-browser-data');
const btnRefreshTemp = $('#btn-refresh-temp');
const tempSizeDisplay = $('#temp-size-display');

// ==================== Logging ====================
function log(msg, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    const ts = new Date().toLocaleTimeString('vi-VN');
    entry.textContent = `[${ts}] ${msg}`;
    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// ==================== Account Parsing ====================
function parseAccounts(text) {
    const lines = text.trim().split('\n').filter(l => l.trim());
    return lines.map(line => {
        const parts = line.trim().split('|');
        if (parts.length < 2) return null;
        const email = parts[0].trim();
        const password = parts[1].trim();
        // Username = phần trước @ trong email
        const username = email.split('@')[0].replace(/[^a-zA-Z0-9_-]/g, '');
        return { email, password, username };
    }).filter(Boolean);
}

inputAccounts.addEventListener('input', () => {
    const parsed = parseAccounts(inputAccounts.value);
    accountCount.textContent = parsed.length;
});

// ==================== Settings ====================
function getSettings() {
    return {
        headless: $('#headless-mode').checked,
        keepBrowser: $('#keep-browsers').checked,
        autofillDelay: parseFloat($('#autofill-delay').value) || 1
    };
}

function loadSettings() {
    try {
        const saved = localStorage.getItem('github_signup_settings');
        if (saved) {
            const s = JSON.parse(saved);
            $('#headless-mode').checked = !!s.headless;
            $('#keep-browsers').checked = s.keepBrowser !== false;
            $('#autofill-delay').value = s.autofillDelay || 1;
        }
    } catch (e) { }
}

function saveSettings() {
    const settings = getSettings();
    localStorage.setItem('github_signup_settings', JSON.stringify(settings));
    log('Settings saved', 'success');
    settingsPanel.classList.add('hidden');
}

// ==================== Tab Switching ====================
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        $(`#tab-${tab.dataset.tab}`).classList.add('active');
    });
});

// ==================== Update UI State ====================
function updateStats() {
    statSuccess.textContent = successList.length;
    statFailed.textContent = failedList.length;
    tabCountSuccess.textContent = successList.length;
    tabCountFailed.textContent = failedList.length;
}

function setProgress(current, total, text) {
    if (total === 0) {
        progressBar.style.setProperty('--progress', '0%');
        progressText.textContent = text || 'Ready';
        return;
    }
    const pct = Math.round((current / total) * 100);
    progressBar.style.setProperty('--progress', `${pct}%`);
    progressText.textContent = text || `${current}/${total} (${pct}%)`;
}

function setRunning(running) {
    isRunning = running;
    btnRun.disabled = running;
    btnStop.disabled = !running;
    inputAccounts.disabled = running;
    if (!running) {
        hideManualControls();
    }
}

function showManualControls(email) {
    isWaitingManual = true;
    manualControls.classList.remove('hidden');
    manualStatusText.textContent = `Chờ hoàn thành captcha cho: ${email}`;
}

function hideManualControls() {
    isWaitingManual = false;
    manualControls.classList.add('hidden');
}

// ==================== Start Signup ====================
btnRun.addEventListener('click', async () => {
    const parsed = parseAccounts(inputAccounts.value);
    if (parsed.length === 0) {
        log('No valid accounts found! Format: email|password', 'error');
        return;
    }

    accounts = parsed;
    successList = [];
    failedList = [];
    resultSuccess.value = '';
    resultFailed.value = '';
    updateStats();
    setProgress(0, accounts.length);
    setRunning(true);

    log(`Starting signup for ${accounts.length} accounts...`, 'info');

    const settings = getSettings();
    try {
        await window.api.startSignup(accounts, settings);
    } catch (err) {
        log(`Error: ${err.message}`, 'error');
        setRunning(false);
    }
});

// ==================== Stop ====================
btnStop.addEventListener('click', async () => {
    log('Stopping...', 'warning');
    try {
        await window.api.stopSignup();
    } catch (e) { }
    setRunning(false);
});

// ==================== Manual Done / Failed ====================
btnDone.addEventListener('click', async () => {
    log('User marked as DONE ✅', 'success');
    hideManualControls();
    try {
        await window.api.nextAccount('done');
    } catch (e) { }
});

btnFail.addEventListener('click', async () => {
    log('User marked as FAILED ❌', 'error');
    hideManualControls();
    try {
        await window.api.nextAccount('failed');
    } catch (e) { }
});

// ==================== Close Browsers ====================
btnCloseAll.addEventListener('click', async () => {
    log('Closing all browsers...', 'warning');
    try {
        await window.api.closeAllBrowsers();
        log('All browsers closed', 'info');
    } catch (e) { }
});

// ==================== IPC Event Handlers ====================

// Log messages
window.api.onLog((data) => {
    const msg = typeof data === 'string' ? data : (data.message || '');
    let type = (typeof data === 'object' && data.type) ? data.type : 'info';
    if (type === 'info') {
        const lmsg = msg.toLowerCase();
        if (lmsg.includes('success') || lmsg.includes('✅') || lmsg.includes('done')) type = 'success';
        else if (lmsg.includes('error') || lmsg.includes('fail') || lmsg.includes('❌')) type = 'error';
        else if (lmsg.includes('warn') || lmsg.includes('⚠') || lmsg.includes('waiting') || lmsg.includes('chờ')) type = 'warning';
    }
    log(msg, type);
});

// Result (individual account result from worker)
window.api.onResult((result) => {
    const { email, password, username, status, error, timestamp, totals } = result;
    if (status === 'success') {
        successList.push(result);
        resultSuccess.value += `${email}|${password}|${username}\n`;
    } else {
        failedList.push(result);
        resultFailed.value += `${email}|${password}|${error || 'Unknown'}|${timestamp || ''}\n`;
    }
    updateStats();
});

// Progress update
window.api.onProgress((data) => {
    const { current, total, text } = data;
    setProgress(current, total, text || `${current}/${total}`);
});

// Waiting for manual completion
window.api.onWaitingManual((data) => {
    const { email } = data;
    showManualControls(email);
});

// Browser count update
window.api.onBrowserCount((data) => {
    statBrowsers.textContent = `${data.active || 0}/${data.max || 1}`;
});

// Process complete
window.api.onComplete((data) => {
    const { total, success, failed } = data;
    setRunning(false);
    setProgress(total, total, `Done! ✅${success} ❌${failed}`);
    log(`\n===== COMPLETED =====`, 'success');
    log(`Total: ${total} | Success: ${success} | Failed: ${failed}`, 'success');
});

// ==================== Results Buttons ====================
btnCopy.addEventListener('click', () => {
    const activeTab = document.querySelector('.tab.active').dataset.tab;
    const text = activeTab === 'success' ? resultSuccess.value : resultFailed.value;
    navigator.clipboard.writeText(text).then(() => {
        log('Copied to clipboard!', 'success');
    });
});

btnSave.addEventListener('click', async () => {
    const activeTab = document.querySelector('.tab.active').dataset.tab;
    const text = activeTab === 'success' ? resultSuccess.value : resultFailed.value;
    const blob = new Blob([text], { type: 'text/plain' });
    // Simple approach: download via data URI
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `github_${activeTab}_${Date.now()}.txt`;
    a.click();
    log(`Saved ${activeTab} results`, 'success');
});

btnRefresh.addEventListener('click', async () => {
    try {
        const results = await window.api.readResults();
        if (results) {
            if (results.success) {
                resultSuccess.value = results.success;
                successList = results.success.trim().split('\n').filter(l => l);
            }
            if (results.failed) {
                resultFailed.value = results.failed;
                failedList = results.failed.trim().split('\n').filter(l => l);
            }
            updateStats();
            log('Results refreshed from files', 'info');
        }
    } catch (e) {
        log('No saved results found', 'warning');
    }
});

// ==================== Log Clear ====================
btnClearLog.addEventListener('click', () => {
    logContainer.innerHTML = '';
});

// ==================== Settings ====================
btnSettings.addEventListener('click', () => {
    settingsPanel.classList.remove('hidden');
    refreshTempSize();
});

btnCloseSettings.addEventListener('click', () => {
    settingsPanel.classList.add('hidden');
});

btnSaveSettings.addEventListener('click', saveSettings);

btnDeleteData.addEventListener('click', async () => {
    log('Deleting browser data...', 'warning');
    try {
        const result = await window.api.deleteBrowserData();
        log(`Deleted ${result.deletedCount} folder(s), freed ${result.freedMB} MB`, 'success');
        refreshTempSize();
    } catch (e) {
        log(`Error deleting browser data`, 'error');
    }
});

async function refreshTempSize() {
    try {
        const size = await window.api.getTempSize();
        tempSizeDisplay.textContent = `Cache: ${size.sizeMB} MB (${size.folderCount} folders)`;
    } catch (e) {
        tempSizeDisplay.textContent = 'Unable to read';
    }
}

btnRefreshTemp.addEventListener('click', refreshTempSize);

// ==================== Init ====================
loadSettings();
log('GitHub Signup Tool ready!', 'success');
log('Paste accounts (email|password) and click Start', 'info');
