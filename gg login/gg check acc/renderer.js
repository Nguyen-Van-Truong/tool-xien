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

//  Result textareas
const resultLoginOk = document.getElementById('result-login-ok');
const resultNeed2fa = document.getElementById('result-need-2fa');
const resultFailed = document.getElementById('result-failed');

// Stats
const statLoginOk = document.getElementById('stat-login-ok');
const statNeed2fa = document.getElementById('stat-need-2fa');
const statFailed = document.getElementById('stat-failed');
const tabCountLoginOk = document.getElementById('tab-count-login-ok');
const tabCountNeed2fa = document.getElementById('tab-count-need-2fa');
const tabCountFailed = document.getElementById('tab-count-failed');
const browserSelect = document.getElementById('browser-select');
const tempSize = document.getElementById('temp-size');
const tempCount = document.getElementById('temp-count');
const btnClearTemp = document.getElementById('btn-clear-temp');

// State
let isRunning = false;
let currentTab = 'login-ok';
let detectedBrowsers = [];

// Load danh sách browsers khi app khởi động
async function loadBrowsers() {
    try {
        detectedBrowsers = await window.api.detectBrowsers();
        browserSelect.innerHTML = '';

        const availableBrowsers = detectedBrowsers.filter(b => b.detected);
        const unavailableBrowsers = detectedBrowsers.filter(b => !b.detected);

        if (availableBrowsers.length === 0) {
            browserSelect.innerHTML = '<option value="" disabled>Không tìm thấy browser!</option>';
            addLog('❌ Không tìm thấy trình duyệt Chromium nào!', 'error');
            return;
        }

        // Thêm browsers available
        availableBrowsers.forEach((browser, index) => {
            const option = document.createElement('option');
            option.value = browser.id;
            option.textContent = `✓ ${browser.name}`;
            if (index === 0) option.selected = true;
            browserSelect.appendChild(option);
        });

        // Thêm separator và browsers unavailable
        if (unavailableBrowsers.length > 0) {
            const separator = document.createElement('option');
            separator.disabled = true;
            separator.textContent = '───────────';
            browserSelect.appendChild(separator);

            unavailableBrowsers.forEach(browser => {
                const option = document.createElement('option');
                option.value = browser.id;
                option.disabled = true;
                option.textContent = `✗ ${browser.name} (không có)`;
                browserSelect.appendChild(option);
            });
        }

        // Set default browser
        await window.api.setBrowser(availableBrowsers[0].id);
        addLog(`🌐 Đã chọn: ${availableBrowsers[0].name}`, 'success');

    } catch (error) {
        addLog(`Lỗi detect browsers: ${error.message}`, 'error');
    }
}

// Load Puppeteer temp size
async function loadTempSize() {
    try {
        const info = await window.api.getTempSize();
        tempSize.textContent = info.sizeMB + ' MB';
        tempCount.textContent = info.folderCount;

        // Highlight nếu dung lượng lớn
        if (info.sizeMB > 100) {
            tempSize.style.color = '#f44336'; // Red
        } else if (info.sizeMB > 50) {
            tempSize.style.color = '#ff9800'; // Orange
        } else {
            tempSize.style.color = '#4caf50'; // Green
        }
    } catch (error) {
        console.log('Error loading temp size:', error);
    }
}

// Clear Puppeteer temp
btnClearTemp.addEventListener('click', async () => {
    const confirm = window.confirm('Xóa tất cả Puppeteer temp folders?');
    if (!confirm) return;

    addLog('🧹 Đang xóa Puppeteer temp...', 'info');

    try {
        const result = await window.api.clearTemp();
        addLog(`✅ Đã xóa ${result.deletedCount} folders`, 'success');
        await loadTempSize(); // Refresh size
    } catch (error) {
        addLog(`❌ Lỗi xóa temp: ${error.message}`, 'error');
    }
});

// Clear All Cache button
const btnClearAll = document.getElementById('btn-clear-all');
const cacheSize = document.getElementById('cache-size');

// Load cache size
async function loadCacheSize() {
    try {
        const result = await window.api.getCacheSize();
        cacheSize.textContent = `${result.sizeMB} MB`;
    } catch (error) {
        cacheSize.textContent = '? MB';
    }
}

btnClearAll.addEventListener('click', async () => {
    if (!confirm('Xóa tất cả cache Puppeteer/Chromium?\n\n(Không ảnh hưởng Chrome/Edge/Firefox của bạn)')) {
        return;
    }

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

// Handle browser change
browserSelect.addEventListener('change', async () => {
    const browserId = browserSelect.value;
    const browser = detectedBrowsers.find(b => b.id === browserId);

    if (browser) {
        await window.api.setBrowser(browserId);
        addLog(`🌐 Đã chọn: ${browser.name}`, 'success');
    }
});

// Update account count on input
inputAccounts.addEventListener('input', () => {
    const lines = inputAccounts.value.trim().split('\n').filter(line => {
        const trimmed = line.trim();
        return trimmed && (trimmed.includes('|') || trimmed.includes('\t') || trimmed.includes(' '));
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
function updateStats(loginOk, need2fa, failed) {
    statLoginOk.textContent = loginOk;
    statNeed2fa.textContent = need2fa;
    statFailed.textContent = failed;
    tabCountLoginOk.textContent = loginOk;
    tabCountNeed2fa.textContent = need2fa;
    tabCountFailed.textContent = failed;
}

// Update progress
function updateProgress(current, total, text) {
    const percent = total > 0 ? (current / total) * 100 : 0;
    progressBar.style.setProperty('--progress', `${percent}%`);
    progressText.textContent = text || `${current}/${total}`;
}

// Parse accounts from input - hỗ trợ: email|pass|2fa_secret
function parseAccounts(text) {
    const lines = text.trim().split('\n').filter(line => line.trim());
    return lines.map(line => {
        const trimmedLine = line.trim();
        let email, password, twoFASecret;

        // Thử các separator theo thứ tự ưu tiên
        if (trimmedLine.includes('|')) {
            // Format: email|pass or email|pass|2fa_secret
            const parts = trimmedLine.split('|');
            email = parts[0];
            password = parts[1];
            twoFASecret = parts[2] || null;
        } else if (trimmedLine.includes('\t')) {
            // Format: email\tpass\t2fa (tab)
            const parts = trimmedLine.split('\t');
            email = parts[0];
            password = parts[1];
            twoFASecret = parts[2] || null;
        } else if (trimmedLine.includes(' ')) {
            // Format: email pass 2fa (khoảng trắng)
            const parts = trimmedLine.split(/\s+/);
            email = parts[0];
            password = parts[1];
            twoFASecret = parts[2] || null;
        }

        return {
            email: email?.trim(),
            password: password?.trim(),
            twoFASecret: twoFASecret?.trim() || null
        };
    }).filter(acc => acc.email && acc.password);
}

async function refreshResults() {
    try {
        const results = await window.api.readResults();
        resultLoginOk.value = results.loginOk;
        resultNeed2fa.value = results.need2fa;
        resultFailed.value = results.loginFailed;

        // Count lines
        const loginOkCount = results.loginOk ? results.loginOk.split('\n').filter(l => l.trim()).length : 0;
        const need2faCount = results.need2fa ? results.need2fa.split('\n').filter(l => l.trim()).length : 0;
        const failedCount = results.loginFailed ? results.loginFailed.split('\n').filter(l => l.trim()).length : 0;

        updateStats(loginOkCount, need2faCount, failedCount);
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
    resultLoginOk.value = '';
    resultNeed2fa.value = '';
    resultFailed.value = '';
    updateStats(0, 0, 0);
    clearLog();

    addLog(`🚀 Bắt đầu với ${accounts.length} accounts...`, 'info');
    updateProgress(0, accounts.length, 'Đang khởi động...');

    // RAM saving options
    const headless = document.getElementById('save-ram-headless')?.checked || false;
    const ramFlags = document.getElementById('save-ram-flags')?.checked || false;

    if (headless) addLog('👻 Chế độ Headless (ẩn browser)', 'info');
    if (ramFlags) addLog('⚡ Áp dụng RAM flags', 'info');

    try {
        await window.api.startLogin(accounts, { headless, ramFlags });
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

// Tắt tất cả browsers
btnCloseAll.addEventListener('click', async () => {
    addLog('✖ Đang tắt tất cả Chrome...', 'warning');
    await window.api.closeAllBrowsers();
    addLog('✅ Đã tắt xong!', 'success');
});

btnClear.addEventListener('click', () => {
    inputAccounts.value = '';
    accountCount.textContent = '0';
});

btnImport.addEventListener('click', async () => {
    // Create file input
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt';
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                inputAccounts.value = event.target.result;
                const lines = inputAccounts.value.trim().split('\n').filter(line => line.trim() && line.includes('|'));
                accountCount.textContent = lines.length;
                addLog(`Đã import ${lines.length} accounts từ ${file.name}`, 'success');
            };
            reader.readAsText(file);
        }
    };
    input.click();
});

btnCopy.addEventListener('click', () => {
    let content = '';
    if (currentTab === 'login-ok') content = resultLoginOk.value;
    else if (currentTab === 'need-2fa') content = resultNeed2fa.value;
    else content = resultFailed.value;

    navigator.clipboard.writeText(content).then(() => {
        addLog('Đã copy vào clipboard!', 'success');
    });
});

btnSave.addEventListener('click', () => {
    let content = '';
    let filename = '';

    if (currentTab === 'login-ok') {
        content = resultLoginOk.value;
        filename = 'login_ok_export.txt';
    } else if (currentTab === 'need-2fa') {
        content = resultNeed2fa.value;
        filename = 'need_2fa_export.txt';
    } else {
        content = resultFailed.value;
        filename = 'login_failed_export.txt';
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
    addLog(`Hoàn thành! HAS_FLOW: ${data.hasFlow}, NO_FLOW: ${data.noFlow}, FAILED: ${data.failed}`, 'success');
    refreshResults();
});

// Download Browser
const btnDownloadBrowser = document.getElementById('btn-download-browser');
const downloadProgress = document.getElementById('download-progress');
const downloadStatus = document.getElementById('download-status');
const downloadBar = document.getElementById('download-bar');
const downloadPercent = document.getElementById('download-percent');

btnDownloadBrowser.addEventListener('click', async () => {
    btnDownloadBrowser.disabled = true;
    downloadProgress.style.display = 'inline-block';
    downloadStatus.textContent = 'Đang khởi động...';
    downloadBar.value = 0;
    downloadPercent.textContent = '0%';
    addLog('📥 Bắt đầu tải Chromium...', 'info');

    try {
        const result = await window.api.downloadBrowser();
        if (result.success) {
            addLog(`✅ Tải thành công: ${result.path}`, 'success');
            // Reload browser list
            loadBrowsers();
        } else {
            addLog(`❌ Lỗi: ${result.error}`, 'error');
        }
    } catch (error) {
        addLog(`❌ Lỗi: ${error.message}`, 'error');
    }

    btnDownloadBrowser.disabled = false;
    setTimeout(() => {
        downloadProgress.style.display = 'none';
    }, 3000);
});

// Download progress listener
window.api.onDownloadProgress((data) => {
    downloadStatus.textContent = data.status;
    downloadBar.value = data.percent;
    downloadPercent.textContent = `${data.percent}%`;
});

// Check browser on load
async function checkBrowserExists() {
    const result = await window.api.checkBrowserExists();
    if (!result.exists) {
        addLog('⚠️ Chưa có Chromium! Bấm nút "📥 Tải Browser" để tải.', 'warning');
        btnDownloadBrowser.style.background = '#ff9800';
    }
}

// Initial load
loadBrowsers();
loadTempSize();
loadCacheSize();
refreshResults();
checkBrowserExists();
addLog('Sẵn sàng!', 'success');

