// DOM Elements
const inputAccounts = document.getElementById('input-accounts');
const btnRun = document.getElementById('btn-run');
const btnStop = document.getElementById('btn-stop');
const btnCloseAll = document.getElementById('btn-close-all');
const btnClear = document.getElementById('btn-clear');
const btnImport = document.getElementById('btn-import');
const btnCopy = document.getElementById('btn-copy');
const btnSave = document.getElementById('btn-save');
const btnRefresh = document.getElementById('btn-refresh');
const btnClearLog = document.getElementById('btn-clear-log');
const logContainer = document.getElementById('log-container');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');
const accountCount = document.getElementById('account-count');

const resultPassed = document.getElementById('result-passed');
const resultHasPhone = document.getElementById('result-has-phone');
const resultNeedPhone = document.getElementById('result-need-phone');
const resultFailed = document.getElementById('result-failed');

const statPassed = document.getElementById('stat-passed');
const statHasPhone = document.getElementById('stat-has-phone');
const statNeedPhone = document.getElementById('stat-need-phone');
const statFailed = document.getElementById('stat-failed');
const tabCountPassed = document.getElementById('tab-count-passed');
const tabCountHasPhone = document.getElementById('tab-count-has-phone');
const tabCountNeedPhone = document.getElementById('tab-count-need-phone');
const tabCountFailed = document.getElementById('tab-count-failed');
const browserSelect = document.getElementById('browser-select');

const tempSize = document.getElementById('temp-size');
const tempCount = document.getElementById('temp-count');
const btnClearTemp = document.getElementById('btn-clear-temp');
const cacheSize = document.getElementById('cache-size');
const btnClearAll = document.getElementById('btn-clear-all');

let isRunning = false;
let currentTab = 'passed';
let detectedBrowsers = [];

// Load browsers
async function loadBrowsers() {
    try {
        detectedBrowsers = await window.api.detectBrowsers();
        browserSelect.innerHTML = '';

        const available = detectedBrowsers.filter(b => b.detected);
        const unavailable = detectedBrowsers.filter(b => !b.detected);

        if (available.length === 0) {
            browserSelect.innerHTML = '<option value="" disabled>Không tìm thấy browser!</option>';
            addLog('❌ Không tìm thấy trình duyệt!', 'error');
            return;
        }

        available.forEach((browser, i) => {
            const opt = document.createElement('option');
            opt.value = browser.id;
            opt.textContent = `✓ ${browser.name}`;
            if (i === 0) opt.selected = true;
            browserSelect.appendChild(opt);
        });

        if (unavailable.length > 0) {
            const sep = document.createElement('option');
            sep.disabled = true;
            sep.textContent = '───────────';
            browserSelect.appendChild(sep);
            unavailable.forEach(browser => {
                const opt = document.createElement('option');
                opt.value = browser.id;
                opt.disabled = true;
                opt.textContent = `✗ ${browser.name} (không có)`;
                browserSelect.appendChild(opt);
            });
        }

        await window.api.setBrowser(available[0].id);
        addLog(`🌐 Đã chọn: ${available[0].name}`, 'success');
    } catch (error) {
        addLog(`Lỗi detect browsers: ${error.message}`, 'error');
    }
}

browserSelect.addEventListener('change', async () => {
    const browserId = browserSelect.value;
    const browser = detectedBrowsers.find(b => b.id === browserId);
    if (browser) {
        await window.api.setBrowser(browserId);
        addLog(`🌐 Đã chọn: ${browser.name}`, 'success');
    }
});

// Account count
inputAccounts.addEventListener('input', () => {
    const lines = inputAccounts.value.trim().split('\n').filter(line => line.trim() && line.includes('|'));
    accountCount.textContent = lines.length;
});

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;
        currentTab = tabName;
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(`tab-${tabName}`).classList.add('active');
    });
});

// Log
function addLog(message, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

function clearLog() { logContainer.innerHTML = ''; }

// Stats
function updateStats(passed, hasPhone, needPhone, failed) {
    statPassed.textContent = passed;
    statHasPhone.textContent = hasPhone;
    statNeedPhone.textContent = needPhone;
    statFailed.textContent = failed;
    tabCountPassed.textContent = passed;
    tabCountHasPhone.textContent = hasPhone;
    tabCountNeedPhone.textContent = needPhone;
    tabCountFailed.textContent = failed;
}

// Progress
function updateProgress(current, total, text) {
    const percent = total > 0 ? (current / total) * 100 : 0;
    progressBar.style.setProperty('--progress', `${percent}%`);
    progressText.textContent = text || `${current}/${total}`;
}

// Parse accounts
function parseAccounts(text) {
    return text.trim().split('\n')
        .filter(line => line.trim())
        .map(line => {
            const trimmed = line.trim();
            let email, password;
            if (trimmed.includes('|')) {
                [email, password] = trimmed.split('|');
            } else if (trimmed.includes('\t')) {
                [email, password] = trimmed.split('\t');
            } else if (trimmed.includes(' ')) {
                const parts = trimmed.split(/\s+/);
                email = parts[0];
                password = parts[1];
            }
            return { email: email?.trim(), password: password?.trim() };
        }).filter(acc => acc.email && acc.password);
}

// Refresh results
async function refreshResults() {
    try {
        const results = await window.api.readResults();
        resultPassed.value = results.passed;
        resultHasPhone.value = results.hasPhone;
        resultNeedPhone.value = results.needPhone;
        resultFailed.value = results.loginFailed;

        const passedCount = results.passed ? results.passed.split('\n').filter(l => l.trim()).length : 0;
        const hasPhoneCount = results.hasPhone ? results.hasPhone.split('\n').filter(l => l.trim()).length : 0;
        const needPhoneCount = results.needPhone ? results.needPhone.split('\n').filter(l => l.trim()).length : 0;
        const failedCount = results.loginFailed ? results.loginFailed.split('\n').filter(l => l.trim()).length : 0;
        updateStats(passedCount, hasPhoneCount, needPhoneCount, failedCount);
    } catch (error) {
        addLog(`Lỗi đọc kết quả: ${error.message}`, 'error');
    }
}

// Run
btnRun.addEventListener('click', async () => {
    const accounts = parseAccounts(inputAccounts.value);
    if (accounts.length === 0) {
        addLog('Không có accounts hợp lệ!', 'error');
        return;
    }

    isRunning = true;
    btnRun.disabled = true;
    btnStop.disabled = false;

    await window.api.clearResults();
    resultPassed.value = '';
    resultHasPhone.value = '';
    resultNeedPhone.value = '';
    resultFailed.value = '';
    updateStats(0, 0, 0, 0);
    clearLog();

    addLog(`🚀 Bắt đầu với ${accounts.length} accounts...`, 'info');
    updateProgress(0, accounts.length, 'Đang khởi động...');

    const headless = document.getElementById('save-ram-headless')?.checked || false;
    if (headless) addLog('👻 Chế độ Headless (ẩn browser)', 'info');

    try {
        await window.api.startLogin(accounts, { headless });
    } catch (error) {
        addLog(`Lỗi: ${error.message}`, 'error');
    }
});

btnStop.addEventListener('click', async () => {
    addLog('Đang dừng...', 'warning');
    await window.api.stopLogin();
    isRunning = false;
    btnRun.disabled = false;
    btnStop.disabled = true;
    updateProgress(0, 0, 'Đã dừng');
});

btnCloseAll.addEventListener('click', async () => {
    addLog('✖ Đang tắt tất cả Chrome...', 'warning');
    await window.api.closeAllBrowsers();
    addLog('✅ Đã tắt xong!', 'success');
});

btnClear.addEventListener('click', () => {
    inputAccounts.value = '';
    accountCount.textContent = '0';
});

btnImport.addEventListener('click', () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt';
    input.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                inputAccounts.value = event.target.result;
                const lines = inputAccounts.value.trim().split('\n').filter(l => l.trim() && l.includes('|'));
                accountCount.textContent = lines.length;
                addLog(`Đã import ${lines.length} accounts từ ${file.name}`, 'success');
            };
            reader.readAsText(file);
        }
    };
    input.click();
});

btnCopy.addEventListener('click', () => {
    let content = resultPassed.value;
    if (currentTab === 'has-phone') content = resultHasPhone.value;
    else if (currentTab === 'need-phone') content = resultNeedPhone.value;
    else if (currentTab === 'failed') content = resultFailed.value;
    navigator.clipboard.writeText(content).then(() => {
        addLog('Đã copy vào clipboard!', 'success');
    });
});

btnSave.addEventListener('click', () => {
    let content = resultPassed.value;
    let filename = 'passed_export.txt';
    if (currentTab === 'has-phone') { content = resultHasPhone.value; filename = 'has_phone_export.txt'; }
    else if (currentTab === 'need-phone') { content = resultNeedPhone.value; filename = 'need_phone_export.txt'; }
    else if (currentTab === 'failed') { content = resultFailed.value; filename = 'failed_export.txt'; }
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

// IPC Events
window.api.onLog((data) => addLog(data.message, data.type || 'info'));
window.api.onResult(() => refreshResults());
window.api.onProgress((data) => updateProgress(data.current, data.total, data.text));
window.api.onComplete((data) => {
    isRunning = false;
    btnRun.disabled = false;
    btnStop.disabled = true;
    updateProgress(data.total, data.total, `Hoàn thành! (${data.totalTime}s)`);
    addLog(`✅ Hoàn thành! PASSED: ${data.passed}, HAS_PHONE: ${data.hasPhone}, NEED_PHONE: ${data.needPhone}, FAILED: ${data.failed} (${data.totalTime}s)`, 'success');
    refreshResults();
});

// Temp & Cache management
async function loadTempSize() {
    try {
        const info = await window.api.getTempSize();
        tempSize.textContent = info.sizeMB + ' MB';
        tempCount.textContent = info.folderCount;
        if (info.sizeMB > 100) tempSize.style.color = '#f44336';
        else if (info.sizeMB > 50) tempSize.style.color = '#ff9800';
        else tempSize.style.color = '#4caf50';
    } catch (e) { }
}

async function loadCacheSize() {
    try {
        const result = await window.api.getCacheSize();
        cacheSize.textContent = result.sizeMB + ' MB';
    } catch (e) { cacheSize.textContent = '? MB'; }
}

btnClearTemp.addEventListener('click', async () => {
    if (!confirm('Xóa tất cả Puppeteer temp folders?')) return;
    addLog('🧹 Đang xóa Puppeteer temp...', 'info');
    try {
        const result = await window.api.clearTemp();
        addLog(`✅ Đã xóa ${result.deletedCount} folders`, 'success');
        await loadTempSize();
    } catch (error) {
        addLog(`❌ Lỗi xóa temp: ${error.message}`, 'error');
    }
});

btnClearAll.addEventListener('click', async () => {
    if (!confirm('Xóa tất cả cache Puppeteer/Chromium?\n\n(Không ảnh hưởng Chrome/Edge của bạn)')) return;
    btnClearAll.disabled = true;
    addLog('🗑️ Đang xóa tất cả cache...', 'info');
    try {
        const result = await window.api.clearAllCache();
        addLog(`✅ Đã xóa ${result.deletedCount} items, giải phóng ${result.freedMB} MB`, 'success');
        loadTempSize();
        loadCacheSize();
    } catch (error) {
        addLog(`❌ Lỗi: ${error.message}`, 'error');
    }
    btnClearAll.disabled = false;
});

// Init
loadBrowsers();
loadTempSize();
loadCacheSize();
refreshResults();
addLog('🎓 TDC Login Checker - Sẵn sàng!', 'success');
addLog('📋 Format: email|password (mỗi dòng 1 account)', 'info');
addLog('⚡ Login → Phát hiện Speedbump → Bấm "Tôi hiểu" → Lưu kết quả', 'info');
