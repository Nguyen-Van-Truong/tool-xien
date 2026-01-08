// Side Panel script for ChatGPT Veterans Auto Verify
// This handles all UI interactions and communicates with content.js via messages

// State variables for UI
let dataArray = []; // Veterans data array
let chatgptAccount = null; // Current ChatGPT account
let accountsArray = []; // Array of ALL loaded accounts
let currentAccountIndex = 0; // Current account being processed
let stats = { processed: 0, success: 0, failed: 0, limit: 0 };
let currentDataIndex = 0;
let isRunning = false;
let currentEmail = '';
let manualConsecutiveLimitErrors = 0; // Track consecutive limit/429 errors for manual verify
const MAX_MANUAL_CONSECUTIVE_LIMIT = 5;

// Month name to number mapping for API
const MONTH_TO_NUM_PANEL = {
    "January": "01", "February": "02", "March": "03", "April": "04",
    "May": "05", "June": "06", "July": "07", "August": "08",
    "September": "09", "October": "10", "November": "11", "December": "12"
};

// Update API Direct Log
function updateApiDirectLog(message) {
    const logEl = document.getElementById('api-direct-log');
    if (logEl) {
        const now = new Date();
        const time = now.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const newLine = `[${time}] ${message}`;
        const currentText = logEl.value || '';
        const lines = currentText.split('\n').filter(l => l.trim());
        if (lines.length >= 20) {
            lines.shift();
        }
        lines.push(newLine);
        logEl.value = lines.join('\n');
        logEl.scrollTop = logEl.scrollHeight;
    }
}

// Extract verificationId from URL
function extractVerificationIdFromUrl(url) {
    const match = url.match(/verificationId=([a-f0-9]+)/i);
    return match ? match[1] : null;
}

// Generate new email for Manual Verify
async function generateEmailForManual() {
    try {
        updateApiDirectLog('📧 Generating email...');

        // Get random domains
        const domainsResponse = await fetch('https://tinyhost.shop/api/random-domains/?limit=10');
        if (!domainsResponse.ok) {
            throw new Error('Failed to fetch domains');
        }

        const domainsData = await domainsResponse.json();
        const domains = domainsData.domains || [];
        if (domains.length === 0) {
            throw new Error('No domains available');
        }

        const randomDomain = domains[Math.floor(Math.random() * domains.length)];

        // Generate random username
        const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
        let username = '';
        for (let i = 0; i < 16; i++) {
            username += chars.charAt(Math.floor(Math.random() * chars.length));
        }

        const email = `${username}@${randomDomain}`;
        updateApiDirectLog(`✅ Email: ${email}`);
        return email;

    } catch (error) {
        updateApiDirectLog(`❌ Gen email error: ${error.message}`);
        return null;
    }
}

// Check email for verification link
async function checkEmailForLink(email) {
    try {
        const [username, domain] = email.split('@');
        if (!username || !domain) {
            throw new Error('Invalid email format');
        }

        updateApiDirectLog(`📬 Checking inbox: ${email}`);

        const response = await fetch(`https://tinyhost.shop/api/email/${domain}/${username}/?page=1&limit=20`);
        if (!response.ok) {
            throw new Error('Failed to fetch emails');
        }

        const data = await response.json();
        const emails = data.emails || [];

        if (emails.length === 0) {
            updateApiDirectLog('📭 No emails yet. Try again in a few seconds...');
            return null;
        }

        // Sort by date (newest first)
        emails.sort((a, b) => new Date(b.date) - new Date(a.date));

        // Find SheerID verification link
        for (const mail of emails) {
            if (mail.html_body) {
                const match = mail.html_body.match(/https:\/\/services\.sheerid\.com\/verify\/[^"'\s<>]+/i);
                if (match) {
                    const link = match[0].replace(/&amp;/g, '&');
                    updateApiDirectLog('✅ Found verification link!');
                    return link;
                }
            }
            if (mail.body) {
                const match = mail.body.match(/https:\/\/services\.sheerid\.com\/verify\/[^"'\s<>()]+/i);
                if (match) {
                    const link = match[0].replace(/&amp;/g, '&');
                    updateApiDirectLog('✅ Found verification link!');
                    return link;
                }
            }
        }

        updateApiDirectLog('📭 No verification link found in emails yet...');
        return null;

    } catch (error) {
        updateApiDirectLog(`❌ Check email error: ${error.message}`);
        return null;
    }
}

// Update Manual Veteran Display
function updateManualVeteranDisplay() {
    const display = document.getElementById('manual-veteran-display');
    if (!display) return;

    chrome.storage.local.get(['veterans-data-array', 'veterans-current-index'], (result) => {
        const data = result['veterans-data-array'] || [];
        const idx = result['veterans-current-index'] || 0;

        if (data.length === 0) {
            display.textContent = 'Chưa load data - load file VETERANS trước';
            display.style.color = '#f87171';
            return;
        }

        if (idx >= data.length) {
            display.textContent = 'Đã hết data - load thêm hoặc reset';
            display.style.color = '#fbbf24';
            return;
        }

        const vet = data[idx];
        display.innerHTML = `
            <div>${vet.first} ${vet.last} (${idx + 1}/${data.length})</div>
            <div style="color: #a1a1aa; font-size: 9px;">${vet.branch} | ${vet.month} ${vet.day}, ${vet.year}</div>
        `;
        display.style.color = '#34d399';
    });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setupPanelHandlers();
    loadPanelData();
    updateUIPanel();

    // Listen for storage changes to update UI
    chrome.storage.onChanged.addListener((changes, areaName) => {
        if (areaName === 'local') {
            if (changes['veterans-stats']) {
                stats = changes['veterans-stats'].newValue || stats;
                updateUIPanel();
            }
            if (changes['veterans-data-array']) {
                dataArray = changes['veterans-data-array'].newValue || [];
                updateUIPanel();
                updateManualVeteranDisplay();
            }
            if (changes['veterans-is-running']) {
                isRunning = changes['veterans-is-running'].newValue || false;
                updateButtonStates();
                // When tool stops, ensure we show the last status message
                if (!isRunning) {
                    chrome.storage.local.get(['veterans-status'], (result) => {
                        if (result['veterans-status'] && result['veterans-status'].message) {
                            updateUIPanelStatus(result['veterans-status'].message, result['veterans-status'].type || 'info');
                        }
                    });
                }
            }
            if (changes['veterans-current-index']) {
                currentDataIndex = changes['veterans-current-index'].newValue || 0;
                updateUIPanel();
                updateManualVeteranDisplay();
            }
            // When data-list changes, update button states
            if (changes['veterans-data-list']) {
                const startBtn = document.getElementById('veterans-start-btn');
                if (startBtn && !isRunning) {
                    const newDataList = changes['veterans-data-list'].newValue;
                    if (newDataList) {
                        const dataLines = newDataList.split('\n').filter((line) => line.trim());
                        const validData = dataLines.filter((line) => {
                            const parts = line.trim().split('|');
                            return parts.length === 6;
                        });
                        startBtn.disabled = validData.length === 0;
                    } else {
                        startBtn.disabled = true;
                    }
                }
            }
            // When email changes, update email display
            if (changes['veterans-saved-email']) {
                currentEmail = changes['veterans-saved-email'].newValue || '';
                const emailInput = document.getElementById('veterans-email-input');
                if (emailInput) {
                    emailInput.value = currentEmail;
                }
            }
            // When status changes, update status display
            if (changes['veterans-status']) {
                const statusData = changes['veterans-status'].newValue;
                if (statusData && statusData.message) {
                    updateUIPanelStatus(statusData.message, statusData.type || 'info');
                }
            }
            // When VPN log changes, update VPN log display
            if (changes['veterans-vpn-log']) {
                const vpnLogEl = document.getElementById('veterans-vpn-log');
                if (vpnLogEl) {
                    vpnLogEl.value = changes['veterans-vpn-log'].newValue || '';
                }
            }
        }
    });

    // Listen for messages from content script
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.action === 'updateStatus') {
            updateUIPanelStatus(message.status, message.type);
        } else if (message.action === 'updateStats') {
            if (message.stats) {
                stats = message.stats;
                updateUIPanel();
            }
        } else if (message.action === 'updatePanel') {
            updateUIPanel();
        }
        return true;
    });

    // Periodically sync state from storage
    setInterval(() => {
        syncStateFromStorage();
    }, 1000);
});

function syncStateFromStorage() {
    chrome.storage.local.get([
        'veterans-data-array',
        'veterans-stats',
        'veterans-current-index',
        'veterans-is-running',
        'veterans-saved-email',
        'veterans-status',
        'chatgpt-accounts-array',
        'chatgpt-current-account-index',
        'chatgpt-account'
    ], (result) => {
        if (result['veterans-data-array']) {
            dataArray = result['veterans-data-array'];
        }
        if (result['veterans-stats']) {
            stats = result['veterans-stats'];
        }
        if (result['veterans-current-index'] !== undefined) {
            currentDataIndex = result['veterans-current-index'];
        }
        if (result['veterans-is-running'] !== undefined) {
            isRunning = result['veterans-is-running'];
        }
        if (result['veterans-saved-email']) {
            currentEmail = result['veterans-saved-email'];
            const emailInput = document.getElementById('veterans-email-input');
            if (emailInput) {
                emailInput.value = currentEmail;
            }
        }
        if (result['veterans-status'] && result['veterans-status'].message) {
            updateUIPanelStatus(result['veterans-status'].message, result['veterans-status'].type || 'info');
        }

        // Sync account array and index
        if (result['chatgpt-accounts-array']) {
            accountsArray = result['chatgpt-accounts-array'];
        }
        if (result['chatgpt-current-account-index'] !== undefined) {
            currentAccountIndex = result['chatgpt-current-account-index'];
        }
        if (result['chatgpt-account']) {
            chatgptAccount = result['chatgpt-account'];
        }

        // Update account display with current position
        const accountCurrent = document.getElementById('chatgpt-account-current');
        if (accountCurrent && accountsArray.length > 0 && currentAccountIndex < accountsArray.length) {
            const currentAcc = accountsArray[currentAccountIndex];
            accountCurrent.value = `${currentAcc.email} (${currentAccountIndex + 1}/${accountsArray.length})`;
        }

        updateUIPanel();
        updateButtonStates();
    });
}

function updateRangeInfo() {
    const rangeFromInput = document.getElementById('veterans-range-from');
    const rangeToInput = document.getElementById('veterans-range-to');
    const rangeInfo = document.getElementById('veterans-range-info');
    const rangeText = document.getElementById('veterans-range-text');

    if (!rangeFromInput || !rangeToInput || !rangeInfo || !rangeText) return;

    // Get total data count from storage
    chrome.storage.local.get(['veterans-data-list'], (result) => {
        if (!result['veterans-data-list']) {
            rangeInfo.style.display = 'none';
            return;
        }

        const dataLines = result['veterans-data-list'].split('\n').filter((line) => line.trim());
        const validData = dataLines.filter((line) => {
            const parts = line.trim().split('|');
            return parts.length === 6;
        });

        const totalData = validData.length;
        if (totalData === 0) {
            rangeInfo.style.display = 'none';
            return;
        }

        // Update max values for inputs
        rangeFromInput.max = totalData;
        rangeToInput.max = totalData;

        // Get range values (empty string if not filled)
        const fromValueStr = rangeFromInput.value.trim();
        const toValueStr = rangeToInput.value.trim();

        // If both are empty, hide range info (process all data)
        if (!fromValueStr && !toValueStr) {
            rangeInfo.style.display = 'none';
            // Clear stored range values
            chrome.storage.local.remove(['veterans-range-from', 'veterans-range-to']);
            return;
        }

        // If either is filled, validate and show range info
        let fromValue = fromValueStr ? parseInt(fromValueStr) : 1;
        let toValue = toValueStr ? parseInt(toValueStr) : totalData;

        // Validate and adjust values
        if (isNaN(fromValue) || fromValue < 1) fromValue = 1;
        if (fromValue > totalData) fromValue = totalData;
        if (isNaN(toValue) || toValue < 1) toValue = totalData;
        if (toValue > totalData) toValue = totalData;
        if (fromValue > toValue) {
            // Swap if from > to
            const temp = fromValue;
            fromValue = toValue;
            toValue = temp;
        }

        // Only update input values if they were filled (don't auto-fill empty inputs)
        if (fromValueStr) rangeFromInput.value = fromValue;
        if (toValueStr) rangeToInput.value = toValue;

        // Calculate count
        const count = toValue - fromValue + 1;

        // Update display
        rangeText.textContent = `Will process: ${count} data (Range: ${fromValue}-${toValue} of ${totalData})`;
        rangeInfo.style.display = 'block';

        // Save range values to storage
        chrome.storage.local.set({
            'veterans-range-from': fromValueStr ? fromValue : '',
            'veterans-range-to': toValueStr ? toValue : ''
        });
    });
}

function updateUIPanel() {
    const totalEl = document.getElementById('veterans-panel-total');
    const processedEl = document.getElementById('veterans-panel-processed');
    const successEl = document.getElementById('veterans-panel-success');
    const failedEl = document.getElementById('veterans-panel-failed');
    const currentEl = document.getElementById('veterans-panel-current');

    // New detailed elements
    const positionEl = document.getElementById('veterans-current-position');
    const nameEl = document.getElementById('veterans-current-name');
    const branchEl = document.getElementById('veterans-current-branch');
    const birthdateEl = document.getElementById('veterans-current-birthdate');

    if (totalEl) totalEl.textContent = dataArray.length || 0;
    if (processedEl) processedEl.textContent = stats.processed || 0;
    if (successEl) successEl.textContent = stats.success || 0;
    if (failedEl) failedEl.textContent = stats.failed || 0;

    // Limit counter
    const limitEl = document.getElementById('veterans-panel-limit');
    if (limitEl) limitEl.textContent = stats.limit || 0;

    // Update current veteran details
    if (currentDataIndex < dataArray.length && dataArray.length > 0) {
        const veteran = dataArray[currentDataIndex];
        const totalOriginal = (stats.processed || 0) + dataArray.length;
        const currentPosition = (stats.processed || 0) + 1;

        if (positionEl) positionEl.textContent = `${currentPosition} / ${totalOriginal}`;
        if (nameEl) nameEl.textContent = `${veteran.first} ${veteran.last}`;
        if (branchEl) branchEl.textContent = veteran.branch || '-';
        if (birthdateEl) birthdateEl.textContent = `${veteran.month}/${veteran.day}/${veteran.year}`;
        if (currentEl) currentEl.value = `${veteran.first} ${veteran.last}`;
    } else {
        if (positionEl) positionEl.textContent = '-';
        if (nameEl) nameEl.textContent = '-';
        if (branchEl) branchEl.textContent = '-';
        if (birthdateEl) birthdateEl.textContent = '-';
        if (currentEl) currentEl.value = '-';
    }

    // Update range info
    updateRangeInfo();
}

function updateUIPanelStatus(message, type = 'info') {
    const statusEl = document.getElementById('veterans-panel-status');
    if (statusEl) {
        // Get timestamp
        const now = new Date();
        const time = now.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

        // Append new log entry
        const newLine = `[${time}] ${message}`;
        const currentText = statusEl.value || '';

        // Keep max 50 lines to prevent memory issues
        const lines = currentText.split('\n').filter(l => l.trim());
        if (lines.length >= 50) {
            lines.shift(); // Remove oldest line
        }
        lines.push(newLine);

        statusEl.value = lines.join('\n');

        // Auto-scroll to bottom
        statusEl.scrollTop = statusEl.scrollHeight;
    }
}

function updateButtonStates() {
    const startBtn = document.getElementById('veterans-start-btn');
    const stopBtn = document.getElementById('veterans-stop-btn');
    const skipBtn = document.getElementById('veterans-skip-btn');

    if (startBtn) {
        if (isRunning) {
            startBtn.disabled = true;
        } else {
            // Check both ChatGPT account and veterans data
            chrome.storage.local.get(['chatgpt-account', 'veterans-data-list'], (result) => {
                const hasAccount = !!result['chatgpt-account'];
                let hasData = false;
                if (result['veterans-data-list']) {
                    const dataLines = result['veterans-data-list'].split('\n').filter((line) => line.trim());
                    const validData = dataLines.filter((line) => {
                        const parts = line.trim().split('|');
                        return parts.length === 6;
                    });
                    hasData = validData.length > 0;
                }
                // Also check dataArray
                const hasDataFromArray = dataArray && dataArray.length > 0;
                startBtn.disabled = !(hasAccount && (hasData || hasDataFromArray));
            });
        }
    }

    if (stopBtn) {
        stopBtn.disabled = !isRunning;
    }

    if (skipBtn) {
        skipBtn.disabled = isRunning;
        skipBtn.style.display = 'block';
    }
}

function updateUIOnStop() {
    updateButtonStates();
}

// Setup panel event handlers
function setupPanelHandlers() {
    // Clear Log button
    const clearLogBtn = document.getElementById('veterans-clear-log-btn');
    if (clearLogBtn) {
        clearLogBtn.addEventListener('click', () => {
            const statusEl = document.getElementById('veterans-panel-status');
            if (statusEl) {
                statusEl.value = 'Log cleared';
            }
        });
    }

    // Load ChatGPT Account file button (6 fields)
    const chatgptLoadBtn = document.getElementById('chatgpt-account-load-btn');
    const chatgptFileInput = document.getElementById('chatgpt-account-file-input');

    if (chatgptLoadBtn && chatgptFileInput) {
        chatgptLoadBtn.addEventListener('click', () => {
            chatgptFileInput.click();
        });

        chatgptFileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (event) => {
                const content = event.target.result;
                const lines = content.split('\n').filter((line) => line.trim());

                // Parse ALL valid accounts (supports 4 or 6 fields)
                // Format 6 fields: email-chatgpt|pass-chatgpt|email-login|pass-email|refresh_token|client_id
                // Format 4 fields: email|password|refresh_token|client_id (email-login = email, pass-email = password)
                const parsedAccounts = [];
                for (const line of lines) {
                    const parts = line.trim().split('|');

                    if (parts.length === 6) {
                        // 6-field format: full format with separate email login
                        parsedAccounts.push({
                            email: parts[0].trim(),
                            password: parts[1].trim(),
                            emailLogin: parts[2].trim(),
                            passEmail: parts[3].trim(),
                            refreshToken: parts[4].trim(),
                            clientId: parts[5].trim(),
                            original: line.trim()
                        });
                    } else if (parts.length === 4) {
                        // 4-field format: email login = chatgpt email
                        parsedAccounts.push({
                            email: parts[0].trim(),
                            password: parts[1].trim(),
                            emailLogin: parts[0].trim(),  // Same as email
                            passEmail: parts[1].trim(),   // Same as password
                            refreshToken: parts[2].trim(),
                            clientId: parts[3].trim(),
                            original: line.trim()
                        });
                    }
                }

                if (parsedAccounts.length === 0) {
                    updateUIPanelStatus('❌ Invalid format! Expected: email|pass|token|clientId (4 fields) or email|pass|emailLogin|passEmail|token|clientId (6 fields)', 'error');
                    chatgptFileInput.value = '';
                    return;
                }

                // Store ALL accounts and set first as current
                accountsArray = parsedAccounts;
                currentAccountIndex = 0;
                chatgptAccount = parsedAccounts[0];

                // Clear old veteran processing state when loading new accounts
                chrome.storage.local.remove([
                    'veterans-data-array',
                    'veterans-current-index',
                    'veterans-is-running',
                    'veterans-stats'
                ]);

                // Reset local state
                dataArray = [];
                currentDataIndex = 0;
                stats = { processed: 0, success: 0, failed: 0, limit: 0 };
                isRunning = false;

                // Save to storage
                chrome.storage.local.set({
                    'chatgpt-account': chatgptAccount,
                    'chatgpt-accounts-array': accountsArray,
                    'chatgpt-current-account-index': 0,
                    'chatgpt-account-list': content
                });

                // Show account info
                const accountInfo = document.getElementById('chatgpt-account-info');
                const accountCount = document.getElementById('chatgpt-account-count');
                if (accountInfo && accountCount) {
                    accountCount.textContent = parsedAccounts.length.toString();
                    accountInfo.classList.add('show');
                }

                // Update current account display
                const accountCurrent = document.getElementById('chatgpt-account-current');
                if (accountCurrent) {
                    accountCurrent.value = `${chatgptAccount.email} (1/${parsedAccounts.length})`;
                }

                console.log(`✅ Loaded ${parsedAccounts.length} account(s)`);
                updateUIPanelStatus(`✅ Loaded ${parsedAccounts.length} ChatGPT account(s)`, 'success');
                updateButtonStates();
                chatgptFileInput.value = '';
            };
            reader.readAsText(file);
        });
    }

    // Load Veterans Data file button (6 fields)
    const veteransLoadBtn = document.getElementById('veterans-data-load-btn');
    const veteransFileInput = document.getElementById('veterans-data-file-input');

    if (veteransLoadBtn && veteransFileInput) {
        veteransLoadBtn.addEventListener('click', () => {
            veteransFileInput.click();
        });

        veteransFileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (event) => {
                const content = event.target.result;

                // Parse and count valid data lines
                const dataLines = content.split('\n').filter((line) => line.trim());
                const validData = dataLines.filter((line) => {
                    const parts = line.trim().split('|');
                    return parts.length === 6;
                });

                if (validData.length === 0) {
                    updateUIPanelStatus('❌ Invalid veterans data format. Expected: first|last|branch|month|day|year', 'error');
                    veteransFileInput.value = '';
                    return;
                }

                // Clear old veteran processing state when loading new veterans data
                chrome.storage.local.remove([
                    'veterans-data-array',
                    'veterans-current-index',
                    'veterans-is-running',
                    'veterans-stats'
                ]);

                // Reset local state
                dataArray = [];
                currentDataIndex = 0;
                stats = { processed: 0, success: 0, failed: 0 };
                isRunning = false;

                // Save new veterans data to BOTH active and backup storage
                chrome.storage.local.set({
                    'veterans-data-list': content,
                    'veterans-data-list-file': content,  // Backup for restoring when switching modes
                    'random-veteran-mode': false  // Clear random mode when file is loaded
                });

                // Show data count
                const dataInfo = document.getElementById('veterans-data-info');
                const dataCount = document.getElementById('veterans-data-count');
                if (dataInfo && dataCount) {
                    dataCount.textContent = validData.length;
                    dataInfo.classList.add('show');
                }

                // Update data source indicator
                updateDataSourceIndicator();

                // Update range info after loading data
                updateRangeInfo();

                updateUIPanelStatus(`✅ Loaded ${validData.length} veterans data entries`, 'success');
                updateButtonStates();
                veteransFileInput.value = '';
            };
            reader.readAsText(file);
        });
    }

    // Range inputs event listeners
    const rangeFromInput = document.getElementById('veterans-range-from');
    const rangeToInput = document.getElementById('veterans-range-to');

    if (rangeFromInput) {
        rangeFromInput.addEventListener('input', () => {
            updateRangeInfo();
        });
        rangeFromInput.addEventListener('change', () => {
            updateRangeInfo();
        });
    }

    if (rangeToInput) {
        rangeToInput.addEventListener('input', () => {
            updateRangeInfo();
        });
        rangeToInput.addEventListener('change', () => {
            updateRangeInfo();
        });
    }

    // Start button
    const startBtn = document.getElementById('veterans-start-btn');
    if (startBtn) {
        startBtn.addEventListener('click', async () => {
            // Get account, data and random mode from storage
            chrome.storage.local.get(['chatgpt-account', 'veterans-data-list', 'random-veteran-mode'], async (result) => {
                // Check ChatGPT account
                if (!result['chatgpt-account']) {
                    updateUIPanelStatus('❌ Please load ChatGPT account first', 'error');
                    return;
                }

                const randomModeEnabled = result['random-veteran-mode'] || false;
                let dataList = result['veterans-data-list'];

                // If Random Mode is enabled, generate random veterans data
                if (randomModeEnabled) {
                    updateUIPanelStatus('🎲 Random Mode: Generating random veteran data...', 'info');

                    // Extended first names list (100+ common American names)
                    const FIRST_NAMES = [
                        'JAMES', 'JOHN', 'ROBERT', 'MICHAEL', 'WILLIAM', 'DAVID', 'RICHARD', 'JOSEPH', 'THOMAS', 'CHARLES',
                        'CHRISTOPHER', 'DANIEL', 'MATTHEW', 'ANTHONY', 'MARK', 'DONALD', 'STEVEN', 'PAUL', 'ANDREW', 'JOSHUA',
                        'KENNETH', 'KEVIN', 'BRIAN', 'GEORGE', 'TIMOTHY', 'RONALD', 'EDWARD', 'JASON', 'JEFFREY', 'RYAN',
                        'JACOB', 'GARY', 'NICHOLAS', 'ERIC', 'JONATHAN', 'STEPHEN', 'LARRY', 'JUSTIN', 'SCOTT', 'BRANDON',
                        'BENJAMIN', 'SAMUEL', 'RAYMOND', 'GREGORY', 'FRANK', 'ALEXANDER', 'PATRICK', 'JACK', 'DENNIS', 'JERRY',
                        'TYLER', 'AARON', 'JOSE', 'ADAM', 'NATHAN', 'HENRY', 'DOUGLAS', 'ZACHARY', 'PETER', 'KYLE',
                        'WALTER', 'ETHAN', 'JEREMY', 'HAROLD', 'KEITH', 'CHRISTIAN', 'ROGER', 'NOAH', 'GERALD', 'CARL',
                        'TERRY', 'SEAN', 'AUSTIN', 'ARTHUR', 'LAWRENCE', 'JESSE', 'DYLAN', 'BRYAN', 'JOE', 'JORDAN',
                        'BILLY', 'BRUCE', 'ALBERT', 'WILLIE', 'GABRIEL', 'LOGAN', 'ALAN', 'JUAN', 'WAYNE', 'ELIJAH',
                        'RANDY', 'ROY', 'VINCENT', 'RALPH', 'EUGENE', 'RUSSELL', 'BOBBY', 'MASON', 'PHILIP', 'HARRY',
                        'JOHNNY', 'TRAVIS', 'CARLOS', 'ANTONIO', 'LUIS', 'MARTIN', 'CRAIG', 'CLARENCE', 'DALE', 'CURTIS',
                        'DANNY', 'GLENN', 'VICTOR', 'ERNEST', 'DEREK', 'TODD', 'SHAWN', 'MARCUS', 'LEONARD', 'TROY'
                    ];

                    // Extended last names list (200+ common American surnames)
                    const LAST_NAMES = [
                        'SMITH', 'JOHNSON', 'WILLIAMS', 'BROWN', 'JONES', 'GARCIA', 'MILLER', 'DAVIS', 'RODRIGUEZ', 'MARTINEZ',
                        'HERNANDEZ', 'LOPEZ', 'GONZALEZ', 'WILSON', 'ANDERSON', 'THOMAS', 'TAYLOR', 'MOORE', 'JACKSON', 'MARTIN',
                        'LEE', 'PEREZ', 'THOMPSON', 'WHITE', 'HARRIS', 'SANCHEZ', 'CLARK', 'RAMIREZ', 'LEWIS', 'ROBINSON',
                        'WALKER', 'YOUNG', 'ALLEN', 'KING', 'WRIGHT', 'SCOTT', 'TORRES', 'NGUYEN', 'HILL', 'FLORES',
                        'GREEN', 'ADAMS', 'NELSON', 'BAKER', 'HALL', 'RIVERA', 'CAMPBELL', 'MITCHELL', 'CARTER', 'ROBERTS',
                        'GOMEZ', 'PHILLIPS', 'EVANS', 'TURNER', 'DIAZ', 'PARKER', 'CRUZ', 'EDWARDS', 'COLLINS', 'REYES',
                        'STEWART', 'MORRIS', 'MORALES', 'MURPHY', 'COOK', 'ROGERS', 'GUTIERREZ', 'ORTIZ', 'MORGAN', 'COOPER',
                        'PETERSON', 'BAILEY', 'REED', 'KELLY', 'HOWARD', 'RAMOS', 'KIM', 'COX', 'WARD', 'RICHARDSON',
                        'WATSON', 'BROOKS', 'CHAVEZ', 'WOOD', 'JAMES', 'BENNETT', 'GRAY', 'MENDOZA', 'RUIZ', 'HUGHES',
                        'PRICE', 'ALVAREZ', 'CASTILLO', 'SANDERS', 'PATEL', 'MYERS', 'LONG', 'ROSS', 'FOSTER', 'JIMENEZ',
                        'POWELL', 'JENKINS', 'PERRY', 'RUSSELL', 'SULLIVAN', 'BELL', 'COLEMAN', 'BUTLER', 'HENDERSON', 'BARNES',
                        'GONZALES', 'FISHER', 'VASQUEZ', 'SIMMONS', 'GRAHAM', 'MCDONALD', 'PATTERSON', 'JORDAN', 'REYNOLDS', 'HAMILTON',
                        'GRAHAM', 'WALLACE', 'MASON', 'WEST', 'COLE', 'OWENS', 'JORDAN', 'ELLIS', 'MILLS', 'STONE',
                        'HUNT', 'BLACK', 'PALMER', 'BERRY', 'GORDON', 'DEAN', 'PAYNE', 'FOX', 'BISHOP', 'WEAVER',
                        'SPENCER', 'DOUGLAS', 'WARREN', 'GRAHAM', 'RICE', 'HART', 'MCCOY', 'LYNCH', 'BURNS', 'SIMPSON',
                        'OLSON', 'FREEMAN', 'GRANT', 'SNYDER', 'WEBB', 'TUCKER', 'HAYES', 'PORTER', 'HUNTER', 'HICKS',
                        'CRAWFORD', 'HENRY', 'BOYD', 'MASON', 'MORALES', 'KENNEDY', 'WARREN', 'DIXON', 'RAMOS', 'REYES',
                        'BURNS', 'GORDON', 'SHAW', 'HOLMES', 'RICE', 'ROBERTSON', 'HUNT', 'BLACK', 'DANIELS', 'PALMER',
                        'MILLS', 'NICHOLS', 'GRANT', 'KNIGHT', 'FERGUSON', 'ROSE', 'STONE', 'HAWKINS', 'DUNN', 'PERKINS',
                        'HUDSON', 'SPENCER', 'GARDNER', 'STEPHENS', 'PAYNE', 'PIERCE', 'BERRY', 'MATTHEWS', 'ARNOLD', 'WAGNER'
                    ];

                    // Weighted branch distribution (realistic military proportions)
                    const BRANCHES_WEIGHTED = [
                        'Army', 'Army', 'Army', 'Army', 'Army', 'Army', 'Army',  // 35%
                        'Air Force', 'Air Force', 'Air Force', 'Air Force', 'Air Force',  // 25%
                        'Navy', 'Navy', 'Navy', 'Navy',  // 20%
                        'Marine Corps', 'Marine Corps', 'Marine Corps',  // 15%
                        'Coast Guard'  // 5%
                    ];

                    const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

                    function randomChoice(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
                    function randomInt(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }

                    // Generate 100 random veterans with realistic data
                    const randomDataLines = [];
                    for (let i = 0; i < 100; i++) {
                        const first = randomChoice(FIRST_NAMES);
                        const last = randomChoice(LAST_NAMES);
                        const branch = randomChoice(BRANCHES_WEIGHTED);
                        const month = randomChoice(MONTHS);
                        const day = randomInt(1, 28).toString();
                        const year = randomInt(1955, 1992).toString();  // Age 32-70 (realistic veteran age)
                        randomDataLines.push(`${first}|${last}|${branch}|${month}|${day}|${year}`);
                    }
                    dataList = randomDataLines.join('\n');

                    // Save random data to storage (keeps file backup intact)
                    chrome.storage.local.set({ 'veterans-data-list': dataList }, () => {
                        // Update data source indicator
                        if (window.updateDataSourceIndicator) {
                            window.updateDataSourceIndicator();
                        }

                        // Update veterans count display
                        const dataCount = document.getElementById('veterans-data-count');
                        if (dataCount) {
                            dataCount.textContent = '100';
                        }
                    });
                    updateUIPanelStatus('🎲 Generated 100 random veterans (120+ first names, 200+ last names)', 'success');
                } else {
                    // Normal mode: require veterans data
                    if (!dataList || !dataList.trim()) {
                        updateUIPanelStatus('❌ Please load veterans data first', 'error');
                        return;
                    }
                }

                // Parse veterans data
                const dataLines = dataList.split('\n').filter((line) => line.trim());
                const parsedDataArray = dataLines
                    .map((line) => {
                        const parts = line.trim().split('|');
                        if (parts.length === 6) {
                            return {
                                first: parts[0].trim(),
                                last: parts[1].trim(),
                                branch: parts[2].trim(),
                                month: parts[3].trim(),
                                day: parts[4].trim(),
                                year: parts[5].trim(),
                                original: line.trim()
                            };
                        }
                        return null;
                    })
                    .filter((item) => item !== null);

                if (parsedDataArray.length === 0) {
                    updateUIPanelStatus('❌ No valid veterans data found', 'error');
                    return;
                }

                // Get ChatGPT account
                const account = result['chatgpt-account'];

                // Get range values and apply range filter (if specified)
                const rangeFromInput = document.getElementById('veterans-range-from');
                const rangeToInput = document.getElementById('veterans-range-to');
                let workingDataArray = parsedDataArray;

                // Check if range is specified (either FROM or TO is filled)
                if (rangeFromInput && rangeToInput) {
                    const fromValueStr = rangeFromInput.value.trim();
                    const toValueStr = rangeToInput.value.trim();

                    // Only apply range if at least one field is filled
                    if (fromValueStr || toValueStr) {
                        let fromValue = fromValueStr ? parseInt(fromValueStr) : 1;
                        let toValue = toValueStr ? parseInt(toValueStr) : parsedDataArray.length;

                        // Validate and adjust values
                        if (isNaN(fromValue) || fromValue < 1) fromValue = 1;
                        if (fromValue > parsedDataArray.length) fromValue = parsedDataArray.length;
                        if (isNaN(toValue) || toValue < 1) toValue = parsedDataArray.length;
                        if (toValue > parsedDataArray.length) toValue = parsedDataArray.length;
                        if (fromValue > toValue) {
                            const temp = fromValue;
                            fromValue = toValue;
                            toValue = temp;
                        }

                        // Apply range filter (convert to 0-based index)
                        workingDataArray = parsedDataArray.slice(fromValue - 1, toValue);

                        console.log(`📊 Using range ${fromValue}-${toValue} of ${parsedDataArray.length} total data`);
                        console.log(`📊 Processing ${workingDataArray.length} data entries`);
                    } else {
                        // No range specified, process all data
                        console.log(`📊 No range specified, processing all ${parsedDataArray.length} data entries`);
                    }
                }

                if (workingDataArray.length === 0) {
                    updateUIPanelStatus('❌ No data in selected range', 'error');
                    return;
                }

                // Update UI
                updateUIPanel();
                // Nút START và STOP luôn hiển thị, chỉ disable/enable
                startBtn.disabled = true;
                const stopBtn = document.getElementById('veterans-stop-btn');
                const skipBtn = document.getElementById('veterans-skip-btn');
                if (stopBtn) stopBtn.disabled = false;
                if (skipBtn) {
                    skipBtn.style.display = 'block';
                    skipBtn.disabled = true;
                }

                // Start verification - save data to storage and send message
                updateUIPanelStatus('🔒 Clearing SheerID before start...', 'info');

                // Clear SheerID data before starting
                chrome.runtime.sendMessage({ action: 'clearSheerID' }, (response) => {
                    if (response && response.success) {
                        console.log('✅ SheerID cleared before start');
                    }
                });

                // Small delay to ensure clear completes
                await new Promise(resolve => setTimeout(resolve, 500));

                updateUIPanelStatus('🚀 Starting verification...', 'info');

                // Save data to storage first
                const dataListString = parsedDataArray
                    .map((data) => data.original)
                    .join('\n');

                chrome.storage.local.set({
                    'chatgpt-account': account,
                    'veterans-data-array': workingDataArray,
                    'veterans-data-list': dataListString,
                    'veterans-current-index': 0,
                    'veterans-is-running': true,
                    'veterans-stats': { processed: 0, success: 0, failed: 0, limit: 0 },
                    'veterans-consecutive-limit-errors': 0, // Reset limit errors when starting
                    'veterans-active-tab-id': null // Will be set below with actual tab ID
                }, () => {
                    console.log('✅ Data saved to storage');

                    // Send message to content script to start verification with both account and data
                    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                        if (!tabs[0]) {
                            updateUIPanelStatus('❌ No active tab found', 'error');
                            startBtn.disabled = false;
                            if (stopBtn) stopBtn.disabled = true;
                            return;
                        }

                        const currentUrl = tabs[0].url || '';
                        const isOnChatGPTPage = currentUrl.includes('chatgpt.com') ||
                            currentUrl.includes('services.sheerid.com') ||
                            currentUrl.includes('auth.openai.com');

                        if (isOnChatGPTPage) {
                            // Save tab ID to storage so only this tab will run
                            chrome.storage.local.set({ 'veterans-active-tab-id': tabs[0].id }, () => {
                                console.log('✅ Saved active tab ID:', tabs[0].id);
                                // Try to send message
                                chrome.tabs.sendMessage(tabs[0].id, {
                                    action: 'startVerification',
                                    account: account,
                                    data: workingDataArray,
                                    tabId: tabs[0].id // Include tab ID in message
                                }, (response) => {
                                    if (chrome.runtime.lastError) {
                                        // If message fails, redirect to ChatGPT page (content script might not be loaded)
                                        console.log('Content script not ready, redirecting to ChatGPT...');
                                        updateUIPanelStatus('🌐 Redirecting to ChatGPT page...', 'info');
                                        chrome.tabs.update(tabs[0].id, { url: 'https://chatgpt.com' });
                                    }
                                });
                            });
                        } else {
                            // Not on ChatGPT page, save tab ID and navigate there
                            chrome.storage.local.set({ 'veterans-active-tab-id': tabs[0].id }, () => {
                                updateUIPanelStatus('🌐 Navigating to ChatGPT page...', 'info');
                                chrome.tabs.update(tabs[0].id, { url: 'https://chatgpt.com' });
                            });
                        }
                    });
                });
            });
        });
    }

    // Stop button
    const stopBtn = document.getElementById('veterans-stop-btn');
    if (stopBtn) {
        stopBtn.addEventListener('click', async () => {
            updateUIPanelStatus('⏹️ Stopping verification...', 'info');

            // Save stopped state to storage
            chrome.storage.local.set({ 'veterans-is-running': false });

            // Send message to content script to stop verification
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                if (tabs[0] && tabs[0].url && (tabs[0].url.includes('chatgpt.com') || tabs[0].url.includes('services.sheerid.com'))) {
                    chrome.tabs.sendMessage(tabs[0].id, {
                        action: 'stopVerification'
                    }, (response) => {
                        if (chrome.runtime.lastError) {
                            console.error('Error sending message:', chrome.runtime.lastError);
                        }
                    });
                }
            });

            // Update UI immediately
            updateUIOnStop();
            stopBtn.disabled = true;
            const startBtn = document.getElementById('veterans-start-btn');
            if (startBtn) {
                const hasData = dataArray && dataArray.length > 0;
                startBtn.disabled = !hasData;
            }

            updateUIPanelStatus('✅ Verification stopped', 'success');
        });
    }

    // Skip button - chỉ hoạt động khi tool STOP
    const skipBtn = document.getElementById('veterans-skip-btn');
    if (skipBtn) {
        skipBtn.addEventListener('click', async () => {
            // Check if running
            chrome.storage.local.get(['veterans-is-running'], (result) => {
                if (result['veterans-is-running']) {
                    updateUIPanelStatus('⚠️ Cannot skip while tool is running. Please stop first.', 'info');
                    return;
                }

                chrome.storage.local.get(['veterans-data-array', 'veterans-current-index', 'veterans-stats'], (storageResult) => {
                    let localDataArray = storageResult['veterans-data-array'] || [];
                    let localCurrentIndex = storageResult['veterans-current-index'] || 0;
                    let localStats = storageResult['veterans-stats'] || { processed: 0, success: 0, failed: 0, limit: 0 };

                    if (localDataArray.length === 0) {
                        updateUIPanelStatus('⚠️ No data to skip', 'info');
                        return;
                    }

                    if (localCurrentIndex >= localDataArray.length) {
                        updateUIPanelStatus('⚠️ No more data to skip', 'info');
                        return;
                    }

                    updateUIPanelStatus('⏭️ Skipping current data...', 'info');

                    // Remove current data (skip it)
                    const skippedData = localDataArray[localCurrentIndex];
                    console.log('⏭️ Skipping data:', skippedData.original);
                    localDataArray.splice(localCurrentIndex, 1);

                    // Rebuild data list string
                    const updatedDataList = localDataArray
                        .map((data) => data.original)
                        .join('\n');

                    // Update stats
                    localStats.processed++;
                    localStats.failed++; // Count skipped as failed

                    // Save to storage
                    chrome.storage.local.set({
                        'veterans-data-array': localDataArray,
                        'veterans-data-list': updatedDataList,
                        'veterans-current-index': localCurrentIndex, // Keep same index since we removed one
                        'veterans-is-running': false, // Tool vẫn STOP
                        'veterans-stats': localStats
                    });

                    // Update local state
                    dataArray = localDataArray;
                    stats = localStats;

                    // Check if there's more data
                    if (localCurrentIndex >= localDataArray.length) {
                        // No more data
                        updateUIOnStop();
                        updateUIPanelStatus('✅ All data processed', 'success');
                        return;
                    }

                    // Log next data info
                    const nextData = localDataArray[localCurrentIndex];
                    console.log(`⏭️ Next data after skip: ${nextData.first} ${nextData.last} (index ${localCurrentIndex})`);

                    // Calculate the correct position: localStats.processed is the number already processed
                    // So the next one is localStats.processed + 1
                    // We need the original total count, which is localStats.processed + localDataArray.length (remaining)
                    const originalTotal = localStats.processed + localDataArray.length;
                    const nextPosition = localStats.processed + 1;

                    // Update UI to show next data
                    updateUIPanel();
                    updateUIPanelStatus(
                        `⏭️ Skipped. Next data: ${nextPosition}/${originalTotal}: ${nextData.first} ${nextData.last}`,
                        'success'
                    );
                });
            });
        });
    }

    // Clear Cookies button
    const clearCookiesBtn = document.getElementById('veterans-clear-cookies-btn');
    if (clearCookiesBtn) {
        clearCookiesBtn.addEventListener('click', async () => {
            updateUIPanelStatus('🍪 Đang xóa cookies và data của ChatGPT, OpenAI...', 'info');

            try {
                // Send message to background script to clear cookies and site data
                chrome.runtime.sendMessage({ action: 'clearCookies' }, (response) => {
                    if (chrome.runtime.lastError) {
                        console.error('Error:', chrome.runtime.lastError);
                        updateUIPanelStatus('❌ Lỗi khi xóa: ' + chrome.runtime.lastError.message, 'error');
                        return;
                    }

                    if (response && response.success) {
                        updateUIPanelStatus(`✅ Đã xóa cookies + site data. Kiểm tra lại browser settings.`, 'success');
                        // Không tự động chuyển trang, để user kiểm tra
                    } else {
                        updateUIPanelStatus('❌ Lỗi khi xóa: ' + (response?.error || 'Unknown error'), 'error');
                    }
                });
            } catch (error) {
                console.error('Error clearing cookies:', error);
                updateUIPanelStatus('❌ Lỗi khi xóa cookies: ' + error.message, 'error');
            }
        });
    }

    // Clear SheerID button
    const clearSheerIDBtn = document.getElementById('veterans-clear-sheerid-btn');
    if (clearSheerIDBtn) {
        clearSheerIDBtn.addEventListener('click', async () => {
            updateUIPanelStatus('🔒 Đang xóa SheerID data...', 'info');

            try {
                // Send message to background script to clear SheerID data
                chrome.runtime.sendMessage({ action: 'clearSheerID' }, (response) => {
                    if (chrome.runtime.lastError) {
                        console.error('Error:', chrome.runtime.lastError);
                        updateUIPanelStatus('❌ Lỗi khi xóa SheerID: ' + chrome.runtime.lastError.message, 'error');
                        return;
                    }

                    if (response && response.success) {
                        updateUIPanelStatus(`✅ Đã xóa SheerID data. Kiểm tra lại browser settings.`, 'success');
                    } else {
                        updateUIPanelStatus('❌ Lỗi khi xóa SheerID: ' + (response?.error || 'Unknown error'), 'error');
                    }
                });
            } catch (error) {
                console.error('Error clearing SheerID:', error);
                updateUIPanelStatus('❌ Lỗi khi xóa SheerID: ' + error.message, 'error');
            }
        });
    }

    // Auto Clear SheerID mode selectbox
    const clearSheerIDModeSelect = document.getElementById('veterans-clear-sheerid-mode');
    if (clearSheerIDModeSelect) {
        // Load saved setting
        chrome.storage.local.get(['veterans-clear-sheerid-mode'], (result) => {
            // Default to 'on-error' if not set
            const mode = result['veterans-clear-sheerid-mode'] || 'on-error';
            clearSheerIDModeSelect.value = mode;
        });

        // Save setting on change
        clearSheerIDModeSelect.addEventListener('change', () => {
            const mode = clearSheerIDModeSelect.value;
            chrome.storage.local.set({ 'veterans-clear-sheerid-mode': mode }, () => {
                const modeLabels = {
                    'always': 'Luôn clear',
                    'on-error': 'Chỉ khi lỗi IP/VPN hoặc Limit',
                    'never': 'Không bao giờ'
                };
                console.log(`✅ Auto Clear SheerID mode: ${mode}`);
                updateUIPanelStatus(`🔒 Clear SheerID: ${modeLabels[mode]}`, 'info');
            });
        });
    }

    // Random Discharge Day checkbox and default day
    const randomDischargeDayCheckbox = document.getElementById('veterans-random-discharge-day');
    const defaultDischargeDayInput = document.getElementById('veterans-default-discharge-day');

    if (randomDischargeDayCheckbox && defaultDischargeDayInput) {
        // Load saved settings
        chrome.storage.local.get(['veterans-random-discharge-day', 'veterans-default-discharge-day'], (result) => {
            randomDischargeDayCheckbox.checked = result['veterans-random-discharge-day'] || false;
            defaultDischargeDayInput.value = result['veterans-default-discharge-day'] || 1;
        });

        // Save checkbox on change
        randomDischargeDayCheckbox.addEventListener('change', () => {
            const isRandom = randomDischargeDayCheckbox.checked;
            chrome.storage.local.set({ 'veterans-random-discharge-day': isRandom }, () => {
                console.log(`✅ Random Discharge Day: ${isRandom ? 'Enabled' : 'Disabled'}`);
                updateUIPanelStatus(`🎲 Random Discharge Day: ${isRandom ? 'Bật' : 'Tắt'}`, 'info');
            });
        });

        // Save default day on change
        defaultDischargeDayInput.addEventListener('change', () => {
            let day = parseInt(defaultDischargeDayInput.value) || 1;
            if (day < 1) day = 1;
            if (day > 31) day = 31;
            defaultDischargeDayInput.value = day;
            chrome.storage.local.set({ 'veterans-default-discharge-day': day }, () => {
                console.log(`✅ Default Discharge Day: ${day}`);
                updateUIPanelStatus(`📅 Default Discharge Day: ${day}`, 'info');
            });
        });
    }

    // Auto Retry on Error checkbox and wait time
    const autoRetryCheckbox = document.getElementById('veterans-auto-retry-enabled');
    const retryWaitTimeInput = document.getElementById('veterans-retry-wait-time');

    if (autoRetryCheckbox && retryWaitTimeInput) {
        // Load saved settings
        chrome.storage.local.get(['veterans-auto-retry-enabled', 'veterans-retry-wait-time'], (result) => {
            autoRetryCheckbox.checked = result['veterans-auto-retry-enabled'] || false;
            retryWaitTimeInput.value = result['veterans-retry-wait-time'] || 90;
        });

        // Save checkbox on change
        autoRetryCheckbox.addEventListener('change', () => {
            const isEnabled = autoRetryCheckbox.checked;
            chrome.storage.local.set({ 'veterans-auto-retry-enabled': isEnabled }, () => {
                updateUIPanelStatus(`🔄 Tự động thử lại: ${isEnabled ? 'BẬT' : 'TẮT'}`, 'info');
            });
        });

        // Save wait time on change
        retryWaitTimeInput.addEventListener('change', () => {
            let waitTime = parseInt(retryWaitTimeInput.value) || 90;
            waitTime = Math.max(10, Math.min(600, waitTime)); // Clamp 10-600
            retryWaitTimeInput.value = waitTime;
            chrome.storage.local.set({ 'veterans-retry-wait-time': waitTime }, () => {
                updateUIPanelStatus(`⏳ Thời gian chờ: ${waitTime} giây`, 'info');
            });
        });
    }

    // API Direct Mode checkbox
    const apiDirectCheckbox = document.getElementById('veterans-api-direct-mode');
    if (apiDirectCheckbox) {
        // Load saved setting
        chrome.storage.local.get(['veterans-api-direct-mode'], (result) => {
            apiDirectCheckbox.checked = result['veterans-api-direct-mode'] || false;
        });

        // Save on change
        apiDirectCheckbox.addEventListener('change', () => {
            const isEnabled = apiDirectCheckbox.checked;
            chrome.storage.local.set({ 'veterans-api-direct-mode': isEnabled }, () => {
                updateUIPanelStatus(`API Direct Mode: ${isEnabled ? 'BẬT' : 'TẮT'}`, 'info');
            });
        });
    }

    // Rotate IP API input - load and save
    const rotateIpApiInput = document.getElementById('veterans-rotate-ip-api');
    if (rotateIpApiInput) {
        chrome.storage.local.get(['veterans-rotate-ip-api'], (result) => {
            if (result['veterans-rotate-ip-api']) {
                rotateIpApiInput.value = result['veterans-rotate-ip-api'];
            }
        });

        rotateIpApiInput.addEventListener('change', () => {
            const apiUrl = rotateIpApiInput.value.trim();
            chrome.storage.local.set({ 'veterans-rotate-ip-api': apiUrl }, () => {
                if (apiUrl) {
                    updateUIPanelStatus(`🔄 Đã lưu link đổi IP`, 'success');
                } else {
                    updateUIPanelStatus(`🔄 Đã xóa link đổi IP`, 'info');
                }
            });
        });
    }

    // Max Limit Errors setting
    const maxLimitErrorsInput = document.getElementById('veterans-max-limit-errors');
    if (maxLimitErrorsInput) {
        // Load saved value
        chrome.storage.local.get(['veterans-max-limit-errors'], (result) => {
            const savedValue = result['veterans-max-limit-errors'];
            if (savedValue !== undefined) {
                maxLimitErrorsInput.value = savedValue;
            }
        });

        // Save on change
        maxLimitErrorsInput.addEventListener('change', () => {
            let value = parseInt(maxLimitErrorsInput.value) || 5;
            // Clamp value between 1 and 20
            value = Math.max(1, Math.min(20, value));
            maxLimitErrorsInput.value = value;
            chrome.storage.local.set({ 'veterans-max-limit-errors': value });
            updateUIPanelStatus(`🚫 Sẽ dừng sau ${value} lỗi Limit liên tiếp`, 'info');
        });
    }

    // Proxy settings
    const proxyEnabledCheckbox = document.getElementById('veterans-proxy-enabled');
    const proxyInput = document.getElementById('veterans-proxy-input');
    const proxyStatus = document.getElementById('veterans-proxy-status');

    if (proxyEnabledCheckbox && proxyInput && proxyStatus) {
        // Load saved proxy settings
        chrome.storage.local.get(['veterans-proxy-enabled', 'veterans-proxy-string'], (result) => {
            if (result['veterans-proxy-string']) {
                proxyInput.value = result['veterans-proxy-string'];
            }
            if (result['veterans-proxy-enabled']) {
                proxyEnabledCheckbox.checked = true;
                proxyStatus.textContent = 'Đang bật';
                proxyStatus.style.color = '#34d399';
            }
        });

        // Save proxy string on input change
        proxyInput.addEventListener('change', () => {
            chrome.storage.local.set({ 'veterans-proxy-string': proxyInput.value });
        });

        // Toggle proxy on/off
        proxyEnabledCheckbox.addEventListener('change', () => {
            const isEnabled = proxyEnabledCheckbox.checked;
            const proxyString = proxyInput.value.trim();

            if (isEnabled) {
                if (!proxyString) {
                    updateUIPanelStatus('❌ Vui lòng nhập proxy string!', 'error');
                    proxyEnabledCheckbox.checked = false;
                    return;
                }

                // Parse proxy string: IP:PORT:USER:PASS
                const parts = proxyString.split(':');
                if (parts.length < 4) {
                    updateUIPanelStatus('❌ Proxy format không đúng! Dùng: IP:PORT:USER:PASS', 'error');
                    proxyEnabledCheckbox.checked = false;
                    return;
                }

                const proxyConfig = {
                    host: parts[0],
                    port: parseInt(parts[1]),
                    username: parts[2],
                    password: parts.slice(3).join(':') // Handle passwords with colons
                };

                // Send to background script to enable proxy
                chrome.runtime.sendMessage({ action: 'enableProxy', proxy: proxyConfig }, (response) => {
                    if (chrome.runtime.lastError) {
                        console.error('Proxy error:', chrome.runtime.lastError);
                        updateUIPanelStatus('❌ Lỗi bật proxy: ' + chrome.runtime.lastError.message, 'error');
                        proxyEnabledCheckbox.checked = false;
                        return;
                    }
                    if (response && response.success) {
                        proxyStatus.textContent = 'Đang bật';
                        proxyStatus.style.color = '#34d399';
                        chrome.storage.local.set({
                            'veterans-proxy-enabled': true,
                            'veterans-proxy-string': proxyString
                        });
                        updateUIPanelStatus(`🌐 Proxy đã bật: ${proxyConfig.host}:${proxyConfig.port}`, 'success');
                    } else {
                        updateUIPanelStatus('❌ Không thể bật proxy: ' + (response?.error || 'Unknown error'), 'error');
                        proxyEnabledCheckbox.checked = false;
                    }
                });
            } else {
                // Disable proxy
                chrome.runtime.sendMessage({ action: 'disableProxy' }, (response) => {
                    proxyStatus.textContent = 'Tắt';
                    proxyStatus.style.color = '#71717a';
                    chrome.storage.local.set({ 'veterans-proxy-enabled': false });
                    updateUIPanelStatus('🌐 Proxy đã tắt', 'info');
                });
            }
        });
    }

    // Manual API Verify button handler
    const manualVerifyBtn = document.getElementById('manual-verify-btn');
    const manualSheeridLink = document.getElementById('manual-sheerid-link');
    const manualVerifyEmail = document.getElementById('manual-verify-email');

    if (manualVerifyBtn && manualSheeridLink && manualVerifyEmail) {
        manualVerifyBtn.addEventListener('click', async () => {
            const link = manualSheeridLink.value.trim();
            let email = manualVerifyEmail.value.trim();

            // Validate link
            if (!link) {
                updateApiDirectLog('❌ Vui lòng paste SheerID link!');
                return;
            }

            // Auto generate email if empty
            if (!email) {
                updateApiDirectLog('📧 No email, auto-generating...');
                manualVerifyBtn.disabled = true;
                manualVerifyBtn.textContent = '⏳ Gen email...';

                email = await generateEmailForManual();
                if (!email) {
                    manualVerifyBtn.disabled = false;
                    manualVerifyBtn.textContent = '🚀 VERIFY (API)';
                    return;
                }
                manualVerifyEmail.value = email;
            }

            // Extract verificationId
            const verificationId = extractVerificationIdFromUrl(link);
            if (!verificationId) {
                updateApiDirectLog('❌ Không tìm thấy verificationId trong link!');
                updateApiDirectLog('Link cần có dạng: ...?verificationId=abc123...');
                return;
            }

            updateApiDirectLog(`🔍 Found verificationId: ${verificationId.substring(0, 10)}...`);

            // Get current veteran data
            chrome.storage.local.get(['veterans-data-array', 'veterans-current-index'], async (result) => {
                const localDataArray = result['veterans-data-array'] || [];
                const localCurrentIndex = result['veterans-current-index'] || 0;

                if (localDataArray.length === 0 || localCurrentIndex >= localDataArray.length) {
                    updateApiDirectLog('❌ Không có veteran data! Load file VETERANS trước.');
                    return;
                }

                const veteranData = localDataArray[localCurrentIndex];
                updateApiDirectLog(`👤 Veteran: ${veteranData.first} ${veteranData.last}`);
                updateApiDirectLog(`🌿 Branch: ${veteranData.branch}`);
                updateApiDirectLog(`📧 Email: ${email}`);

                // Format birth date
                const monthNum = MONTH_TO_NUM_PANEL[veteranData.month] || "01";
                const dayPadded = String(veteranData.day).padStart(2, '0');
                const birthDate = `${veteranData.year}-${monthNum}-${dayPadded}`;
                updateApiDirectLog(`🎂 Birth: ${birthDate}`);

                // Disable button
                manualVerifyBtn.disabled = true;
                manualVerifyBtn.textContent = '⏳ Verifying...';

                updateApiDirectLog('🚀 Calling SheerID API...');

                // Call background script for API verification
                chrome.runtime.sendMessage({
                    action: 'sheeridVerify',
                    verificationId: verificationId,
                    veteranData: {
                        first: veteranData.first,
                        last: veteranData.last,
                        branch: veteranData.branch,
                        birthDate: birthDate,
                        dischargeDate: '2025-12-01'
                    },
                    email: email
                }, async (response) => {
                    // Re-enable button
                    manualVerifyBtn.disabled = false;
                    manualVerifyBtn.textContent = '🚀 VERIFY (API)';

                    // Clear link input after verify (each verification_id is single-use)
                    manualSheeridLink.value = '';

                    if (chrome.runtime.lastError) {
                        updateApiDirectLog('❌ Error: ' + chrome.runtime.lastError.message);
                        return;
                    }

                    if (!response) {
                        updateApiDirectLog('❌ No response from background!');
                        return;
                    }

                    if (response.success) {
                        const result = response.result;
                        const currentStep = result.currentStep || 'unknown';
                        updateApiDirectLog(`✅ API Response: ${currentStep}`);

                        if (currentStep === 'success') {
                            manualConsecutiveLimitErrors = 0; // Reset on success
                            updateApiDirectLog('🎉 VERIFICATION SUCCESS!');
                            updateUIPanelStatus('🎉 Manual API Verify: SUCCESS!', 'success');
                        } else if (currentStep === 'emailLoop') {
                            manualConsecutiveLimitErrors = 0; // Reset on success
                            updateApiDirectLog('📧 Email sent! Auto-checking in 5s...');
                            updateUIPanelStatus('📧 Manual API Verify: Check email!', 'info');

                            // Auto check email after 5 seconds
                            setTimeout(async () => {
                                updateApiDirectLog('📬 Auto-checking email...');
                                const emailLink = await checkEmailForLink(email);

                                const linkResult = document.getElementById('manual-email-link-result');
                                const linkEl = document.getElementById('manual-email-link');

                                if (emailLink && linkResult && linkEl) {
                                    linkEl.href = emailLink;
                                    linkEl.textContent = emailLink.length > 60 ? emailLink.substring(0, 60) + '...' : emailLink;
                                    linkEl.dataset.fullLink = emailLink;
                                    linkResult.style.display = 'block';
                                    updateApiDirectLog('✅ Link found! Click or copy link ở trên.');
                                } else {
                                    updateApiDirectLog('📭 No link yet. Click "📬 Check" to retry.');
                                }
                            }, 5000);
                        } else {
                            updateApiDirectLog(`⚠️ Status: ${currentStep}`);
                            if (result.errorIds) {
                                updateApiDirectLog(`⚠️ Errors: ${JSON.stringify(result.errorIds)}`);
                            }
                        }
                    } else {
                        const errorMsg = (response.error || 'Unknown').toLowerCase();
                        const detailsStr = (response.details || '').toLowerCase();

                        // Check if 429 or limit error
                        const isLimitError = errorMsg.includes('429') ||
                            errorMsg.includes('limit') ||
                            errorMsg.includes('redeemed') ||
                            errorMsg.includes('rate') ||
                            detailsStr.includes('429') ||
                            detailsStr.includes('limit') ||
                            detailsStr.includes('redeemed');

                        if (isLimitError) {
                            manualConsecutiveLimitErrors++;
                            updateApiDirectLog(`🚫 Limit Error (${manualConsecutiveLimitErrors}/${MAX_MANUAL_CONSECUTIVE_LIMIT})`);

                            if (manualConsecutiveLimitErrors >= MAX_MANUAL_CONSECUTIVE_LIMIT) {
                                updateApiDirectLog(`🛑 ${MAX_MANUAL_CONSECUTIVE_LIMIT} lỗi Limit liên tiếp!`);
                                updateApiDirectLog('⚠️ Cần đổi IP/VPN trước khi tiếp tục!');
                                updateUIPanelStatus('🛑 Rate Limit - Đổi IP/VPN!', 'error');
                            }
                        } else {
                            manualConsecutiveLimitErrors = 0; // Reset for non-limit errors
                        }

                        updateApiDirectLog('❌ API Error: ' + (response.error || 'Unknown'));
                        if (response.details) {
                            // Try to parse error details
                            try {
                                const details = JSON.parse(response.details);
                                if (details.errorIds) {
                                    updateApiDirectLog('⚠️ Errors: ' + JSON.stringify(details.errorIds));
                                }
                                if (details.currentStep) {
                                    updateApiDirectLog('⚠️ Step: ' + details.currentStep);
                                }
                            } catch (e) {
                                updateApiDirectLog('⚠️ Details: ' + response.details.substring(0, 100));
                            }
                        }
                    }
                });
            });
        });
    }


    // Manual Get Link button - calls ChatGPT API via content script
    const manualGetLinkBtn = document.getElementById('manual-get-link-btn');
    if (manualGetLinkBtn && manualSheeridLink) {
        manualGetLinkBtn.addEventListener('click', async () => {
            updateApiDirectLog('🔓 Getting verification link...');
            manualGetLinkBtn.disabled = true;
            manualGetLinkBtn.textContent = '⏳...';

            // Check if current tab is on SheerID with verificationId
            chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
                const currentUrl = tabs[0]?.url || '';
                const currentTabId = tabs[0]?.id;

                // If already on SheerID with verificationId, just get URL from page
                if (currentUrl.includes('services.sheerid.com') && currentUrl.includes('verificationId=')) {
                    manualSheeridLink.value = currentUrl;
                    updateApiDirectLog('✅ Got link from current SheerID page!');
                    manualGetLinkBtn.disabled = false;
                    manualGetLinkBtn.textContent = '🔓 Get';
                    return;
                }

                // If on ChatGPT page, use content script (has proper cookies context)
                if (currentUrl.includes('chatgpt.com')) {
                    updateApiDirectLog('📡 Calling API via content script...');

                    chrome.tabs.sendMessage(currentTabId, {
                        action: 'createVerification'
                    }, (response) => {
                        manualGetLinkBtn.disabled = false;
                        manualGetLinkBtn.textContent = '🔓 Get';

                        if (chrome.runtime.lastError) {
                            updateApiDirectLog('❌ Error: ' + chrome.runtime.lastError.message);
                            updateApiDirectLog('💡 Try refreshing the ChatGPT page');
                            return;
                        }

                        if (response && response.success && response.link) {
                            manualSheeridLink.value = response.link;
                            updateApiDirectLog('✅ Got verification link!');
                            if (response.verificationId) {
                                updateApiDirectLog(`🆔 ID: ${response.verificationId}`);
                            }
                            updateApiDirectLog(`📎 ${response.link.substring(0, 60)}...`);
                        } else {
                            updateApiDirectLog('❌ Failed: ' + (response?.error || 'Unknown'));
                        }
                    });
                    return;
                }

                // Not on ChatGPT - try to find a ChatGPT tab
                chrome.tabs.query({ url: '*://chatgpt.com/*' }, (chatgptTabs) => {
                    if (chatgptTabs && chatgptTabs.length > 0) {
                        const chatgptTab = chatgptTabs[0];
                        updateApiDirectLog(`📡 Found ChatGPT tab, calling API...`);

                        chrome.tabs.sendMessage(chatgptTab.id, {
                            action: 'createVerification'
                        }, (response) => {
                            manualGetLinkBtn.disabled = false;
                            manualGetLinkBtn.textContent = '🔓 Get';

                            if (chrome.runtime.lastError) {
                                updateApiDirectLog('❌ Error: ' + chrome.runtime.lastError.message);
                                updateApiDirectLog('💡 Go to ChatGPT tab and refresh');
                                return;
                            }

                            if (response && response.success && response.link) {
                                manualSheeridLink.value = response.link;
                                updateApiDirectLog('✅ Got verification link!');
                                if (response.verificationId) {
                                    updateApiDirectLog(`🆔 ID: ${response.verificationId}`);
                                }
                                updateApiDirectLog(`📎 ${response.link.substring(0, 60)}...`);
                            } else {
                                updateApiDirectLog('❌ Failed: ' + (response?.error || 'Unknown'));
                            }
                        });
                    } else {
                        manualGetLinkBtn.disabled = false;
                        manualGetLinkBtn.textContent = '🔓 Get';
                        updateApiDirectLog('❌ No ChatGPT tab found!');
                        updateApiDirectLog('💡 Open chatgpt.com and login first');
                    }
                });
            });
        });
    }

    // Manual Refresh Enrollment Status button - uses content script on ChatGPT page
    const manualRefreshBtn = document.getElementById('manual-refresh-btn');
    if (manualRefreshBtn) {
        manualRefreshBtn.addEventListener('click', async () => {
            updateApiDirectLog('🔄 Refreshing enrollment status...');
            manualRefreshBtn.disabled = true;
            manualRefreshBtn.textContent = '⏳';

            // Find ChatGPT tab to send message
            chrome.tabs.query({ url: '*://chatgpt.com/*' }, (chatgptTabs) => {
                if (!chatgptTabs || chatgptTabs.length === 0) {
                    // Try current tab
                    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                        const currentUrl = tabs[0]?.url || '';
                        if (!currentUrl.includes('chatgpt.com')) {
                            manualRefreshBtn.disabled = false;
                            manualRefreshBtn.textContent = '🔄';
                            updateApiDirectLog('❌ No ChatGPT tab found!');
                            updateApiDirectLog('💡 Open chatgpt.com and login first');
                            return;
                        }
                        sendRefreshMessage(tabs[0].id);
                    });
                    return;
                }
                sendRefreshMessage(chatgptTabs[0].id);
            });

            function sendRefreshMessage(tabId) {
                chrome.tabs.sendMessage(tabId, {
                    action: 'refreshEnrollment'
                }, (response) => {
                    manualRefreshBtn.disabled = false;
                    manualRefreshBtn.textContent = '🔄';

                    if (chrome.runtime.lastError) {
                        updateApiDirectLog('❌ Error: ' + chrome.runtime.lastError.message);
                        updateApiDirectLog('💡 Try refreshing the ChatGPT page');
                        return;
                    }

                    if (response && response.success) {
                        updateApiDirectLog('✅ Enrollment status refreshed!');
                        if (response.data && response.data.verification_id) {
                            updateApiDirectLog(`🆔 Current ID: ${response.data.verification_id.substring(0, 10)}...`);
                        }
                        updateApiDirectLog('💡 Now click "🔓 Get" to get new link');
                    } else {
                        updateApiDirectLog('❌ Refresh failed: ' + (response?.error || 'Unknown'));
                    }
                });
            }
        });
    }

    // Manual Generate Email button
    const manualGenEmailBtn = document.getElementById('manual-gen-email-btn');
    const manualEmailInput = document.getElementById('manual-verify-email');
    if (manualGenEmailBtn && manualEmailInput) {
        manualGenEmailBtn.addEventListener('click', async () => {
            manualGenEmailBtn.disabled = true;
            manualGenEmailBtn.textContent = '⏳...';

            const email = await generateEmailForManual();
            if (email) {
                manualEmailInput.value = email;
            }

            manualGenEmailBtn.disabled = false;
            manualGenEmailBtn.textContent = '📧 Gen';
        });
    }

    // Manual Check Email button
    const manualCheckEmailBtn = document.getElementById('manual-check-email-btn');
    const manualEmailLinkResult = document.getElementById('manual-email-link-result');
    const manualEmailLink = document.getElementById('manual-email-link');
    if (manualCheckEmailBtn && manualEmailInput) {
        manualCheckEmailBtn.addEventListener('click', async () => {
            const email = manualEmailInput.value.trim();
            if (!email) {
                updateApiDirectLog('❌ Nhập email trước khi check!');
                return;
            }

            manualCheckEmailBtn.disabled = true;
            manualCheckEmailBtn.textContent = '⏳...';

            const link = await checkEmailForLink(email);

            if (link && manualEmailLinkResult && manualEmailLink) {
                manualEmailLink.href = link;
                manualEmailLink.textContent = link.length > 60 ? link.substring(0, 60) + '...' : link;
                manualEmailLink.dataset.fullLink = link;
                manualEmailLinkResult.style.display = 'block';
            }

            manualCheckEmailBtn.disabled = false;
            manualCheckEmailBtn.textContent = '📬 Check';
        });
    }

    // Copy Link button
    const manualCopyLinkBtn = document.getElementById('manual-copy-link-btn');
    if (manualCopyLinkBtn && manualEmailLink) {
        manualCopyLinkBtn.addEventListener('click', () => {
            const fullLink = manualEmailLink.dataset.fullLink || manualEmailLink.href;
            navigator.clipboard.writeText(fullLink).then(() => {
                updateApiDirectLog('📋 Link copied!');
                manualCopyLinkBtn.textContent = '✓';
                setTimeout(() => {
                    manualCopyLinkBtn.textContent = 'Copy';
                }, 1500);
            }).catch(err => {
                updateApiDirectLog('❌ Copy failed: ' + err.message);
            });
        });
    }

    // API Log Clear button
    const apiLogClearBtn = document.getElementById('api-log-clear-btn');
    if (apiLogClearBtn) {
        apiLogClearBtn.addEventListener('click', () => {
            const logEl = document.getElementById('api-direct-log');
            if (logEl) {
                logEl.value = 'Cleared. Ready for manual verify...';
            }
        });
    }

    // Manual API Section Collapsible Toggle
    const manualApiHeader = document.getElementById('manual-api-header');
    const manualApiContent = document.getElementById('manual-api-content');
    const manualApiToggle = document.getElementById('manual-api-toggle');

    if (manualApiHeader && manualApiContent && manualApiToggle) {
        // Load saved state
        chrome.storage.local.get(['manual-api-expanded'], (result) => {
            if (result['manual-api-expanded']) {
                manualApiContent.style.display = 'block';
                manualApiToggle.style.transform = 'rotate(180deg)';
            }
        });

        // Toggle on click
        manualApiHeader.addEventListener('click', () => {
            const isHidden = manualApiContent.style.display === 'none';

            manualApiContent.style.display = isHidden ? 'block' : 'none';
            manualApiToggle.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';

            // Save state
            chrome.storage.local.set({ 'manual-api-expanded': isHidden });
        });
    }

    // Initial update of manual veteran display
    updateManualVeteranDisplay();

    // =========================================
    // RANDOM VERIFY SECTION - Event Handlers
    // =========================================

    const randomApiHeader = document.getElementById('random-api-header');
    const randomApiContent = document.getElementById('random-api-content');
    const randomApiToggle = document.getElementById('random-api-toggle');

    // Collapsible toggle for RANDOM VERIFY section
    if (randomApiHeader && randomApiContent && randomApiToggle) {
        // Load saved state
        chrome.storage.local.get(['random-api-expanded'], (result) => {
            if (result['random-api-expanded']) {
                randomApiContent.style.display = 'block';
                randomApiToggle.style.transform = 'rotate(180deg)';
            }
        });

        // Toggle on click
        randomApiHeader.addEventListener('click', () => {
            const isHidden = randomApiContent.style.display === 'none';
            randomApiContent.style.display = isHidden ? 'block' : 'none';
            randomApiToggle.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
            chrome.storage.local.set({ 'random-api-expanded': isHidden });
        });
    }

    // Random API Log helper
    function randomLog(msg) {
        const logEl = document.getElementById('random-api-log');
        if (logEl) {
            const time = new Date().toLocaleTimeString('vi-VN');
            logEl.value += `[${time}] ${msg}\n`;
            logEl.scrollTop = logEl.scrollHeight;
        }
    }

    // Random generators (for preview)
    const FIRST_NAMES = ['James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Charles'];
    const LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez'];
    const BRANCHES = ['Army', 'Air Force', 'Navy', 'Marine Corps', 'Coast Guard'];

    function randomChoice(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

    function generateRandomBirthDate() {
        const today = new Date();
        const minAge = 25, maxAge = 55;
        const minDate = new Date(today); minDate.setFullYear(today.getFullYear() - maxAge);
        const maxDate = new Date(today); maxDate.setFullYear(today.getFullYear() - minAge);
        const d = new Date(minDate.getTime() + Math.random() * (maxDate.getTime() - minDate.getTime()));
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    }

    function generateRandomDischargeDate() {
        const today = new Date();
        const daysAgo = Math.floor(Math.random() * 300) + 30;
        const d = new Date(today); d.setDate(today.getDate() - daysAgo);
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    }

    // TinyHost domains that work with tinyhost.shop API
    const TINYHOST_DOMAINS = ['topnova.net', 'mailhub.pw', 'emlhub.com', 'zetmail.com', 'mailpoof.com'];

    function generateRandomEmail() {
        const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
        let u = ''; for (let i = 0; i < 16; i++) u += chars[Math.floor(Math.random() * chars.length)];
        const domain = TINYHOST_DOMAINS[Math.floor(Math.random() * TINYHOST_DOMAINS.length)];
        return `${u}@${domain}`;
    }

    // Store last generated preview for reference
    let lastRandomPreview = null;

    // Random Preview Button
    const randomPreviewBtn = document.getElementById('random-preview-btn');
    if (randomPreviewBtn) {
        randomPreviewBtn.addEventListener('click', () => {
            const firstName = randomChoice(FIRST_NAMES);
            const lastName = randomChoice(LAST_NAMES);
            const branch = randomChoice(BRANCHES);
            const birthDate = generateRandomBirthDate();
            const dischargeDate = generateRandomDischargeDate();

            lastRandomPreview = { firstName, lastName, branch, birthDate, dischargeDate };

            document.getElementById('random-preview-name').textContent = `👤 Name: ${firstName} ${lastName}`;
            document.getElementById('random-preview-branch').textContent = `🏛️ Branch: ${branch}`;
            document.getElementById('random-preview-birth').textContent = `📅 Birth: ${birthDate}`;
            document.getElementById('random-preview-discharge').textContent = `📅 Discharge: ${dischargeDate}`;

            randomLog(`🎲 Preview: ${firstName} ${lastName} | ${branch}`);
        });
    }

    // Random Generate Email Button
    const randomGenEmailBtn = document.getElementById('random-gen-email-btn');
    if (randomGenEmailBtn) {
        randomGenEmailBtn.addEventListener('click', () => {
            const email = generateRandomEmail();
            document.getElementById('random-verify-email').value = email;
            randomLog(`📧 Generated: ${email}`);
        });
    }

    // Random Get Link Button - Use content script like MANUAL section
    const randomGetLinkBtn = document.getElementById('random-get-link-btn');
    if (randomGetLinkBtn) {
        randomGetLinkBtn.addEventListener('click', async () => {
            randomLog('🔓 Getting verification link...');
            randomGetLinkBtn.disabled = true;
            randomGetLinkBtn.textContent = '⏳...';

            const randomSheeridLink = document.getElementById('random-sheerid-link');

            chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
                const currentUrl = tabs[0]?.url || '';
                const currentTabId = tabs[0]?.id;

                // If already on SheerID with verificationId, just get URL from page
                if (currentUrl.includes('services.sheerid.com') && currentUrl.includes('verificationId=')) {
                    randomSheeridLink.value = currentUrl;
                    randomLog('✅ Got link from current SheerID page!');
                    randomGetLinkBtn.disabled = false;
                    randomGetLinkBtn.textContent = '🔓 Get';
                    return;
                }

                // If on ChatGPT page, use content script (has proper cookies context)
                if (currentUrl.includes('chatgpt.com')) {
                    randomLog('📡 Calling API via content script...');

                    chrome.tabs.sendMessage(currentTabId, {
                        action: 'createVerification'
                    }, (response) => {
                        randomGetLinkBtn.disabled = false;
                        randomGetLinkBtn.textContent = '🔓 Get';

                        if (chrome.runtime.lastError) {
                            randomLog('❌ Error: ' + chrome.runtime.lastError.message);
                            randomLog('💡 Try refreshing the ChatGPT page');
                            return;
                        }

                        if (response && response.success && response.link) {
                            randomSheeridLink.value = response.link;
                            randomLog('✅ Got verification link!');
                            if (response.verificationId) {
                                randomLog(`🆔 ID: ...${response.verificationId.slice(-8)}`);
                            }
                        } else {
                            randomLog('❌ Failed: ' + (response?.error || 'Unknown'));
                        }
                    });
                    return;
                }

                // Not on ChatGPT - try to find a ChatGPT tab
                chrome.tabs.query({ url: '*://chatgpt.com/*' }, (chatgptTabs) => {
                    if (chatgptTabs && chatgptTabs.length > 0) {
                        const chatgptTab = chatgptTabs[0];
                        randomLog(`📡 Found ChatGPT tab, calling API...`);

                        chrome.tabs.sendMessage(chatgptTab.id, {
                            action: 'createVerification'
                        }, (response) => {
                            randomGetLinkBtn.disabled = false;
                            randomGetLinkBtn.textContent = '🔓 Get';

                            if (chrome.runtime.lastError) {
                                randomLog('❌ Error: ' + chrome.runtime.lastError.message);
                                randomLog('💡 Go to ChatGPT tab and refresh');
                                return;
                            }

                            if (response && response.success && response.link) {
                                randomSheeridLink.value = response.link;
                                randomLog('✅ Got verification link!');
                                if (response.verificationId) {
                                    randomLog(`🆔 ID: ...${response.verificationId.slice(-8)}`);
                                }
                            } else {
                                randomLog('❌ Failed: ' + (response?.error || 'Unknown'));
                            }
                        });
                    } else {
                        randomGetLinkBtn.disabled = false;
                        randomGetLinkBtn.textContent = '🔓 Get';
                        randomLog('❌ No ChatGPT tab found!');
                        randomLog('💡 Open chatgpt.com and login first');
                    }
                });
            });
        });
    }

    // Store last verify result for Check Email
    let lastRandomVerifyResult = null;
    let lastRandomVerifyEmail = null;

    // Random Verify Button (main action)
    const randomVerifyBtn = document.getElementById('random-verify-btn');
    if (randomVerifyBtn) {
        randomVerifyBtn.addEventListener('click', async () => {
            const linkInput = document.getElementById('random-sheerid-link');
            const emailInput = document.getElementById('random-verify-email');

            const link = linkInput?.value?.trim();
            const email = emailInput?.value?.trim() || null; // null = will random generate

            if (!link) {
                randomLog('❌ Vui lòng nhập SheerID link!');
                return;
            }

            // Extract verificationId
            const match = link.match(/verificationId=([a-f0-9]+)/i);
            if (!match) {
                randomLog('❌ Không tìm thấy verificationId trong link!');
                return;
            }
            const verificationId = match[1];

            randomLog('🎲 Starting RANDOM verify...');
            randomLog(`   ID: ...${verificationId.slice(-8)}`);
            if (email) randomLog(`   Email: ${email}`);
            else randomLog(`   Email: (will random)`);

            randomVerifyBtn.disabled = true;
            randomVerifyBtn.textContent = '⏳ Verifying...';

            try {
                const response = await new Promise((resolve) => {
                    chrome.runtime.sendMessage({
                        action: 'randomSheeridVerify',
                        verificationId: verificationId,
                        email: email
                    }, resolve);
                });

                if (response && response.success) {
                    const result = response.result;
                    const vet = response.veteranData;

                    randomLog(`✅ Success! Step: ${result.currentStep}`);
                    randomLog(`   Veteran: ${vet.firstName} ${vet.lastName}`);
                    randomLog(`   Branch: ${vet.branch}`);
                    randomLog(`   Email: ${vet.email}`);

                    // Update preview with actual used data
                    document.getElementById('random-preview-name').textContent = `👤 Name: ${vet.firstName} ${vet.lastName}`;
                    document.getElementById('random-preview-branch').textContent = `🏛️ Branch: ${vet.branch}`;
                    document.getElementById('random-preview-birth').textContent = `📅 Birth: ${vet.birthDate}`;
                    document.getElementById('random-preview-discharge').textContent = `📅 Discharge: ${vet.dischargeDate}`;

                    // Store for Check Email
                    lastRandomVerifyResult = result;
                    lastRandomVerifyEmail = vet.email;

                    if (result.currentStep === 'emailLoop') {
                        randomLog('📧 Cần xác nhận email - click Check Email!');
                    } else if (result.currentStep === 'docUpload') {
                        randomLog('📄 Yêu cầu upload document - auto verify failed');
                    }
                } else {
                    randomLog(`❌ Failed: ${response?.error || 'Unknown error'}`);
                    if (response?.veteranData) {
                        randomLog(`   Data used: ${response.veteranData.firstName} ${response.veteranData.lastName}`);
                    }
                }
            } catch (err) {
                randomLog(`❌ Error: ${err.message}`);
            } finally {
                randomVerifyBtn.disabled = false;
                randomVerifyBtn.textContent = '🎲 VERIFY 1 (Manual)';
            }
        });
    }

    // Random Check Email Button - reuse checkEmailForLink function from MANUAL section
    const randomCheckEmailBtn = document.getElementById('random-check-email-btn');
    const randomEmailInput = document.getElementById('random-verify-email');
    const randomEmailLinkResult = document.getElementById('random-email-link-result');
    const randomEmailLink = document.getElementById('random-email-link');

    if (randomCheckEmailBtn && randomEmailInput) {
        randomCheckEmailBtn.addEventListener('click', async () => {
            // Use email from input or from last verify result
            const email = randomEmailInput.value.trim() || lastRandomVerifyEmail;
            if (!email) {
                randomLog('❌ Nhập email trước khi check!');
                return;
            }

            randomCheckEmailBtn.disabled = true;
            randomCheckEmailBtn.textContent = '⏳...';
            randomLog(`📬 Checking inbox: ${email}...`);

            try {
                // Use same checkEmailForLink function as MANUAL section
                const link = await checkEmailForLink(email);

                if (link && randomEmailLinkResult && randomEmailLink) {
                    randomEmailLink.href = link;
                    randomEmailLink.textContent = link.length > 60 ? link.substring(0, 60) + '...' : link;
                    randomEmailLink.dataset.fullLink = link;
                    randomEmailLinkResult.style.display = 'block';
                    randomLog('✅ Found verification link!');
                } else {
                    randomLog('📭 No emails yet. Try again in a few seconds...');
                }
            } catch (err) {
                randomLog(`❌ Error: ${err.message}`);
            }

            randomCheckEmailBtn.disabled = false;
            randomCheckEmailBtn.textContent = '📬 Check';
        });
    }

    // Random Copy Link button
    const randomCopyLinkBtn = document.getElementById('random-copy-link-btn');
    if (randomCopyLinkBtn && randomEmailLink) {
        randomCopyLinkBtn.addEventListener('click', () => {
            const fullLink = randomEmailLink.dataset.fullLink || randomEmailLink.href;
            navigator.clipboard.writeText(fullLink).then(() => {
                randomLog('📋 Link copied!');
                randomCopyLinkBtn.textContent = '✓';
                setTimeout(() => {
                    randomCopyLinkBtn.textContent = 'Copy';
                }, 1500);
            }).catch(err => {
                randomLog('❌ Copy failed: ' + err.message);
            });
        });
    }

    // Random Log Clear Button
    const randomLogClearBtn = document.getElementById('random-log-clear-btn');
    if (randomLogClearBtn) {
        randomLogClearBtn.addEventListener('click', () => {
            const logEl = document.getElementById('random-api-log');
            if (logEl) logEl.value = 'Cleared. Ready for random verify...';
        });
    }

    // =========================================
    // RANDOM VERIFY AUTO-LOOP (Standalone)
    // =========================================
    let isRandomAutoRunning = false;
    let randomStats = { processed: 0, success: 0, failed: 0 };

    function updateRandomStats() {
        const pEl = document.getElementById('random-stats-processed');
        const sEl = document.getElementById('random-stats-success');
        const fEl = document.getElementById('random-stats-failed');
        if (pEl) pEl.textContent = randomStats.processed;
        if (sEl) sEl.textContent = randomStats.success;
        if (fEl) fEl.textContent = randomStats.failed;
    }

    function updateRandomButtonStates() {
        const startBtn = document.getElementById('random-start-auto-btn');
        const stopBtn = document.getElementById('random-stop-btn');
        if (startBtn) {
            startBtn.disabled = isRandomAutoRunning;
            startBtn.style.opacity = isRandomAutoRunning ? '0.5' : '1';
        }
        if (stopBtn) {
            stopBtn.disabled = !isRandomAutoRunning;
            stopBtn.style.opacity = isRandomAutoRunning ? '1' : '0.5';
        }
    }

    // Start Auto Button - Use same flow as main Start button but with random data
    const randomStartAutoBtn = document.getElementById('random-start-auto-btn');
    const randomStopBtn = document.getElementById('random-stop-btn');

    if (randomStartAutoBtn) {
        randomStartAutoBtn.addEventListener('click', async () => {
            if (isRandomAutoRunning) return;

            isRandomAutoRunning = true;
            updateRandomButtonStates();
            randomLog('▶️ Starting Auto Random Verify (uses main flow)...');
            randomLog('   This will auto-navigate and login like main Start button');

            // Get ChatGPT account from storage
            chrome.storage.local.get(['chatgpt-account'], async (result) => {
                const account = result['chatgpt-account'];

                // Generate random veterans data (one at a time, loop will generate more)
                const generateRandomVeteranLine = () => {
                    const FIRST_NAMES = ['James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Charles', 'Christopher', 'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven', 'Paul', 'Andrew', 'Joshua', 'Kenneth', 'Kevin', 'Brian', 'George', 'Timothy', 'Ronald', 'Edward', 'Jason', 'Jeffrey', 'Ryan'];
                    const LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White', 'Harris', 'Clark', 'Lewis', 'Robinson', 'Walker'];
                    const BRANCHES = ['Army', 'Air Force', 'Navy', 'Marine Corps', 'Coast Guard'];
                    const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

                    const firstName = FIRST_NAMES[Math.floor(Math.random() * FIRST_NAMES.length)];
                    const lastName = LAST_NAMES[Math.floor(Math.random() * LAST_NAMES.length)];
                    const branch = BRANCHES[Math.floor(Math.random() * BRANCHES.length)];
                    const month = MONTHS[Math.floor(Math.random() * MONTHS.length)];
                    const day = Math.floor(Math.random() * 28) + 1;
                    const year = Math.floor(Math.random() * (1985 - 1950)) + 1950;

                    return `${firstName.toUpperCase()}|${lastName.toUpperCase()}|${branch}|${month}|${day}|${year}`;
                };

                // Main loop
                while (isRandomAutoRunning) {
                    try {
                        // Generate single random veteran for this iteration
                        const randomLine = generateRandomVeteranLine();
                        const parts = randomLine.split('|');

                        // Month name to number mapping
                        const MONTH_TO_NUM = {
                            "January": "01", "February": "02", "March": "03", "April": "04",
                            "May": "05", "June": "06", "July": "07", "August": "08",
                            "September": "09", "October": "10", "November": "11", "December": "12"
                        };

                        const monthNum = MONTH_TO_NUM[parts[3]] || "01";
                        const dayPadded = String(parts[4]).padStart(2, '0');
                        const birthDate = `${parts[5]}-${monthNum}-${dayPadded}`;

                        // Discharge date: random day in 2025
                        const dischargeDate = "2025-12-01";

                        const veteranData = {
                            first: parts[0],
                            last: parts[1],
                            branch: parts[2],
                            month: parts[3],
                            day: parts[4],
                            year: parts[5],
                            birthDate: birthDate,       // Add for API
                            dischargeDate: dischargeDate, // Add for API
                            original: randomLine
                        };

                        randomLog(`🎲 Generated: ${veteranData.first} ${veteranData.last} (${veteranData.branch})`);

                        // Update preview
                        document.getElementById('random-preview-name').textContent = `👤 Name: ${veteranData.first} ${veteranData.last}`;
                        document.getElementById('random-preview-branch').textContent = `🏛️ Branch: ${veteranData.branch}`;
                        document.getElementById('random-preview-birth').textContent = `📅 Birth: ${veteranData.month} ${veteranData.day}, ${veteranData.year}`;

                        // Save to storage and trigger verification
                        await new Promise((resolve) => {
                            chrome.storage.local.set({
                                'chatgpt-account': account,
                                'veterans-data-array': [veteranData],
                                'veterans-data-list': randomLine,
                                'veterans-current-index': 0,
                                'veterans-is-running': true,
                                'veterans-is-random-mode': true, // Mark as random mode
                                'veterans-stats': { processed: 0, success: 0, failed: 0, limit: 0 },
                                'veterans-consecutive-limit-errors': 0
                            }, resolve);
                        });

                        // Find or create ChatGPT tab
                        const tabs = await new Promise(resolve => {
                            chrome.tabs.query({ url: '*://chatgpt.com/*' }, resolve);
                        });

                        let targetTab;
                        if (tabs && tabs.length > 0) {
                            targetTab = tabs[0];
                            randomLog('📍 Using existing ChatGPT tab');
                        } else {
                            // Create new tab
                            randomLog('🌐 Creating new ChatGPT tab...');
                            targetTab = await new Promise(resolve => {
                                chrome.tabs.create({ url: 'https://chatgpt.com' }, resolve);
                            });
                            // Wait for tab to load
                            await new Promise(r => setTimeout(r, 5000));
                        }

                        if (!isRandomAutoRunning) break;

                        // Save tab ID
                        await new Promise(resolve => {
                            chrome.storage.local.set({ 'veterans-active-tab-id': targetTab.id }, resolve);
                        });

                        // Send startVerification message
                        randomLog('🚀 Starting verification flow...');

                        const verifyResult = await new Promise((resolve) => {
                            chrome.tabs.sendMessage(targetTab.id, {
                                action: 'startVerification',
                                account: account,
                                data: [veteranData],
                                tabId: targetTab.id,
                                isRandomMode: true // Tell content script this is random mode
                            }, (response) => {
                                if (chrome.runtime.lastError) {
                                    resolve({ success: false, error: chrome.runtime.lastError.message });
                                } else {
                                    resolve(response || { success: true });
                                }
                            });
                        });

                        if (!isRandomAutoRunning) break;

                        // Wait for verification to complete (check storage for result)
                        randomLog('⏳ Waiting for verification result...');
                        let waitCount = 0;
                        const MAX_WAIT = 60; // 60 seconds max

                        while (waitCount < MAX_WAIT && isRandomAutoRunning) {
                            await new Promise(r => setTimeout(r, 1000));
                            waitCount++;

                            // Check if verification completed
                            const status = await new Promise(resolve => {
                                chrome.storage.local.get(['veterans-is-running', 'veterans-stats', 'veterans-last-result'], resolve);
                            });

                            if (!status['veterans-is-running']) {
                                // Verification finished
                                const stats = status['veterans-stats'] || {};
                                const lastResult = status['veterans-last-result'];

                                randomStats.processed++;
                                if (stats.success > 0 || (lastResult && lastResult.success)) {
                                    randomStats.success++;
                                    randomLog(`✅ Success! ${veteranData.first} ${veteranData.last}`);
                                    if (lastResult && lastResult.email) {
                                        randomLog(`📧 Email: ${lastResult.email}`);
                                        lastRandomVerifyEmail = lastResult.email;
                                        document.getElementById('random-verify-email').value = lastResult.email;
                                    }
                                } else {
                                    randomStats.failed++;
                                    const errorMsg = lastResult?.error || lastResult?.status || 'Unknown';
                                    randomLog(`❌ Failed: ${errorMsg}`);
                                }
                                updateRandomStats();
                                break;
                            }
                        }

                        if (waitCount >= MAX_WAIT) {
                            randomLog('⚠️ Timeout waiting for result');
                            randomStats.processed++;
                            randomStats.failed++;
                            updateRandomStats();
                            // Stop the main flow
                            chrome.storage.local.set({ 'veterans-is-running': false });
                        }

                        if (!isRandomAutoRunning) break;

                        // Delay before next iteration
                        randomLog('⏳ Next in 3s...');
                        await new Promise(r => setTimeout(r, 3000));

                    } catch (err) {
                        randomStats.processed++;
                        randomStats.failed++;
                        updateRandomStats();
                        randomLog('❌ Error: ' + err.message);
                        await new Promise(r => setTimeout(r, 3000));
                    }
                }

                randomLog('⏹️ Auto loop stopped');
                isRandomAutoRunning = false;
                updateRandomButtonStates();
                // Clean up
                chrome.storage.local.set({
                    'veterans-is-running': false,
                    'veterans-is-random-mode': false
                });
            });
        });
    }

    // Stop Button
    if (randomStopBtn) {
        randomStopBtn.addEventListener('click', () => {
            if (isRandomAutoRunning) {
                randomLog('⏹️ Stopping...');
                isRandomAutoRunning = false;
                updateRandomButtonStates();
            }
        });
    }

    // Initialize button states
    updateRandomButtonStates();
}

// Load saved data into panel
function loadPanelData() {
    chrome.storage.local.get(
        ['chatgpt-account', 'veterans-data-list', 'veterans-saved-email', 'veterans-is-running', 'veterans-range-from', 'veterans-range-to', 'veterans-data-array', 'veterans-stats', 'veterans-current-index'],
        (result) => {
            const startBtn = document.getElementById('veterans-start-btn');
            const stopBtn = document.getElementById('veterans-stop-btn');

            // Load ChatGPT account
            if (result['chatgpt-account']) {
                chatgptAccount = result['chatgpt-account'];
                const accountInfo = document.getElementById('chatgpt-account-info');
                const accountCount = document.getElementById('chatgpt-account-count');
                if (accountInfo && accountCount) {
                    accountCount.textContent = '1';
                    accountInfo.classList.add('show');
                }
                const accountCurrent = document.getElementById('chatgpt-account-current');
                if (accountCurrent) {
                    accountCurrent.value = chatgptAccount.email;
                }
            }

            // Load range values (only if they exist, otherwise leave empty)
            const rangeFromInput = document.getElementById('veterans-range-from');
            const rangeToInput = document.getElementById('veterans-range-to');
            if (rangeFromInput && result['veterans-range-from'] !== undefined && result['veterans-range-from'] !== '') {
                rangeFromInput.value = result['veterans-range-from'];
            } else if (rangeFromInput) {
                rangeFromInput.value = '';
            }
            if (rangeToInput && result['veterans-range-to'] !== undefined && result['veterans-range-to'] !== '') {
                rangeToInput.value = result['veterans-range-to'];
            } else if (rangeToInput) {
                rangeToInput.value = '';
            }

            // Load state
            if (result['veterans-data-array']) {
                dataArray = result['veterans-data-array'];
            }
            if (result['veterans-stats']) {
                stats = result['veterans-stats'];
            }
            if (result['veterans-current-index'] !== undefined) {
                currentDataIndex = result['veterans-current-index'];
            }
            if (result['veterans-is-running'] !== undefined) {
                isRunning = result['veterans-is-running'];
            }

            // Update data count if data exists
            if (result['veterans-data-list']) {
                const dataLines = result['veterans-data-list'].split('\n').filter((line) => line.trim());
                const validData = dataLines.filter((line) => {
                    const parts = line.trim().split('|');
                    return parts.length === 6;
                });

                const dataInfo = document.getElementById('veterans-data-info');
                const dataCount = document.getElementById('veterans-data-count');
                if (dataInfo && dataCount && validData.length > 0) {
                    dataCount.textContent = validData.length;
                    dataInfo.classList.add('show');
                }

                // Update range info
                updateRangeInfo();

                // Enable START button if we have valid data and not running
                if (startBtn && validData.length > 0 && !result['veterans-is-running']) {
                    startBtn.disabled = false;
                } else if (startBtn) {
                    startBtn.disabled = true;
                }
            } else {
                // No data list, disable START button
                if (startBtn && !result['veterans-is-running']) {
                    startBtn.disabled = true;
                }
            }

            // Update email
            if (result['veterans-saved-email']) {
                const emailInput = document.getElementById('veterans-email-input');
                if (emailInput) {
                    emailInput.value = result['veterans-saved-email'];
                }
                currentEmail = result['veterans-saved-email'];
            }

            // Update stop and skip button states
            if (stopBtn) {
                stopBtn.disabled = !result['veterans-is-running'];
            }

            const skipBtn = document.getElementById('veterans-skip-btn');
            if (skipBtn) {
                skipBtn.disabled = result['veterans-is-running'] || false;
                skipBtn.style.display = 'block';
            }

            // Update UI
            updateUIPanel();
        }
    );
}
