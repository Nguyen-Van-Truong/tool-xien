/**
 * Renderer Process - Frontend Logic
 * Handles UI interactions and IPC communication
 */

// DOM Elements
const inputAccounts = document.getElementById('input-accounts');
const btnRun = document.getElementById('btn-run');
const btnStop = document.getElementById('btn-stop');
const btnCloseAll = document.getElementById('btn-close-all');
const btnClear = document.getElementById('btn-clear');
const btnCopy = document.getElementById('btn-copy');
const btnSave = document.getElementById('btn-save');
const btnRefresh = document.getElementById('btn-refresh');
const btnClearLog = document.getElementById('btn-clear-log');
const logContainer = document.getElementById('log-container');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');
const accountCount = document.getElementById('account-count');

// Result textareas
const resultSuccess = document.getElementById('result-success');
const resultFailed = document.getElementById('result-failed');

// Stats
const statSuccess = document.getElementById('stat-success');
const statFailed = document.getElementById('stat-failed');
const tabCountSuccess = document.getElementById('tab-count-success');
const tabCountFailed = document.getElementById('tab-count-failed');

// State
let isRunning = false;
let currentTab = 'success';

// Update account count on input
inputAccounts.addEventListener('input', () => {
    const lines = inputAccounts.value.trim().split('\n').filter(line => {
        const trimmed = line.trim();
        return trimmed && trimmed.split('|').length >= 4; // email|pass|first|last
    });
    accountCount.textContent = lines.length;
});

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;
        currentTab = tabName;

        // Update tab buttons
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(`tab-${tabName}`).classList.add('active');
    });
});

// Log functions
function addLog(message, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

function clearLog() {
    logContainer.innerHTML = '';
}

// Update stats
function updateStats(success, failed) {
    statSuccess.textContent = success;
    statFailed.textContent = failed;
    tabCountSuccess.textContent = success;
    tabCountFailed.textContent = failed;
}

// Update progress
function updateProgress(current, total, text) {
    const percent = total > 0 ? (current / total) * 100 : 0;
    progressBar.style.setProperty('--progress', `${percent}%`);
    progressText.textContent = text || `${current}/${total}`;
}

// Parse accounts from input
function parseAccounts(text) {
    const lines = text.trim().split('\n').filter(line => line.trim());
    return lines.map(line => {
        const parts = line.trim().split('|');
        if (parts.length >= 4) {
            return {
                email: parts[0].trim(),
                password: parts[1].trim(),
                firstname: parts[2].trim(),
                lastname: parts[3].trim()
            };
        }
        return null;
    }).filter(acc => acc && acc.email && acc.password && acc.firstname && acc.lastname);
}

// Refresh results from files
async function refreshResults() {
    try {
        const results = await window.api.readResults();
        resultSuccess.value = results.success;
        resultFailed.value = results.failed;

        // Count lines
        const successCount = results.success ? results.success.split('\n').filter(l => l.trim()).length : 0;
        const failedCount = results.failed ? results.failed.split('\n').filter(l => l.trim()).length : 0;

        updateStats(successCount, failedCount);
    } catch (error) {
        addLog(`Lỗi đọc kết quả: ${error.message}`, 'error');
    }
}

// Button handlers
btnRun.addEventListener('click', async () => {
    const accounts = parseAccounts(inputAccounts.value);

    if (accounts.length === 0) {
        addLog('Không có accounts hợp lệ!', 'error');
        return;
    }

    isRunning = true;
    btnRun.disabled = true;
    btnStop.disabled = false;

    // Clear kết quả cũ trước khi chạy
    addLog('🗑️ Xóa kết quả cũ...', 'info');
    await window.api.clearResults();

    // Clear UI
    resultSuccess.value = '';
    resultFailed.value = '';
    updateStats(0, 0);
    clearLog();

    addLog(`🚀 Bắt đầu với ${accounts.length} accounts...`, 'info');
    updateProgress(0, accounts.length, 'Đang khởi động...');

    try {
        await window.api.startSignup(accounts, { headless: false });
    } catch (error) {
        addLog(`Lỗi: ${error.message}`, 'error');
    }
});

btnStop.addEventListener('click', async () => {
    addLog('Đang dừng...', 'warning');
    await window.api.stopSignup();
    isRunning = false;
    btnRun.disabled = false;
    btnStop.disabled = true;
    updateProgress(0, 0, 'Đã dừng');
});

// Tắt tất cả browsers
btnCloseAll.addEventListener('click', async () => {
    addLog('✖ Đang tắt tất cả browsers...', 'warning');
    await window.api.closeAllBrowsers();
    addLog('✅ Đã tắt xong!', 'success');
});

btnClear.addEventListener('click', () => {
    inputAccounts.value = '';
    accountCount.textContent = '0';
});

btnCopy.addEventListener('click', () => {
    let content = '';
    if (currentTab === 'success') content = resultSuccess.value;
    else content = resultFailed.value;

    navigator.clipboard.writeText(content).then(() => {
        addLog('Đã copy vào clipboard!', 'success');
    });
});

btnSave.addEventListener('click', () => {
    let content = '';
    let filename = '';

    if (currentTab === 'success') {
        content = resultSuccess.value;
        filename = 'grok_success_export.txt';
    } else {
        content = resultFailed.value;
        filename = 'grok_failed_export.txt';
    }

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    addLog(`Đã lưu ${filename}`, 'success');
});

btnRefresh.addEventListener('click', refreshResults);
btnClearLog.addEventListener('click', clearLog);

// IPC Event handlers
window.api.onLog((data) => {
    addLog(data.message, data.type || 'info');
});

window.api.onResult((data) => {
    refreshResults();
});

window.api.onProgress((data) => {
    updateProgress(data.current, data.total, data.text);
});

window.api.onComplete((data) => {
    isRunning = false;
    btnRun.disabled = false;
    btnStop.disabled = true;
    updateProgress(data.total, data.total, `Hoàn thành! (${data.totalTime}s)`);
    addLog(`Hoàn thành! SUCCESS: ${data.success}, FAILED: ${data.failed}`, 'success');
    refreshResults();
});

// Initial load
refreshResults();
addLog('Sẵn sàng!', 'success');
