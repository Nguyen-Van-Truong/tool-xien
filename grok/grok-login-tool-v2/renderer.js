/**
 * Renderer Process - Frontend Logic
 * Grok Login + Payment Tool V2
 */

// DOM Elements
const inputAccounts = document.getElementById('input-accounts');
const inputCards = document.getElementById('input-cards');
const accountCount = document.getElementById('account-count');
const cardCount = document.getElementById('card-count');

const btnRun = document.getElementById('btn-run');
const btnStop = document.getElementById('btn-stop');
const btnCloseAll = document.getElementById('btn-close-all');
const btnCopy = document.getElementById('btn-copy');
const btnSave = document.getElementById('btn-save');
const btnRefresh = document.getElementById('btn-refresh');
const btnClearLog = document.getElementById('btn-clear-log');
const logContainer = document.getElementById('log-container');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');

// Result textareas
const resultSuccess = document.getElementById('result-success');
const resultFailed = document.getElementById('result-failed');

// Stats
const statSuccess = document.getElementById('stat-success');
const statFailed = document.getElementById('stat-failed');
const tabCountSuccess = document.getElementById('tab-count-success');
const tabCountFailed = document.getElementById('tab-count-failed');
const statBrowsers = document.getElementById('stat-browsers');

// State
let isRunning = false;
let currentTab = 'success';

// Settings
const settings = {
    maxConcurrent: 3,
    headless: false,
    keepBrowsers: true,
    // Autofill settings (like Propaganda extension)
    autofillDelay: 7,
    randomName: true,
    randomAddress: true,
    autoSubmitPayment: true, // Tự động bấm Submit sau khi điền form
    // Default billing info (used when random is OFF)
    billingName: '',
    billingAddress1: '',
    billingAddress2: '',
    billingCity: '',
    billingState: '',
    billingZip: ''
};

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
        if (parts.length >= 2) {
            return {
                email: parts[0].trim(),
                password: parts[1].trim()
            };
        }
        return null;
    }).filter(acc => acc && acc.email && acc.password);
}

// Parse cards from input
function parseCards(text) {
    const lines = text.trim().split('\n').filter(line => line.trim());
    return lines.map(line => {
        const parts = line.trim().split('|');
        if (parts.length >= 4) {
            return {
                number: parts[0].trim(),
                month: parts[1].trim(),
                year: parts[2].trim(),
                cvc: parts[3].trim()
            };
        }
        return null;
    }).filter(card => card && card.number && card.month && card.year && card.cvc);
}

// Refresh results from files
async function refreshResults() {
    try {
        const results = await window.api.readResults();
        resultSuccess.value = results.success;
        resultFailed.value = results.failed;

        const successCount = results.success ? results.success.split('\n').filter(l => l.trim()).length : 0;
        const failedCount = results.failed ? results.failed.split('\n').filter(l => l.trim()).length : 0;

        updateStats(successCount, failedCount);
    } catch (error) {
        addLog(`Lỗi đọc kết quả: ${error.message}`, 'error');
    }
}

// Update counts on input
inputAccounts.addEventListener('input', () => {
    const accounts = parseAccounts(inputAccounts.value);
    accountCount.textContent = accounts.length;
});

inputCards.addEventListener('input', () => {
    const cards = parseCards(inputCards.value);
    cardCount.textContent = cards.length;
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

// Run button handler
btnRun.addEventListener('click', async () => {
    const accounts = parseAccounts(inputAccounts.value);
    const cards = parseCards(inputCards.value);

    if (accounts.length === 0) {
        addLog('❌ Không có accounts hợp lệ!', 'error');
        return;
    }

    if (cards.length === 0) {
        addLog('❌ Không có cards hợp lệ!', 'error');
        return;
    }

    isRunning = true;
    btnRun.disabled = true;
    btnStop.disabled = false;

    addLog('🗑️ Xóa kết quả cũ...', 'info');
    await window.api.clearResults();

    resultSuccess.value = '';
    resultFailed.value = '';
    updateStats(0, 0);
    clearLog();

    addLog(`🚀 Bắt đầu với ${accounts.length} accounts và ${cards.length} cards...`, 'info');
    updateProgress(0, accounts.length, 'Đang khởi động...');

    try {
        await window.api.startProcess(accounts, cards, {
            headless: settings.headless,
            maxConcurrent: settings.maxConcurrent,
            keepBrowserOpen: settings.keepBrowsers,
            // Autofill options (like Propaganda extension)
            autofillDelay: settings.autofillDelay,
            randomName: settings.randomName,
            randomAddress: settings.randomAddress,
            autoSubmitPayment: settings.autoSubmitPayment,
            billingInfo: {
                name: settings.billingName,
                address1: settings.billingAddress1,
                address2: settings.billingAddress2,
                city: settings.billingCity,
                state: settings.billingState,
                zip: settings.billingZip
            }
        });
    } catch (error) {
        addLog(`Lỗi: ${error.message}`, 'error');
    }
});

btnStop.addEventListener('click', async () => {
    addLog('Đang dừng...', 'warning');
    await window.api.stopProcess();
    isRunning = false;
    btnRun.disabled = false;
    btnStop.disabled = true;
    updateProgress(0, 0, 'Đã dừng');
});

btnCloseAll.addEventListener('click', async () => {
    addLog('✖ Đang tắt tất cả browsers...', 'warning');
    await window.api.closeAllBrowsers();
    addLog('✅ Đã tắt xong!', 'success');
});

btnCopy.addEventListener('click', () => {
    let content = currentTab === 'success' ? resultSuccess.value : resultFailed.value;
    navigator.clipboard.writeText(content).then(() => {
        addLog('Đã copy vào clipboard!', 'success');
    });
});

btnSave.addEventListener('click', () => {
    let content = '';
    let filename = '';

    if (currentTab === 'success') {
        content = resultSuccess.value;
        filename = 'grok_payment_success.txt';
    } else {
        content = resultFailed.value;
        filename = 'grok_payment_failed.txt';
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
    addLog(`🎉 Hoàn thành! SUCCESS: ${data.success}, FAILED: ${data.failed}`, 'success');
    refreshResults();
});

window.api.onBrowserCount((data) => {
    statBrowsers.textContent = `${data.active}/${data.max}`;
    if (data.active >= data.max) {
        statBrowsers.parentElement.style.color = 'var(--accent-yellow)';
    } else if (data.active > 0) {
        statBrowsers.parentElement.style.color = 'var(--accent-blue)';
    } else {
        statBrowsers.parentElement.style.color = 'var(--text-secondary)';
    }
});

// Settings elements
const btnSettings = document.getElementById('btn-settings');
const btnCloseSettings = document.getElementById('btn-close-settings');
const btnSaveSettings = document.getElementById('btn-save-settings');
const settingsPanel = document.getElementById('settings-panel');

btnSettings?.addEventListener('click', () => {
    settingsPanel.classList.remove('hidden');
    document.getElementById('max-concurrent').value = settings.maxConcurrent;
    document.getElementById('headless-mode').checked = settings.headless;
    document.getElementById('keep-browsers').checked = settings.keepBrowsers;
    // Autofill settings
    document.getElementById('autofill-delay').value = settings.autofillDelay;
    document.getElementById('random-name').checked = settings.randomName;
    document.getElementById('random-address').checked = settings.randomAddress;
    document.getElementById('auto-submit-payment').checked = settings.autoSubmitPayment;
    // Billing info
    document.getElementById('billing-name').value = settings.billingName;
    document.getElementById('billing-address1').value = settings.billingAddress1;
    document.getElementById('billing-address2').value = settings.billingAddress2;
    document.getElementById('billing-city').value = settings.billingCity;
    document.getElementById('billing-state').value = settings.billingState;
    document.getElementById('billing-zip').value = settings.billingZip;
});

btnCloseSettings?.addEventListener('click', () => {
    settingsPanel.classList.add('hidden');
});

btnSaveSettings?.addEventListener('click', () => {
    settings.maxConcurrent = parseInt(document.getElementById('max-concurrent').value);
    settings.headless = document.getElementById('headless-mode').checked;
    settings.keepBrowsers = document.getElementById('keep-browsers').checked;
    // Autofill settings
    settings.autofillDelay = parseFloat(document.getElementById('autofill-delay').value) || 7;
    settings.randomName = document.getElementById('random-name').checked;
    settings.randomAddress = document.getElementById('random-address').checked;
    settings.autoSubmitPayment = document.getElementById('auto-submit-payment').checked;
    // Billing info
    settings.billingName = document.getElementById('billing-name').value.trim();
    settings.billingAddress1 = document.getElementById('billing-address1').value.trim();
    settings.billingAddress2 = document.getElementById('billing-address2').value.trim();
    settings.billingCity = document.getElementById('billing-city').value.trim();
    settings.billingState = document.getElementById('billing-state').value.trim();
    settings.billingZip = document.getElementById('billing-zip').value.trim();
    settingsPanel.classList.add('hidden');
    addLog(`⚙️ Settings saved: ${settings.maxConcurrent} concurrent, delay=${settings.autofillDelay}s, autoSubmit=${settings.autoSubmitPayment}`, 'success');
});

// Delete browser data button
const btnDeleteBrowserDataTemp = document.getElementById('btn-delete-browser-data-temp');
const btnRefreshTemp = document.getElementById('btn-refresh-temp');
const tempSizeDisplay = document.getElementById('temp-size-display');

async function loadTempSize() {
    try {
        const info = await window.api.getTempSize();
        tempSizeDisplay.textContent = `📁 ${info.folderCount} folders (${info.sizeMB} MB)`;
        
        if (info.sizeMB > 100) {
            tempSizeDisplay.style.color = '#ff4757';
        } else if (info.sizeMB > 50) {
            tempSizeDisplay.style.color = '#ffc107';
        } else {
            tempSizeDisplay.style.color = '#00d26a';
        }
    } catch (error) {
        tempSizeDisplay.textContent = '❌ Error loading';
        console.log('Error loading temp size:', error);
    }
}

btnRefreshTemp?.addEventListener('click', async () => {
    tempSizeDisplay.textContent = '⏳ Checking...';
    await loadTempSize();
});

btnDeleteBrowserDataTemp?.addEventListener('click', async () => {
    const confirmed = confirm('⚠️ Xóa toàn bộ Puppeteer browser data?\n\nĐiều này sẽ xóa cache, cookies, và temp files.\nBạn có chắc chắn?');

    if (!confirmed) return;

    btnDeleteBrowserDataTemp.disabled = true;
    btnDeleteBrowserDataTemp.textContent = '⏳ Đang xóa...';
    addLog('🗑️ Deleting Puppeteer data...', 'info');

    try {
        const result = await window.api.deleteBrowserData();
        addLog(`✅ Deleted ${result.deletedCount} folders`, 'success');
        alert(`✅ Xóa thành công!\n\nFolders deleted: ${result.deletedCount}`);
        await loadTempSize();
    } catch (error) {
        addLog(`❌ Error: ${error.message}`, 'error');
        alert(`❌ Lỗi: ${error.message}`);
    }

    btnDeleteBrowserDataTemp.disabled = false;
    btnDeleteBrowserDataTemp.textContent = '🗑️ Clear Temp Folders';
});

// Initial load
refreshResults();
loadTempSize();
addLog('🤖 Grok Login + Payment Tool V2 sẵn sàng!', 'success');
addLog('📋 Nhập accounts (email|password) và cards (number|MM|YYYY|CVC)', 'info');
