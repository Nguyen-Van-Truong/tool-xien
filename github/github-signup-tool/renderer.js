/**
 * GitHub Signup Tool - Renderer
 * Frontend logic, IPC events, UI state management
 */

// ==================== State ====================
let accounts = [];
let successList = [];
let failedList = [];
let isRunning = false;
let isPaused = false;
let isWaitingManual = false;

// ==================== DOM ====================
const $ = (sel) => document.querySelector(sel);
const inputAccounts = $('#input-accounts');
const accountCount = $('#account-count');
const btnRun = $('#btn-run');
const btnStop = $('#btn-stop');
const btnCloseAll = $('#btn-close-all');
const browserCountBtn = $('#browser-count-btn');
const btnDone = $('#btn-done');
const btnFail = $('#btn-fail');
const manualControls = $('#manual-controls');
const manualStatusText = $('#manual-status-text');
const statusBar = $('#status-bar');
const statusDot = statusBar.querySelector('.status-dot');
const statusText = $('#status-text');
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
const btnClearResults = $('#btn-clear-results');
const btnCopy = $('#btn-copy');
const btnSave = $('#btn-save');
const btnRefresh = $('#btn-refresh');
const btnClearLog = $('#btn-clear-log');
const btnDeleteData = $('#btn-delete-browser-data');
const btnRefreshTemp = $('#btn-refresh-temp');
const tempSizeDisplay = $('#temp-size-display');

// ==================== Logging ====================
function log(msg, type = 'info') {
    if (!msg && !msg.trim) return;
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    const ts = new Date().toLocaleTimeString('vi-VN');
    entry.textContent = `[${ts}] ${msg}`;
    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;

    // Keep log manageable
    while (logContainer.children.length > 500) {
        logContainer.removeChild(logContainer.firstChild);
    }
}

// ==================== Account Parsing ====================
function parseAccounts(text) {
    if (!text || !text.trim()) return [];
    const lines = text.trim().split('\n').filter(l => l.trim());
    return lines.map(line => {
        const parts = line.trim().split('|');
        if (parts.length < 2) return null;
        const email = parts[0].trim();
        const password = parts[1].trim();
        if (!email || !password) return null;
        const username = email.split('@')[0].replace(/[^a-zA-Z0-9_-]/g, '').substring(0, 39);
        // Optional: refresh_token (field 3) and client_id (field 4) for auto-OTP
        const refreshToken = parts.length >= 3 ? parts[2].trim() : '';
        const clientId = parts.length >= 4 ? parts[3].trim() : '';
        return { email, password, username, refreshToken, clientId };
    }).filter(Boolean);
}

inputAccounts.addEventListener('input', () => {
    const parsed = parseAccounts(inputAccounts.value);
    accountCount.textContent = parsed.length;
});

// ==================== Status ====================
function setStatus(state, text) {
    statusDot.className = `status-dot status-${state}`;
    statusText.textContent = text;
}

// ==================== Settings ====================
function getSettings() {
    return {
        headless: $('#headless-mode').checked,
        keepBrowser: $('#keep-browsers').checked,
        autoClickCreate: $('#auto-click-create').checked,
        autofillDelay: parseFloat($('#autofill-delay').value) || 1.5,
        typingDelay: parseInt($('#typing-delay').value) || 50
    };
}

function loadSettings() {
    try {
        const saved = localStorage.getItem('github_signup_settings');
        if (saved) {
            const s = JSON.parse(saved);
            $('#headless-mode').checked = !!s.headless;
            $('#keep-browsers').checked = s.keepBrowser !== false;
            $('#auto-click-create').checked = s.autoClickCreate !== false;
            $('#autofill-delay').value = s.autofillDelay || 1.5;
            $('#typing-delay').value = s.typingDelay || 50;
        }
    } catch (e) { }
}

function saveSettings() {
    const settings = getSettings();
    localStorage.setItem('github_signup_settings', JSON.stringify(settings));
    log('✅ Settings đã lưu!', 'success');
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

// ==================== Update UI ====================
function updateStats() {
    statSuccess.textContent = successList.length;
    statFailed.textContent = failedList.length;
    tabCountSuccess.textContent = successList.length;
    tabCountFailed.textContent = failedList.length;
}

function updateBrowserCountUI(count) {
    statBrowsers.textContent = count;
    browserCountBtn.textContent = count;
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

function setRunningState(running) {
    isRunning = running;
    isPaused = false;
    btnRun.disabled = running;
    btnStop.disabled = !running;
    inputAccounts.disabled = running;

    if (running) {
        setStatus('running', 'Đang chạy...');
    } else {
        hideManualControls();
        if (successList.length + failedList.length > 0) {
            setStatus('done', `Xong! ✅${successList.length} ❌${failedList.length}`);
        } else {
            setStatus('ready', 'Ready');
        }
    }
}

function showManualControls(email, username, autoOTP = false) {
    isWaitingManual = true;
    manualControls.classList.remove('hidden');
    if (autoOTP) {
        manualStatusText.textContent = `🔄 Giải CAPTCHA → Auto OTP: ${email}`;
        setStatus('waiting', `🔄 Auto-OTP: ${email}`);
    } else {
        manualStatusText.textContent = `Chờ captcha: ${email} (${username})`;
        setStatus('waiting', `Chờ: ${email}`);
    }
}

function hideManualControls() {
    isWaitingManual = false;
    manualControls.classList.add('hidden');
}

// ==================== Start Signup ====================
btnRun.addEventListener('click', async () => {
    const parsed = parseAccounts(inputAccounts.value);
    if (parsed.length === 0) {
        log('❌ Không có account hợp lệ! Format: email|password', 'error');
        return;
    }

    accounts = parsed;
    successList = [];
    failedList = [];
    resultSuccess.value = '';
    resultFailed.value = '';
    updateStats();
    setProgress(0, accounts.length);
    setRunningState(true);

    log(`▶️ Bắt đầu signup ${accounts.length} account(s)...`, 'highlight');

    const settings = getSettings();
    try {
        await window.api.startSignup(accounts, settings);
    } catch (err) {
        log(`❌ Error: ${err.message}`, 'error');
    }
    setRunningState(false);
});

// ==================== Stop/Pause ====================
btnStop.addEventListener('click', async () => {
    log('⏸️ Đang dừng... (browsers vẫn mở)', 'warning');
    try {
        await window.api.stopSignup();
    } catch (e) { }
    isPaused = true;
    btnStop.disabled = true;
    btnRun.disabled = false;
    inputAccounts.disabled = false;
    setStatus('paused', 'Đã dừng (browsers vẫn mở)');
});

// ==================== Manual Done / Failed ====================
btnDone.addEventListener('click', async () => {
    log('✅ User đánh dấu DONE', 'success');
    hideManualControls();
    setStatus('running', 'Đang tiếp tục...');
    try { await window.api.nextAccount('done'); } catch (e) { }
});

btnFail.addEventListener('click', async () => {
    log('❌ User đánh dấu FAILED', 'error');
    hideManualControls();
    setStatus('running', 'Đang tiếp tục...');
    try { await window.api.nextAccount('failed'); } catch (e) { }
});

// ==================== Close All Browsers ====================
btnCloseAll.addEventListener('click', async () => {
    log('🗑️ Đang đóng tất cả browsers...', 'warning');
    try {
        await window.api.closeAllBrowsers();
        updateBrowserCountUI(0);
        log('✅ Đã đóng tất cả browsers.', 'info');
    } catch (e) { }
});

// ==================== IPC Listeners ====================

// Log messages from worker
window.api.onLog((data) => {
    const msg = typeof data === 'string' ? data : (data.message || data || '');
    if (!msg.toString().trim()) return;

    let type = 'info';
    const lmsg = msg.toString().toLowerCase();
    if (lmsg.includes('thành công') || lmsg.includes('success') || lmsg.includes('✅')) type = 'success';
    else if (lmsg.includes('lỗi') || lmsg.includes('error') || lmsg.includes('fail') || lmsg.includes('❌') || lmsg.includes('thất bại')) type = 'error';
    else if (lmsg.includes('warn') || lmsg.includes('⚠') || lmsg.includes('chờ') || lmsg.includes('dừng') || lmsg.includes('⏸')) type = 'warning';
    else if (lmsg.includes('━━') || lmsg.includes('═══') || lmsg.includes('📌') || lmsg.includes('🚀')) type = 'highlight';

    log(msg, type);
});

// Individual result
window.api.onResult((result) => {
    const { email, password, username, status, error, timestamp } = result;
    if (status === 'success') {
        successList.push(result);
        resultSuccess.value += `${email}|${password}|${username}\n`;
    } else {
        failedList.push(result);
        resultFailed.value += `${email}|${password}|${error || 'Unknown'}|${timestamp || ''}\n`;
    }
    updateStats();
});

// Progress
window.api.onProgress((data) => {
    const { current, total, text } = data;
    setProgress(current, total, text || `${current}/${total}`);
});

// Waiting for manual
window.api.onWaitingManual((data) => {
    showManualControls(data.email, data.username || '', data.autoOTP || false);
});

// OTP auto-fetch status
window.api.onOTPStatus((data) => {
    const { status, code, email } = data;
    switch (status) {
        case 'fetching':
            log(`📧 Đang lấy OTP từ email ${email || ''}...`, 'highlight');
            manualStatusText.textContent = `📧 Đang lấy OTP từ email...`;
            break;
        case 'filling':
            log(`🔑 OTP: ${code} - Đang nhập...`, 'success');
            manualStatusText.textContent = `🔑 OTP: ${code} - Đang nhập...`;
            break;
        case 'success':
            log('✅ Auto-OTP thành công!', 'success');
            break;
        case 'filled':
            log(`✅ Đã nhập OTP: ${code} - Chờ xác minh...`, 'success');
            manualStatusText.textContent = `✅ Đã nhập OTP: ${code}`;
            break;
        case 'failed':
            log('⚠️ Auto-OTP thất bại - Nhập thủ công', 'warning');
            manualStatusText.textContent = `⚠️ Auto-OTP thất bại - Nhập OTP thủ công`;
            break;
    }
});

// Browser count
window.api.onBrowserCount((data) => {
    updateBrowserCountUI(data.active || 0);
});

// Complete
window.api.onComplete((data) => {
    const { total, success, failed, totalTime } = data;
    setRunningState(false);
    setProgress(total, total, `Done! ✅${success} ❌${failed} ⏱${totalTime}s`);
    log('', 'info');
    log(`🎉 ═══════ HOÀN THÀNH ═══════`, 'success');
    log(`📊 Total: ${total} | Success: ${success} | Failed: ${failed} | Time: ${totalTime}s`, 'success');
});

// ==================== Results Buttons ====================
btnCopy.addEventListener('click', () => {
    const activeTab = document.querySelector('.tab.active').dataset.tab;
    const text = activeTab === 'success' ? resultSuccess.value : resultFailed.value;
    if (!text.trim()) {
        log('ℹ️ Không có dữ liệu để copy', 'warning');
        return;
    }
    navigator.clipboard.writeText(text).then(() => {
        log(`📋 Đã copy ${activeTab} results!`, 'success');
    });
});

btnSave.addEventListener('click', () => {
    const activeTab = document.querySelector('.tab.active').dataset.tab;
    const text = activeTab === 'success' ? resultSuccess.value : resultFailed.value;
    if (!text.trim()) {
        log('ℹ️ Không có dữ liệu để lưu', 'warning');
        return;
    }
    const blob = new Blob([text], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `github_${activeTab}_${Date.now()}.txt`;
    a.click();
    log(`💾 Đã lưu ${activeTab} results!`, 'success');
});

btnRefresh.addEventListener('click', async () => {
    try {
        const results = await window.api.readResults();
        if (results) {
            if (results.success) {
                resultSuccess.value = results.success;
                successList = results.success.split('\n').filter(l => l.trim());
            } else {
                resultSuccess.value = '';
                successList = [];
            }
            if (results.failed) {
                resultFailed.value = results.failed;
                failedList = results.failed.split('\n').filter(l => l.trim());
            } else {
                resultFailed.value = '';
                failedList = [];
            }
            updateStats();
            log('🔄 Đã refresh kết quả từ file.', 'info');
        }
    } catch (e) {
        log('⚠️ Không tìm thấy file kết quả', 'warning');
    }
});

btnClearResults.addEventListener('click', async () => {
    try {
        await window.api.clearResults();
        resultSuccess.value = '';
        resultFailed.value = '';
        successList = [];
        failedList = [];
        updateStats();
        log('🗑️ Đã xóa kết quả.', 'info');
    } catch (e) { }
});

// ==================== Log ====================
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

// Close settings when clicking outside
settingsPanel.addEventListener('click', (e) => {
    if (e.target === settingsPanel) settingsPanel.classList.add('hidden');
});

btnSaveSettings.addEventListener('click', saveSettings);

btnDeleteData.addEventListener('click', async () => {
    log('🗑️ Đang xóa browser data...', 'warning');
    try {
        const result = await window.api.deleteBrowserData();
        log(`✅ Đã xóa ${result.deletedCount} folder(s), giải phóng ${result.freedMB} MB`, 'success');
        refreshTempSize();
    } catch (e) {
        log('❌ Lỗi khi xóa browser data', 'error');
    }
});

async function refreshTempSize() {
    try {
        const size = await window.api.getTempSize();
        tempSizeDisplay.textContent = `📦 ${size.sizeMB} MB (${size.folderCount} folders)`;
    } catch (e) {
        tempSizeDisplay.textContent = '❓ Không đọc được';
    }
}

btnRefreshTemp.addEventListener('click', refreshTempSize);

// ==================== Init ====================
loadSettings();
setStatus('ready', 'Ready');
log('🐙 GitHub Signup Tool ready!', 'success');
log('📝 Format: email|password|refresh_token|client_id', 'info');
log('ℹ️ Có refresh_token + client_id → tự động lấy OTP', 'info');
log('ℹ️ Không có → chế độ thủ công (Done/Failed)', 'info');
