// DOM Elements - Config
const adminAccount = document.getElementById('admin-account');
const adminCookies = document.getElementById('admin-cookies');
const passwordLoginSection = document.getElementById('password-login-section');
const cookiesLoginSection = document.getElementById('cookies-login-section');
const commonPassword = document.getElementById('common-password');
const randomCount = document.getElementById('random-count');
const inputAccounts = document.getElementById('input-accounts');
const accountCount = document.getElementById('account-count');
const browserSelect = document.getElementById('browser-select');

// DOM Elements - Buttons
const btnRun = document.getElementById('btn-run');
const btnResume = document.getElementById('btn-resume');
const btnStop = document.getElementById('btn-stop');
const btnCloseBrowser = document.getElementById('btn-close-browser');
const btnGenerate = document.getElementById('btn-generate');
const btnClearInput = document.getElementById('btn-clear-input');
const btnCopy = document.getElementById('btn-copy');
const btnSave = document.getElementById('btn-save');
const btnRefresh = document.getElementById('btn-refresh');
const btnClearLog = document.getElementById('btn-clear-log');
const btnClearTemp = document.getElementById('btn-clear-temp');

// DOM Elements - Results
const resultCreated = document.getElementById('result-created');
const resultFailed = document.getElementById('result-failed');
const statCreated = document.getElementById('stat-created');
const statFailed = document.getElementById('stat-failed');
const tabCountCreated = document.getElementById('tab-count-created');
const tabCountFailed = document.getElementById('tab-count-failed');
const tempSize = document.getElementById('temp-size');
const tempCount = document.getElementById('temp-count');

// DOM Elements - Progress
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');
const logContainer = document.getElementById('log-container');

// State
let isRunning = false;
let currentTab = 'created';
let createdCount = 0;
let failedCount = 0;

// Random names for generating accounts
const FIRST_NAMES = [
    'James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Charles',
    'Christopher', 'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven', 'Paul', 'Andrew', 'Joshua',
    'Emma', 'Olivia', 'Ava', 'Isabella', 'Sophia', 'Mia', 'Charlotte', 'Amelia', 'Harper', 'Evelyn'
];

const LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
    'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'
];

// Helper functions
function randomChoice(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

function randomString(length) {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

// Add log entry
function addLog(message, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry log-${type}`;
    const time = new Date().toLocaleTimeString();
    entry.textContent = `[${time}] ${message}`;
    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// Update progress
function updateProgress(current, total, text) {
    const percent = total > 0 ? (current / total) * 100 : 0;
    progressBar.style.width = `${percent}%`;
    progressText.textContent = text || `${current}/${total}`;
}

// Update stats
function updateStats() {
    statCreated.textContent = createdCount;
    statFailed.textContent = failedCount;
    tabCountCreated.textContent = createdCount;
    tabCountFailed.textContent = failedCount;
}

// Parse accounts from textarea
function parseAccounts() {
    const text = inputAccounts.value.trim();
    if (!text) return [];

    const lines = text.split('\n').filter(line => line.trim());
    const accounts = [];

    for (const line of lines) {
        const parts = line.trim().split('|');
        if (parts.length >= 3) {
            accounts.push({
                firstName: parts[0].trim(),
                lastName: parts[1].trim(),
                emailPrefix: parts[2].trim()
            });
        }
    }

    return accounts;
}

// Update account count
function updateAccountCount() {
    const createMode = document.querySelector('input[name="create-mode"]:checked').value;
    if (createMode === 'random') {
        accountCount.textContent = randomCount.value;
    } else {
        const accounts = parseAccounts();
        accountCount.textContent = accounts.length;
    }
}

// Generate random accounts
function generateRandomAccounts() {
    const count = parseInt(randomCount.value) || 5;
    const lines = [];

    for (let i = 0; i < count; i++) {
        const firstName = randomChoice(FIRST_NAMES);
        const lastName = randomChoice(LAST_NAMES);
        const emailPrefix = `${firstName.toLowerCase()}${randomString(4)}`;
        lines.push(`${firstName}|${lastName}|${emailPrefix}`);
    }

    inputAccounts.value = lines.join('\n');
    updateAccountCount();
    addLog(`🎲 Đã tạo ${count} accounts ngẫu nhiên`, 'success');
}

// Refresh results from files
async function refreshResults() {
    try {
        const results = await window.api.readResults();
        resultCreated.value = results.created || '';
        resultFailed.value = results.failed || '';

        createdCount = results.created ? results.created.split('\n').filter(l => l.trim()).length : 0;
        failedCount = results.failed ? results.failed.split('\n').filter(l => l.trim()).length : 0;

        updateStats();
    } catch (error) {
        addLog(`Lỗi đọc kết quả: ${error.message}`, 'error');
    }
}

// Load temp size
async function loadTempSize() {
    try {
        const info = await window.api.getTempSize();
        tempSize.textContent = info.sizeMB + ' MB';
        tempCount.textContent = info.folderCount;

        if (info.sizeMB > 100) {
            tempSize.style.color = '#f44336';
        } else if (info.sizeMB > 50) {
            tempSize.style.color = '#ff9800';
        } else {
            tempSize.style.color = '#4caf50';
        }
    } catch (error) {
        console.log('Error loading temp size:', error);
    }
}

// Tab handling
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        tab.classList.add('active');
        currentTab = tab.dataset.tab;
        document.getElementById(`tab-${currentTab}`).classList.add('active');
    });
});

// Event Listeners

// Generate random accounts
btnGenerate.addEventListener('click', generateRandomAccounts);

// Clear input
btnClearInput.addEventListener('click', () => {
    inputAccounts.value = '';
    updateAccountCount();
});

// Update count on input change
inputAccounts.addEventListener('input', updateAccountCount);
randomCount.addEventListener('input', updateAccountCount);
document.querySelectorAll('input[name="create-mode"]').forEach(radio => {
    radio.addEventListener('change', updateAccountCount);
});

// Toggle login sections based on login mode
const manualLoginSection = document.getElementById('manual-login-section');
const btnManualLoginDone = document.getElementById('btn-manual-login-done');

document.querySelectorAll('input[name="login-mode"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        passwordLoginSection.style.display = 'none';
        cookiesLoginSection.style.display = 'none';
        manualLoginSection.style.display = 'none';

        if (e.target.value === 'password') {
            passwordLoginSection.style.display = 'block';
        } else if (e.target.value === 'cookies') {
            cookiesLoginSection.style.display = 'block';
        } else if (e.target.value === 'manual') {
            manualLoginSection.style.display = 'block';
        }
    });
});

// Parse cookies from text (JSON or Netscape format)
function parseCookies(cookiesText) {
    try {
        // Try JSON format first
        let cookies = JSON.parse(cookiesText);
        if (Array.isArray(cookies)) {
            return cookies.map(c => ({
                name: c.name,
                value: c.value,
                domain: c.domain || '.google.com',
                path: c.path || '/',
                httpOnly: c.httpOnly || false,
                secure: c.secure || true
            }));
        }
    } catch (e) {
        // Not JSON, try Netscape format or simple format
    }

    // Try simple format: name=value (one per line)
    const lines = cookiesText.split('\n').filter(l => l.trim());
    const cookies = [];
    for (const line of lines) {
        if (line.includes('=')) {
            const [name, ...valueParts] = line.split('=');
            cookies.push({
                name: name.trim(),
                value: valueParts.join('=').trim(),
                domain: '.google.com',
                path: '/',
                secure: true
            });
        }
    }
    return cookies;
}

// Run button
btnRun.addEventListener('click', async () => {
    const loginMode = document.querySelector('input[name="login-mode"]:checked').value;

    let adminEmail = null;
    let adminPassword = null;
    let otpSecret = null;
    let cookies = null;

    if (loginMode === 'password') {
        const adminAcc = adminAccount.value.trim();
        if (!adminAcc || !adminAcc.includes('|')) {
            addLog('❌ Vui lòng nhập Admin Account (format: email|password hoặc email|password|otp_secret)', 'error');
            return;
        }

        const parts = adminAcc.split('|');
        adminEmail = parts[0].trim();
        adminPassword = parts[1].trim();
        otpSecret = parts.length >= 3 ? parts[2].trim() : null;

        if (otpSecret) {
            addLog(`🔐 Có 2FA OTP secret, sẽ tự động nhập OTP`, 'info');
        }
    } else if (loginMode === 'cookies') {
        // Cookies login
        const cookiesText = adminCookies.value.trim();
        if (!cookiesText) {
            addLog('❌ Vui lòng nhập cookies (JSON format)', 'error');
            return;
        }

        cookies = parseCookies(cookiesText);
        if (cookies.length === 0) {
            addLog('❌ Không thể parse cookies', 'error');
            return;
        }
        addLog(`🍪 Đã parse ${cookies.length} cookies, sẽ login bằng cookies`, 'info');
    } else if (loginMode === 'manual') {
        // Manual login - browser sẽ mở và đợi user đăng nhập
        addLog('✋ Chế độ thủ công - browser sẽ mở và chờ bạn đăng nhập', 'info');
        addLog('👆 Sau khi đăng nhập xong, bấm nút "Đã đăng nhập xong" để tiếp tục', 'info');
    }

    const passwordMode = document.querySelector('input[name="password-mode"]:checked').value;
    const createMode = document.querySelector('input[name="create-mode"]:checked').value;

    let accounts = [];
    if (createMode === 'random') {
        const count = parseInt(randomCount.value) || 5;
        for (let i = 0; i < count; i++) {
            const firstName = randomChoice(FIRST_NAMES);
            const lastName = randomChoice(LAST_NAMES);
            const emailPrefix = `${firstName.toLowerCase()}${randomString(4)}`;
            accounts.push({ firstName, lastName, emailPrefix });
        }
    } else {
        accounts = parseAccounts();
    }

    if (accounts.length === 0) {
        addLog('❌ Không có accounts để tạo', 'error');
        return;
    }

    const config = {
        loginMode,
        adminEmail,
        adminPassword,
        otpSecret,
        cookies,
        accounts,
        passwordMode,
        commonPassword: commonPassword.value.trim() || 'Password123!',
        headless: document.getElementById('save-ram-headless').checked,
        ramFlags: document.getElementById('save-ram-flags').checked
    };

    isRunning = true;
    btnRun.disabled = true;
    btnStop.disabled = false;
    createdCount = 0;
    failedCount = 0;
    updateStats();

    addLog(`🚀 Bắt đầu tạo ${accounts.length} accounts...`, 'info');

    try {
        await window.api.startCreate(config);
    } catch (error) {
        addLog(`Lỗi: ${error.message}`, 'error');
    }
});

// Stop button
btnStop.addEventListener('click', async () => {
    addLog('⏹️ Đang dừng...', 'warning');
    await window.api.stopCreate();
    isRunning = false;
    btnRun.disabled = false;
    btnStop.disabled = true;
});

// Close browser
btnCloseBrowser.addEventListener('click', async () => {
    await window.api.closeBrowser();
    addLog('✅ Đã đóng browser', 'success');
});

// Copy button
btnCopy.addEventListener('click', () => {
    const textarea = currentTab === 'created' ? resultCreated : resultFailed;
    navigator.clipboard.writeText(textarea.value);
    addLog('📋 Đã copy!', 'success');
});

// Save button
btnSave.addEventListener('click', async () => {
    const filename = currentTab === 'created' ? 'created_accounts_export.txt' : 'failed_accounts_export.txt';
    const textarea = currentTab === 'created' ? resultCreated : resultFailed;

    try {
        await window.api.saveFile(filename, textarea.value);
        addLog(`💾 Đã lưu: ${filename}`, 'success');
    } catch (error) {
        addLog(`Lỗi lưu file: ${error.message}`, 'error');
    }
});

// Refresh button
btnRefresh.addEventListener('click', refreshResults);

// Clear log
btnClearLog.addEventListener('click', () => {
    logContainer.innerHTML = '';
    addLog('Log đã được xóa', 'info');
});

// Clear temp
btnClearTemp.addEventListener('click', async () => {
    const confirm = window.confirm('Xóa tất cả Puppeteer temp folders?');
    if (!confirm) return;

    addLog('🧹 Đang xóa Puppeteer temp...', 'info');

    try {
        const result = await window.api.clearTemp();
        addLog(`✅ Đã xóa ${result.deletedCount} folders`, 'success');
        await loadTempSize();
    } catch (error) {
        addLog(`❌ Lỗi xóa temp: ${error.message}`, 'error');
    }
});

// IPC Listeners
window.api.onLog((data) => {
    addLog(data.message, data.type);
});

window.api.onResult((data) => {
    if (data.status === 'CREATED') {
        createdCount++;
        resultCreated.value += `${data.email}|${data.password}\n`;
    } else {
        failedCount++;
        resultFailed.value += `${data.email}|${data.error}\n`;
    }
    updateStats();
});

window.api.onProgress((data) => {
    updateProgress(data.current, data.total, data.text);
});

window.api.onComplete((data) => {
    isRunning = false;
    btnRun.disabled = false;
    btnStop.disabled = true;
    btnManualLoginDone.disabled = true;
    updateProgress(data.created + data.failed, data.created + data.failed, `Hoàn thành!`);
    addLog(`🏁 Hoàn thành! Created: ${data.created}, Failed: ${data.failed}`, 'success');
    refreshResults();
});

// Event: Đang chờ manual login - enable button
window.api.onWaitingManualLogin((data) => {
    if (data.waiting) {
        btnManualLoginDone.disabled = false;
        addLog('👆 Bấm nút "Đã đăng nhập xong" khi hoàn tất', 'warning');
    }
});

// Button: Đã đăng nhập xong (manual login mode)
btnManualLoginDone.addEventListener('click', async () => {
    btnManualLoginDone.disabled = true;
    addLog('✅ Đã xác nhận đăng nhập, đang tiếp tục...', 'info');
    await window.api.manualLoginContinue();
});

// Load browsers
async function loadBrowsers() {
    try {
        const browsers = await window.api.detectBrowsers();
        browserSelect.innerHTML = '';

        const available = browsers.filter(b => b.detected);
        const unavailable = browsers.filter(b => !b.detected);

        if (available.length === 0) {
            browserSelect.innerHTML = '<option value="" disabled>Không tìm thấy browser!</option>';
            return;
        }

        available.forEach((browser, index) => {
            const option = document.createElement('option');
            option.value = browser.id;
            option.textContent = `✓ ${browser.name}`;
            if (index === 0) option.selected = true;
            browserSelect.appendChild(option);
        });

        if (unavailable.length > 0) {
            const sep = document.createElement('option');
            sep.disabled = true;
            sep.textContent = '───────────';
            browserSelect.appendChild(sep);

            unavailable.forEach(browser => {
                const option = document.createElement('option');
                option.value = browser.id;
                option.disabled = true;
                option.textContent = `✗ ${browser.name} (không có)`;
                browserSelect.appendChild(option);
            });
        }

        await window.api.setBrowser(available[0].id);
        addLog(`🌐 Browser: ${available[0].name}`, 'info');
    } catch (error) {
        addLog(`Lỗi load browsers: ${error.message}`, 'error');
    }
}

// Browser change handler
browserSelect.addEventListener('change', async () => {
    const browserId = browserSelect.value;
    if (browserId) {
        await window.api.setBrowser(browserId);
        const browserName = browserSelect.options[browserSelect.selectedIndex].text;
        addLog(`🌐 Đổi browser: ${browserName}`, 'info');
    }
});

// Resume button handler
btnResume.addEventListener('click', async () => {
    addLog('▶️ Đang tiếp tục từ trạng thái hiện tại...', 'info');

    // Build accounts list
    const createMode = document.querySelector('input[name="create-mode"]:checked').value;
    let accounts = [];

    if (createMode === 'random') {
        const count = parseInt(randomCount.value) || 5;
        for (let i = 0; i < count; i++) {
            const firstName = randomChoice(FIRST_NAMES);
            const lastName = randomChoice(LAST_NAMES);
            const emailPrefix = `${firstName.toLowerCase()}${randomString(4)}`;
            accounts.push({ firstName, lastName, emailPrefix });
        }
    } else {
        accounts = parseAccounts();
    }

    if (accounts.length === 0) {
        addLog('❌ Không có accounts để tạo', 'error');
        return;
    }

    const passwordMode = document.querySelector('input[name="password-mode"]:checked').value;
    const config = {
        accounts,
        passwordMode,
        commonPassword: commonPassword.value.trim() || 'Password123!'
    };

    btnResume.disabled = true;
    btnStop.disabled = false;
    isRunning = true;

    try {
        await window.api.resumeCreate(config);
    } catch (error) {
        addLog(`Lỗi: ${error.message}`, 'error');
    }
});

// Event: browser đã sẵn sàng
window.api.onBrowserReady((data) => {
    if (data.ready) {
        btnResume.disabled = false;
        addLog('🔓 Browser sẵn sàng, có thể bấm Tiếp tục', 'info');
    }
});

// Initial load
loadBrowsers();
loadTempSize();
refreshResults();
updateAccountCount();
addLog('Sẵn sàng!', 'success');

