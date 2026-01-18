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

// Result textareas
const resultHasFlow = document.getElementById('result-has-flow');
const resultNoFlow = document.getElementById('result-no-flow');
const resultFailed = document.getElementById('result-failed');

// Stats
const statHasFlow = document.getElementById('stat-has-flow');
const statNoFlow = document.getElementById('stat-no-flow');
const statFailed = document.getElementById('stat-failed');
const tabCountHasFlow = document.getElementById('tab-count-has-flow');
const tabCountNoFlow = document.getElementById('tab-count-no-flow');
const tabCountFailed = document.getElementById('tab-count-failed');
const browserSelect = document.getElementById('browser-select');

// State
let isRunning = false;
let currentTab = 'has-flow';
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
    const lines = inputAccounts.value.trim().split('\n').filter(line => line.trim() && line.includes('|'));
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
function updateStats(hasFlow, noFlow, failed) {
    statHasFlow.textContent = hasFlow;
    statNoFlow.textContent = noFlow;
    statFailed.textContent = failed;
    tabCountHasFlow.textContent = hasFlow;
    tabCountNoFlow.textContent = noFlow;
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
        const [email, password] = line.trim().split('|');
        return { email: email?.trim(), password: password?.trim() };
    }).filter(acc => acc.email && acc.password);
}

// Refresh results from files
async function refreshResults() {
    try {
        const results = await window.api.readResults();
        resultHasFlow.value = results.hasFlow;
        resultNoFlow.value = results.noFlow;
        resultFailed.value = results.loginFailed;

        // Count lines
        const hasFlowCount = results.hasFlow ? results.hasFlow.split('\n').filter(l => l.trim()).length : 0;
        const noFlowCount = results.noFlow ? results.noFlow.split('\n').filter(l => l.trim()).length : 0;
        const failedCount = results.loginFailed ? results.loginFailed.split('\n').filter(l => l.trim()).length : 0;

        updateStats(hasFlowCount, noFlowCount, failedCount);
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
    resultHasFlow.value = '';
    resultNoFlow.value = '';
    resultFailed.value = '';
    updateStats(0, 0, 0);
    clearLog();

    addLog(`🚀 Bắt đầu với ${accounts.length} accounts...`, 'info');
    updateProgress(0, accounts.length, 'Đang khởi động...');

    try {
        await window.api.startLogin(accounts);
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
    if (currentTab === 'has-flow') content = resultHasFlow.value;
    else if (currentTab === 'no-flow') content = resultNoFlow.value;
    else content = resultFailed.value;

    navigator.clipboard.writeText(content).then(() => {
        addLog('Đã copy vào clipboard!', 'success');
    });
});

btnSave.addEventListener('click', () => {
    let content = '';
    let filename = '';

    if (currentTab === 'has-flow') {
        content = resultHasFlow.value;
        filename = 'has_flow_export.txt';
    } else if (currentTab === 'no-flow') {
        content = resultNoFlow.value;
        filename = 'no_flow_export.txt';
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

// Initial load
loadBrowsers();
refreshResults();
addLog('Sẵn sàng!', 'success');
