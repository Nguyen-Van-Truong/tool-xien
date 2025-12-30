// Side Panel script for ChatGPT Auto Signup
let dataArray = [];
let stats = { processed: 0, success: 0, failed: 0 };
let currentDataIndex = 0;
let isRunning = false;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setupPanelHandlers();
    loadPanelData();
    updateUIPanel();
    
    // Listen for storage changes to update UI
    chrome.storage.onChanged.addListener((changes, areaName) => {
        if (areaName === 'local') {
            if (changes['chatgpt-signup-stats']) {
                stats = changes['chatgpt-signup-stats'].newValue || stats;
                updateUIPanel();
            }
            if (changes['chatgpt-signup-data-array']) {
                dataArray = changes['chatgpt-signup-data-array'].newValue || [];
                updateUIPanel();
            }
            if (changes['chatgpt-signup-is-running']) {
                isRunning = changes['chatgpt-signup-is-running'].newValue || false;
                updateButtonStates();
                if (!isRunning) {
                    chrome.storage.local.get(['chatgpt-signup-status'], (result) => {
                        if (result['chatgpt-signup-status'] && result['chatgpt-signup-status'].message) {
                            updateUIPanelStatus(result['chatgpt-signup-status'].message, result['chatgpt-signup-status'].type || 'info');
                        }
                    });
                }
            }
            if (changes['chatgpt-signup-current-index']) {
                currentDataIndex = changes['chatgpt-signup-current-index'].newValue || 0;
                updateUIPanel();
            }
            if (changes['chatgpt-signup-status']) {
                const statusData = changes['chatgpt-signup-status'].newValue;
                if (statusData && statusData.message) {
                    updateUIPanelStatus(statusData.message, statusData.type || 'info');
                }
            }
        }
    });
    
    // Periodically sync state from storage
    setInterval(() => {
        syncStateFromStorage();
    }, 1000);
});

function syncStateFromStorage() {
    chrome.storage.local.get([
        'chatgpt-signup-data-array',
        'chatgpt-signup-stats',
        'chatgpt-signup-current-index',
        'chatgpt-signup-is-running',
        'chatgpt-signup-status',
        'chatgpt-signup-api-endpoint'
    ], (result) => {
        if (result['chatgpt-signup-data-array']) {
            dataArray = result['chatgpt-signup-data-array'];
        }
        if (result['chatgpt-signup-stats']) {
            stats = result['chatgpt-signup-stats'];
        }
        if (result['chatgpt-signup-current-index'] !== undefined) {
            currentDataIndex = result['chatgpt-signup-current-index'];
        }
        if (result['chatgpt-signup-is-running'] !== undefined) {
            isRunning = result['chatgpt-signup-is-running'];
        }
        if (result['chatgpt-signup-api-endpoint']) {
            const apiInput = document.getElementById('signup-api-input');
            if (apiInput) {
                apiInput.value = result['chatgpt-signup-api-endpoint'];
            }
        }
        if (result['chatgpt-signup-status'] && result['chatgpt-signup-status'].message) {
            updateUIPanelStatus(result['chatgpt-signup-status'].message, result['chatgpt-signup-status'].type || 'info');
        }
        updateUIPanel();
        updateButtonStates();
    });
}

function updateUIPanel() {
    const totalEl = document.getElementById('signup-panel-total');
    const processedEl = document.getElementById('signup-panel-processed');
    const successEl = document.getElementById('signup-panel-success');
    const failedEl = document.getElementById('signup-panel-failed');
    const currentEl = document.getElementById('signup-panel-current');
    
    if (totalEl) totalEl.textContent = dataArray.length || 0;
    if (processedEl) processedEl.textContent = stats.processed || 0;
    if (successEl) successEl.textContent = stats.success || 0;
    if (failedEl) failedEl.textContent = stats.failed || 0;
    if (currentEl) {
        currentEl.value = currentDataIndex < dataArray.length && dataArray.length > 0
            ? dataArray[currentDataIndex].email || '-'
            : '-';
    }
}

function updateUIPanelStatus(message, type = 'info') {
    const statusEl = document.getElementById('signup-panel-status');
    if (statusEl) {
        statusEl.textContent = message;
        statusEl.className = 'signup-status-text ' + 
            (type === 'success' ? 'success' : type === 'error' ? 'error' : '');
    }
}

function updateButtonStates() {
    const startBtn = document.getElementById('signup-start-btn');
    const stopBtn = document.getElementById('signup-stop-btn');
    
    if (startBtn) {
        if (isRunning) {
            startBtn.disabled = true;
        } else {
            const hasData = dataArray && dataArray.length > 0;
            startBtn.disabled = !hasData;
        }
    }
    
    if (stopBtn) {
        stopBtn.disabled = !isRunning;
    }
}

// Setup panel event handlers
function setupPanelHandlers() {
    // Load file button
    const loadBtn = document.getElementById('signup-load-btn');
    const fileInput = document.getElementById('signup-file-input');
    
    if (loadBtn && fileInput) {
        loadBtn.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = (event) => {
                const content = event.target.result;
                
                // Parse and count valid data lines (format: email-chatgpt|pass-chatgpt|email-login|pass-email|refresh_token|client_id)
                const dataLines = content.split('\n').filter((line) => line.trim());
                const validData = dataLines
                    .map((line) => {
                        const parts = line.trim().split('|');
                        if (parts.length >= 6) {
                            return {
                                email: parts[0].trim(),
                                password: parts[1].trim(),
                                emailLogin: parts[2].trim(),
                                passEmail: parts[3].trim(),
                                refreshToken: parts[4].trim(),
                                clientId: parts[5].trim(),
                                original: line.trim()
                            };
                        }
                        return null;
                    })
                    .filter((item) => item !== null);
                
                // Update local dataArray ngay lập tức
                dataArray = validData;
                
                // Save to storage (cả data-list và data-array)
                chrome.storage.local.set({ 
                    'chatgpt-signup-data-list': content,
                    'chatgpt-signup-data-array': validData
                }, () => {
                    // Show data count
                    const dataInfo = document.getElementById('signup-data-info');
                    const dataCount = document.getElementById('signup-data-count');
                    if (dataInfo && dataCount) {
                        dataCount.textContent = validData.length;
                        dataInfo.classList.add('show');
                    }
                    
                    // Enable START button when data is loaded
                    const startBtn = document.getElementById('signup-start-btn');
                    if (startBtn) {
                        if (validData.length > 0 && !isRunning) {
                            startBtn.disabled = false;
                        } else {
                            startBtn.disabled = true;
                        }
                    }
                    
                    // Update UI
                    updateUIPanel();
                    updateButtonStates();
                    
                    updateUIPanelStatus(`✅ Loaded ${validData.length} accounts`, 'success');
                });
                
                // Reset file input
                fileInput.value = '';
            };
            reader.readAsText(file);
        });
    }
    
    // Save file button
    const saveBtn = document.getElementById('signup-save-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            chrome.storage.local.get(['chatgpt-signup-data-list'], (result) => {
                let dataList = result['chatgpt-signup-data-list'];
                
                if (!dataList || !dataList.trim()) {
                    updateUIPanelStatus('❌ No data to save', 'error');
                    return;
                }
                
                const blob = new Blob([dataList], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'accounts.txt';
                a.click();
                URL.revokeObjectURL(url);
                updateUIPanelStatus('✅ File saved successfully', 'success');
            });
        });
    }
    
    // API endpoint input - save on change
    const apiInput = document.getElementById('signup-api-input');
    if (apiInput) {
        apiInput.addEventListener('change', () => {
            chrome.storage.local.set({
                'chatgpt-signup-api-endpoint': apiInput.value
            });
        });
        apiInput.addEventListener('blur', () => {
            chrome.storage.local.set({
                'chatgpt-signup-api-endpoint': apiInput.value
            });
        });
    }
    
    // Start button
    const startBtn = document.getElementById('signup-start-btn');
    if (startBtn) {
        startBtn.addEventListener('click', async () => {
            // Get data from storage
            chrome.storage.local.get(['chatgpt-signup-data-list', 'chatgpt-signup-api-endpoint'], async (result) => {
                let dataList = result['chatgpt-signup-data-list'];
                const apiEndpoint = result['chatgpt-signup-api-endpoint'];
                
                if (!dataList || !dataList.trim()) {
                    updateUIPanelStatus('❌ Please load data first', 'error');
                    return;
                }
                
                // Không cần kiểm tra API endpoint nữa vì sử dụng dongvanfb.net API
                
                // Parse data
                // Format: email-chatgpt|pass-chatgpt|email-login|pass-email|refresh_token|client_id
                const dataLines = dataList.split('\n').filter((line) => line.trim());
                const parsedDataArray = dataLines
                    .map((line) => {
                        const parts = line.trim().split('|');
                        if (parts.length < 6) {
                            return null;
                        }
                        return {
                            email: parts[0].trim(),           // email-chatgpt
                            password: parts[1].trim(),        // pass-chatgpt
                            emailLogin: parts[2].trim(),      // email-login
                            passEmail: parts[3].trim(),       // pass-email
                            refreshToken: parts[4].trim(),    // refresh_token
                            clientId: parts[5].trim(),        // client_id
                            original: line.trim()
                        };
                    })
                    .filter((item) => item !== null);
                
                if (parsedDataArray.length === 0) {
                    updateUIPanelStatus('❌ No valid data found', 'error');
                    return;
                }
                
                // Update UI
                updateUIPanel();
                startBtn.disabled = true;
                const stopBtn = document.getElementById('signup-stop-btn');
                if (stopBtn) stopBtn.disabled = false;
                
                // Start signup - save data to storage and send message
                updateUIPanelStatus('🚀 Starting signup...', 'info');
                
                // Save data to storage first
                chrome.storage.local.set({
                    'chatgpt-signup-data-array': parsedDataArray,
                    'chatgpt-signup-data-list': dataList,
                    'chatgpt-signup-current-index': 0,
                    'chatgpt-signup-is-running': true,
                    'chatgpt-signup-stats': { processed: 0, success: 0, failed: 0 }
                }, () => {
                    console.log('✅ Data saved to storage');
                    
                    // Send message to content script to start signup
                    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                        if (!tabs[0] || !tabs[0].id) {
                            updateUIPanelStatus('❌ Không tìm thấy tab', 'error');
                            startBtn.disabled = false;
                            if (stopBtn) stopBtn.disabled = true;
                            return;
                        }
                        
                        const currentUrl = tabs[0].url || '';
                        console.log('📍 Current tab URL:', currentUrl);
                        
                        // Kiểm tra xem có phải trang ChatGPT không
                        const isChatGPTPage = currentUrl.includes('chatgpt.com');
                        
                        if (isChatGPTPage) {
                            // Đang ở trang ChatGPT, gửi message
                            chrome.tabs.sendMessage(tabs[0].id, {
                                action: 'startSignup',
                                data: dataList,
                                apiEndpoint: apiEndpoint
                            }, (response) => {
                                if (chrome.runtime.lastError) {
                                    console.error('Error sending message:', chrome.runtime.lastError);
                                    // Content script có thể chưa load, reload trang
                                    updateUIPanelStatus('🔄 Reloading page to load script...', 'info');
                                    chrome.tabs.reload(tabs[0].id, () => {
                                        // Đợi trang reload rồi thử lại
                                        setTimeout(() => {
                                            chrome.tabs.sendMessage(tabs[0].id, {
                                                action: 'startSignup',
                                                data: dataList,
                                                apiEndpoint: apiEndpoint
                                            }, (retryResponse) => {
                                                if (chrome.runtime.lastError) {
                                                    console.error('Error after reload:', chrome.runtime.lastError);
                                                    updateUIPanelStatus('⚠️ Vui lòng reload trang ChatGPT thủ công', 'error');
                                                    startBtn.disabled = false;
                                                    if (stopBtn) stopBtn.disabled = true;
                                                }
                                            });
                                        }, 4000);
                                    });
                                }
                            });
                        } else {
                            // Không phải trang ChatGPT, redirect
                            updateUIPanelStatus('🌐 Navigating to ChatGPT...', 'info');
                            chrome.tabs.update(tabs[0].id, { url: 'https://chatgpt.com' }, () => {
                                // Đợi trang load rồi gửi message
                                setTimeout(() => {
                                    chrome.tabs.sendMessage(tabs[0].id, {
                                        action: 'startSignup',
                                        data: dataList,
                                        apiEndpoint: apiEndpoint
                                    }, (response) => {
                                        if (chrome.runtime.lastError) {
                                            console.error('Error sending message after redirect:', chrome.runtime.lastError);
                                            updateUIPanelStatus('⚠️ Vui lòng reload trang ChatGPT', 'error');
                                            startBtn.disabled = false;
                                            if (stopBtn) stopBtn.disabled = true;
                                        }
                                    });
                                }, 3000);
                            });
                        }
                    });
                });
            });
        });
    }
    
    // Stop button
    const stopBtn = document.getElementById('signup-stop-btn');
    if (stopBtn) {
        stopBtn.addEventListener('click', async () => {
            updateUIPanelStatus('⏹️ Stopping signup...', 'info');
            
            // Save stopped state to storage
            chrome.storage.local.set({ 'chatgpt-signup-is-running': false });
            
            // Send message to content script to stop signup
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                if (tabs[0] && tabs[0].url && tabs[0].url.includes('chatgpt.com')) {
                    chrome.tabs.sendMessage(tabs[0].id, {
                        action: 'stopSignup'
                    }, (response) => {
                        if (chrome.runtime.lastError) {
                            console.error('Error sending message:', chrome.runtime.lastError);
                        }
                    });
                }
            });
            
            // Update UI immediately
            updateButtonStates();
            stopBtn.disabled = true;
            const startBtn = document.getElementById('signup-start-btn');
            if (startBtn) {
                const hasData = dataArray && dataArray.length > 0;
                startBtn.disabled = !hasData;
            }
            
            updateUIPanelStatus('✅ Signup stopped', 'success');
        });
    }
}

// Load saved data into panel
function loadPanelData() {
    chrome.storage.local.get(
        ['chatgpt-signup-data-list', 'chatgpt-signup-is-running', 'chatgpt-signup-data-array', 'chatgpt-signup-stats', 'chatgpt-signup-current-index', 'chatgpt-signup-api-endpoint'],
        (result) => {
            const startBtn = document.getElementById('signup-start-btn');
            const stopBtn = document.getElementById('signup-stop-btn');
            
            // Load state
            if (result['chatgpt-signup-data-array']) {
                dataArray = result['chatgpt-signup-data-array'];
            }
            if (result['chatgpt-signup-stats']) {
                stats = result['chatgpt-signup-stats'];
            }
            if (result['chatgpt-signup-current-index'] !== undefined) {
                currentDataIndex = result['chatgpt-signup-current-index'];
            }
            if (result['chatgpt-signup-is-running'] !== undefined) {
                isRunning = result['chatgpt-signup-is-running'];
            }
            
            // Load API endpoint
            if (result['chatgpt-signup-api-endpoint']) {
                const apiInput = document.getElementById('signup-api-input');
                if (apiInput) {
                    apiInput.value = result['chatgpt-signup-api-endpoint'];
                }
            }
            
            // Update data count if data exists
            if (result['chatgpt-signup-data-list']) {
                const dataLines = result['chatgpt-signup-data-list'].split('\n').filter((line) => line.trim());
                const validData = dataLines.filter((line) => {
                    const parts = line.trim().split('|');
                    return parts.length >= 6; // Phải có ít nhất 6 phần
                });
                
                const dataInfo = document.getElementById('signup-data-info');
                const dataCount = document.getElementById('signup-data-count');
                if (dataInfo && dataCount && validData.length > 0) {
                    dataCount.textContent = validData.length;
                    dataInfo.classList.add('show');
                }
                
                // Enable START button if we have valid data and not running
                if (startBtn && validData.length > 0 && !result['chatgpt-signup-is-running']) {
                    startBtn.disabled = false;
                } else if (startBtn) {
                    startBtn.disabled = true;
                }
            } else {
                // No data list, disable START button
                if (startBtn && !result['chatgpt-signup-is-running']) {
                    startBtn.disabled = true;
                }
            }
            
            // Update stop button state
            if (stopBtn) {
                stopBtn.disabled = !result['chatgpt-signup-is-running'];
            }
            
            // Update UI
            updateUIPanel();
        }
    );
}

