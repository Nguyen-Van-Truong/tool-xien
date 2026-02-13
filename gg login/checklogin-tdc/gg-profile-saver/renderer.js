// ============ DOM ELEMENTS ============
const inputAccounts = document.getElementById('input-accounts');
const btnRun = document.getElementById('btn-run');
const btnStop = document.getElementById('btn-stop');
const btnCloseAll = document.getElementById('btn-close-all');
const btnImport = document.getElementById('btn-import');
const btnLoadFile = document.getElementById('btn-load-file');
const btnSaveAccounts = document.getElementById('btn-save-accounts');
const btnClearInput = document.getElementById('btn-clear-input');
const btnOpenAll = document.getElementById('btn-open-all');
const btnClean = document.getElementById('btn-clean');
const btnBackup = document.getElementById('btn-backup');
const btnRestore = document.getElementById('btn-restore');
const btnRefreshProfiles = document.getElementById('btn-refresh-profiles');
const btnClearLog = document.getElementById('btn-clear-log');
const btnClearTemp = document.getElementById('btn-clear-temp');

const logContainer = document.getElementById('log-container');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');
const accountCount = document.getElementById('account-count');
const profileTbody = document.getElementById('profile-tbody');

const statLogged = document.getElementById('stat-logged');
const statFailed = document.getElementById('stat-failed');
const statVerify = document.getElementById('stat-verify');
const tabCountAll = document.getElementById('tab-count-all');
const tabCountLogged = document.getElementById('tab-count-logged');
const tabCountFailed = document.getElementById('tab-count-failed');

const profilesSize = document.getElementById('profiles-size');
const tempSizeEl = document.getElementById('temp-size');
const browserSelect = document.getElementById('browser-select');

let isRunning = false;
let currentTab = 'all';
let allProfiles = [];

// ============ BROWSERS ============
async function loadBrowsers() {
    try {
        const browsers = await window.api.detectBrowsers();
        browserSelect.innerHTML = '';
        const available = browsers.filter(b => b.detected);
        const unavailable = browsers.filter(b => !b.detected);

        available.forEach((b, i) => {
            const opt = document.createElement('option');
            opt.value = b.id;
            opt.textContent = `✓ ${b.name}`;
            if (i === 0) opt.selected = true;
            browserSelect.appendChild(opt);
        });

        if (unavailable.length > 0) {
            const sep = document.createElement('option');
            sep.disabled = true;
            sep.textContent = '───────────';
            browserSelect.appendChild(sep);
            unavailable.forEach(b => {
                const opt = document.createElement('option');
                opt.value = b.id;
                opt.disabled = true;
                opt.textContent = `✗ ${b.name}`;
                browserSelect.appendChild(opt);
            });
        }

        if (available.length > 0) {
            await window.api.setBrowser(available[0].id);
            addLog(`🌐 Browser: ${available[0].name}`, 'success');
        }
    } catch (e) {
        addLog(`Lỗi detect browsers: ${e.message}`, 'error');
    }
}

browserSelect.addEventListener('change', async () => {
    await window.api.setBrowser(browserSelect.value);
});

// Download Chromium riêng
document.getElementById('btn-download-chrome').addEventListener('click', async () => {
    const btn = document.getElementById('btn-download-chrome');
    btn.disabled = true;
    btn.textContent = '⏳ Đang tải...';
    addLog('⬇️ Đang tải Puppeteer Chromium vào folder riêng (~300MB)...', 'info');
    addLog('   ⏳ Chờ vài phút, không đóng app...', 'warning');

    try {
        const result = await window.api.downloadBrowser();
        if (result.success) {
            addLog('✅ Tải Chromium thành công! Đã lưu trong ./browser/', 'success');
            await loadBrowsers(); // reload browser list
        } else {
            addLog(`❌ Lỗi tải: ${result.error}`, 'error');
        }
    } catch (e) {
        addLog(`❌ Lỗi: ${e.message}`, 'error');
    }

    btn.disabled = false;
    btn.textContent = '⬇️ Tải Chrome';
});

// ============ ACCOUNT INPUT ============
inputAccounts.addEventListener('input', () => {
    const lines = inputAccounts.value.trim().split('\n').filter(l => l.trim() && !l.startsWith('#') && l.includes('|'));
    accountCount.textContent = lines.length;
});

function parseAccounts(text) {
    return text.trim().split('\n')
        .filter(line => line.trim() && !line.startsWith('#'))
        .map(line => {
            const trimmed = line.trim();
            let email, password;
            if (trimmed.includes('|')) [email, password] = trimmed.split('|', 2);
            else if (trimmed.includes('\t')) [email, password] = trimmed.split('\t', 2);
            else { const parts = trimmed.split(/\s+/); email = parts[0]; password = parts[1]; }
            return { email: email?.trim(), password: password?.trim() };
        }).filter(a => a.email && a.password);
}

// ============ LOG ============
function addLog(message, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// ============ PROGRESS ============
function updateProgress(current, total, text) {
    const percent = total > 0 ? (current / total) * 100 : 0;
    progressBar.style.setProperty('--progress', `${percent}%`);
    progressText.textContent = text || `${current}/${total}`;
}

// ============ PROFILES ============
function getStatusBadge(status) {
    const cls = status.replace(/_/g, '-');
    const icons = {
        'logged_in': '✅', 'wrong_password': '❌', 'email_error': '🗑️',
        'needs_verification': '📱', 'error': '⚠️'
    };
    return `<span class="status-badge ${cls}">${icons[status] || '❓'} ${status}</span>`;
}

function formatTime(isoStr) {
    if (!isoStr) return '-';
    const d = new Date(isoStr);
    return `${d.getDate()}/${d.getMonth() + 1} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
}

async function refreshProfiles() {
    try {
        allProfiles = await window.api.getProfiles();
        renderProfiles();
        updateStats();
    } catch (e) {
        addLog(`Lỗi load profiles: ${e.message}`, 'error');
    }
}

function renderProfiles() {
    let filtered = allProfiles;
    if (currentTab === 'logged-in') filtered = allProfiles.filter(p => p.status === 'logged_in');
    else if (currentTab === 'failed') filtered = allProfiles.filter(p => p.status !== 'logged_in');

    if (filtered.length === 0) {
        profileTbody.innerHTML = '<tr class="empty-row"><td colspan="7">Không có profile nào</td></tr>';
        return;
    }

    profileTbody.innerHTML = filtered.map((p, i) => `
        <tr>
            <td>${i + 1}</td>
            <td>${p.profileDir}</td>
            <td style="font-family: Consolas; font-size: 0.8rem">${p.email}</td>
            <td>${getStatusBadge(p.status)}</td>
            <td style="font-size: 0.78rem; color: #999">${p.reason || '-'}</td>
            <td style="font-size: 0.78rem; color: #888">${formatTime(p.lastLogin)}</td>
            <td>
                <button class="action-btn open" onclick="openProfile('${p.email}')">📂 Open</button>
                <button class="action-btn delete" onclick="deleteProfile('${p.email}')">🗑️</button>
            </td>
        </tr>
    `).join('');
}

function updateStats() {
    const logged = allProfiles.filter(p => p.status === 'logged_in').length;
    const failed = allProfiles.filter(p => ['error', 'wrong_password', 'email_error'].includes(p.status)).length;
    const verify = allProfiles.filter(p => p.status === 'needs_verification').length;

    statLogged.textContent = logged;
    statFailed.textContent = failed;
    statVerify.textContent = verify;
    tabCountAll.textContent = allProfiles.length;
    tabCountLogged.textContent = logged;
    tabCountFailed.textContent = allProfiles.length - logged;
}

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        currentTab = tab.dataset.tab;
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        renderProfiles();
    });
});

// ============ ACTIONS ============

// Open single profile
async function openProfile(email) {
    addLog(`📂 Mở profile ${email}...`, 'info');
    const result = await window.api.openProfile(email);
    if (!result.success) addLog(`❌ ${result.reason}`, 'error');
}

// Delete single profile
async function deleteProfile(email) {
    if (!confirm(`Xóa profile ${email}?`)) return;
    const result = await window.api.deleteProfile(email);
    if (result) {
        addLog(`🗑️ Đã xóa ${email}`, 'warning');
        refreshProfiles();
    }
}

// Login All
btnRun.addEventListener('click', async () => {
    const accounts = parseAccounts(inputAccounts.value);
    if (accounts.length === 0) {
        addLog('❌ Không có accounts hợp lệ!', 'error');
        return;
    }

    isRunning = true;
    btnRun.disabled = true;
    btnStop.disabled = false;
    addLog(`🚀 Bắt đầu login ${accounts.length} accounts...`, 'info');
    updateProgress(0, accounts.length, 'Đang khởi động...');

    const headless = document.getElementById('chk-headless')?.checked || false;
    if (headless) addLog('👻 Chế độ Headless', 'info');

    try {
        await window.api.startLogin(accounts, { headless });
    } catch (e) {
        addLog(`❌ Lỗi: ${e.message}`, 'error');
    }
});

btnStop.addEventListener('click', async () => {
    addLog('⏸ Đang dừng...', 'warning');
    await window.api.stopLogin();
    isRunning = false;
    btnRun.disabled = false;
    btnStop.disabled = true;
    updateProgress(0, 0, 'Đã dừng');
});

btnCloseAll.addEventListener('click', async () => {
    addLog('✖ Đang tắt browsers...', 'warning');
    const count = await window.api.closeAllBrowsers();
    addLog(`✅ Đã đóng ${count} browsers`, 'success');
});

// Import
btnImport.addEventListener('click', async () => {
    addLog('📥 Đang import accounts...', 'info');
    const result = await window.api.importAccounts();

    result.sources.forEach(s => {
        if (s.status === 'not_found') addLog(`   ⚠️ ${s.name} - không tìm thấy`, 'warning');
        else if (s.imported > 0) addLog(`   📥 ${s.name} - import ${s.imported} mới (bỏ ${s.skipped} trùng)`, 'success');
        else addLog(`   ✅ ${s.name} - tất cả đã có`, 'info');
    });

    addLog(`✅ Import: ${result.totalImported} mới | Tổng: ${result.totalAccounts} accounts`, 'success');

    // Reload accounts into textarea
    const content = await window.api.readAccounts();
    inputAccounts.value = content;
    const lines = content.trim().split('\n').filter(l => l.trim() && !l.startsWith('#') && l.includes('|'));
    accountCount.textContent = lines.length;
});

// Load file
btnLoadFile.addEventListener('click', () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt';
    input.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
            inputAccounts.value = ev.target.result;
            const lines = inputAccounts.value.trim().split('\n').filter(l => l.trim() && l.includes('|'));
            accountCount.textContent = lines.length;
            addLog(`📂 Loaded ${lines.length} accounts từ ${file.name}`, 'success');
        };
        reader.readAsText(file);
    };
    input.click();
});

// Save accounts
btnSaveAccounts.addEventListener('click', async () => {
    await window.api.saveAccounts(inputAccounts.value);
    addLog('💾 Đã lưu accounts.txt', 'success');
});

// Clear input
btnClearInput.addEventListener('click', () => {
    inputAccounts.value = '';
    accountCount.textContent = '0';
});

// Open All
btnOpenAll.addEventListener('click', async () => {
    addLog('🚀 Mở tất cả profiles...', 'info');
    const result = await window.api.openAllProfiles();
    if (!result.success) addLog(`❌ ${result.reason}`, 'error');
});

// Clean
btnClean.addEventListener('click', async () => {
    if (!confirm('Xóa tất cả profiles lỗi? (Giữ lại profiles đã login OK)')) return;
    addLog('🧹 Đang clean profiles lỗi...', 'info');
    const result = await window.api.cleanProfiles();
    addLog(`✅ Đã xóa ${result.deleted} profiles lỗi, giữ ${result.kept} OK`, 'success');
    refreshProfiles();
});

// Backup
btnBackup.addEventListener('click', async () => {
    addLog('💾 Đang backup...', 'info');
    const result = await window.api.backup();
    addLog(`✅ Backup: ${result.name} (${result.files.join(', ')})`, 'success');
});

// Restore
btnRestore.addEventListener('click', async () => {
    const backups = await window.api.listBackups();
    if (backups.length === 0) {
        addLog('❌ Không có backup nào', 'error');
        return;
    }

    const name = prompt(`Chọn backup để restore:\n\n${backups.map((b, i) => `${i + 1}. ${b}`).join('\n')}\n\nNhập tên backup:`);
    if (!name) return;

    // Allow entering number or full name
    let backupName = name.trim();
    const num = parseInt(backupName);
    if (!isNaN(num) && num >= 1 && num <= backups.length) {
        backupName = backups[num - 1];
    }

    addLog(`♻️ Đang restore ${backupName}...`, 'info');
    const result = await window.api.restore(backupName);
    if (result.success) {
        addLog(`✅ Restore OK: ${result.files.join(', ')}`, 'success');
        refreshProfiles();
        const content = await window.api.readAccounts();
        inputAccounts.value = content;
    } else {
        addLog(`❌ ${result.reason}`, 'error');
    }
});

// Refresh profiles
btnRefreshProfiles.addEventListener('click', refreshProfiles);

// Clear log
btnClearLog.addEventListener('click', () => { logContainer.innerHTML = ''; });

// Clear temp
btnClearTemp.addEventListener('click', async () => {
    addLog('🧹 Xóa Puppeteer temp...', 'info');
    const result = await window.api.clearTemp();
    addLog(`✅ Đã xóa ${result.deletedCount} folders`, 'success');
    loadStorageInfo();
});

// ============ STORAGE INFO ============
async function loadStorageInfo() {
    try {
        const pSize = await window.api.getProfilesSize();
        profilesSize.textContent = pSize.sizeMB + ' MB';
    } catch (e) {}
    try {
        const tSize = await window.api.getTempSize();
        tempSizeEl.textContent = tSize.sizeMB + ' MB';
    } catch (e) {}
}

// ============ IPC EVENTS ============
window.api.onLog((data) => addLog(data.message, data.type || 'info'));

window.api.onResult((data) => {
    refreshProfiles();
});

window.api.onProgress((data) => {
    updateProgress(data.current, data.total, data.text);
});

window.api.onComplete((data) => {
    isRunning = false;
    btnRun.disabled = false;
    btnStop.disabled = true;
    updateProgress(data.total, data.total, `Hoàn thành! (${data.totalTime}s)`);
    addLog(`✅ Hoàn thành! Login: ${data.loggedIn} | Failed: ${data.failed} | Skipped: ${data.skipped} (${data.totalTime}s)`, 'success');
    refreshProfiles();
    loadStorageInfo();
});

window.api.onProfilesUpdated(() => refreshProfiles());

// ============ INIT ============
async function init() {
    addLog('📂 GG Profile Saver v2.0 - Sẵn sàng!', 'success');
    addLog('💡 Thêm accounts → Login All → Profiles tự lưu', 'info');

    await loadBrowsers();
    await refreshProfiles();
    await loadStorageInfo();

    // Khởi động với input trống
    inputAccounts.value = '';
    accountCount.textContent = '0';
}

init();
