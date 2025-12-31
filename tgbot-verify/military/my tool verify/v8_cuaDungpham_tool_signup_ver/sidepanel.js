// Side Panel script for ChatGPT Veterans Auto Verify
// This handles all UI interactions and communicates with content.js via messages

// State variables for UI
let dataArray = []; // Veterans data array
let chatgptAccount = null; // Single ChatGPT account
let stats = { processed: 0, success: 0, failed: 0 };
let currentDataIndex = 0;
let isRunning = false;
let currentEmail = '';

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
        'veterans-status'
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
        statusEl.textContent = message;
        statusEl.className = 'veterans-status-text ' +
            (type === 'success' ? 'success' : type === 'error' ? 'error' : '');
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

                // Parse first valid account (supports 4 or 6 fields)
                // Format 6 fields: email-chatgpt|pass-chatgpt|email-login|pass-email|refresh_token|client_id
                // Format 4 fields: email|password|refresh_token|client_id (email-login = email, pass-email = password)
                let validAccount = null;
                for (const line of lines) {
                    const parts = line.trim().split('|');

                    if (parts.length === 6) {
                        // 6-field format: full format with separate email login
                        validAccount = {
                            email: parts[0].trim(),
                            password: parts[1].trim(),
                            emailLogin: parts[2].trim(),
                            passEmail: parts[3].trim(),
                            refreshToken: parts[4].trim(),
                            clientId: parts[5].trim(),
                            original: line.trim()
                        };
                        console.log('✅ Loaded 6-field account format');
                        break;
                    } else if (parts.length === 4) {
                        // 4-field format: email login = chatgpt email
                        validAccount = {
                            email: parts[0].trim(),
                            password: parts[1].trim(),
                            emailLogin: parts[0].trim(),  // Same as email
                            passEmail: parts[1].trim(),   // Same as password
                            refreshToken: parts[2].trim(),
                            clientId: parts[3].trim(),
                            original: line.trim()
                        };
                        console.log('✅ Loaded 4-field account format (email login = chatgpt email)');
                        break;
                    }
                }

                if (!validAccount) {
                    updateUIPanelStatus('❌ Invalid format! Expected: email|pass|token|clientId (4 fields) or email|pass|emailLogin|passEmail|token|clientId (6 fields)', 'error');
                    chatgptFileInput.value = '';
                    return;
                }

                // Save to storage
                chatgptAccount = validAccount;
                chrome.storage.local.set({
                    'chatgpt-account': validAccount,
                    'chatgpt-account-list': content
                });

                // Show account info
                const accountInfo = document.getElementById('chatgpt-account-info');
                const accountCount = document.getElementById('chatgpt-account-count');
                if (accountInfo && accountCount) {
                    accountCount.textContent = '1';
                    accountInfo.classList.add('show');
                }

                // Update current account display
                const accountCurrent = document.getElementById('chatgpt-account-current');
                if (accountCurrent) {
                    accountCurrent.value = validAccount.email;
                }

                updateUIPanelStatus(`✅ Loaded ChatGPT account: ${validAccount.email}`, 'success');
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

                // Save to storage
                chrome.storage.local.set({ 'veterans-data-list': content });

                // Show data count
                const dataInfo = document.getElementById('veterans-data-info');
                const dataCount = document.getElementById('veterans-data-count');
                if (dataInfo && dataCount) {
                    dataCount.textContent = validData.length;
                    dataInfo.classList.add('show');
                }

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
            // Get both account and data from storage
            chrome.storage.local.get(['chatgpt-account', 'veterans-data-list'], async (result) => {
                // Check ChatGPT account
                if (!result['chatgpt-account']) {
                    updateUIPanelStatus('❌ Please load ChatGPT account first', 'error');
                    return;
                }

                // Check veterans data
                let dataList = result['veterans-data-list'];
                if (!dataList || !dataList.trim()) {
                    updateUIPanelStatus('❌ Please load veterans data first', 'error');
                    return;
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
                    'veterans-stats': { processed: 0, success: 0, failed: 0 }
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
                            // Try to send message
                            chrome.tabs.sendMessage(tabs[0].id, {
                                action: 'startVerification',
                                account: account,
                                data: workingDataArray
                            }, (response) => {
                                if (chrome.runtime.lastError) {
                                    // If message fails, redirect to ChatGPT page (content script might not be loaded)
                                    console.log('Content script not ready, redirecting to ChatGPT...');
                                    updateUIPanelStatus('🌐 Redirecting to ChatGPT page...', 'info');
                                    chrome.tabs.update(tabs[0].id, { url: 'https://chatgpt.com' });
                                }
                            });
                        } else {
                            // Not on ChatGPT page, navigate there
                            updateUIPanelStatus('🌐 Navigating to ChatGPT page...', 'info');
                            chrome.tabs.update(tabs[0].id, { url: 'https://chatgpt.com' });
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
                    let localStats = storageResult['veterans-stats'] || { processed: 0, success: 0, failed: 0 };

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
            updateUIPanelStatus('🍪 Đang xóa cookies của ChatGPT và SheerID...', 'info');

            try {
                // Get all cookies - we'll filter for chatgpt.com and sheerid.com domains
                const allCookies = await chrome.cookies.getAll({});

                // Filter cookies for chatgpt.com, sheerid.com and their subdomains
                const cookiesToDelete = allCookies.filter(cookie => {
                    return cookie.domain.includes('chatgpt.com') ||
                        cookie.domain.includes('sheerid.com');
                });

                if (cookiesToDelete.length === 0) {
                    updateUIPanelStatus('ℹ️ Không có cookies nào để xóa', 'info');
                    return;
                }

                // Delete each cookie
                let deletedCount = 0;
                for (const cookie of cookiesToDelete) {
                    try {
                        // Construct proper URL for cookie removal
                        const protocol = cookie.secure ? 'https' : 'http';
                        // Handle domain format (.chatgpt.com or chatgpt.com)
                        const domain = cookie.domain.startsWith('.') ? cookie.domain.substring(1) : cookie.domain;
                        const url = `${protocol}://${domain}${cookie.path || '/'}`;

                        await chrome.cookies.remove({
                            url: url,
                            name: cookie.name
                        });
                        deletedCount++;
                    } catch (error) {
                        console.error(`Error deleting cookie ${cookie.name}:`, error);
                    }
                }

                updateUIPanelStatus(`✅ Đã xóa ${deletedCount} cookies`, 'success');

                // Wait a bit then reload to chatgpt.com
                setTimeout(() => {
                    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                        if (tabs[0]) {
                            chrome.tabs.update(tabs[0].id, { url: 'https://chatgpt.com' });
                        }
                    });
                }, 1000);

            } catch (error) {
                console.error('Error clearing cookies:', error);
                updateUIPanelStatus('❌ Lỗi khi xóa cookies: ' + error.message, 'error');
            }
        });
    }
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
