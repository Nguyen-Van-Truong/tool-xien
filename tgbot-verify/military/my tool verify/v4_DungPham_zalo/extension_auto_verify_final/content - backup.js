// Content script for automation
let isRunning = false;
let currentDataIndex = 0;
let dataArray = [];
let currentEmail = '';
let mailRetryCount = 0;
const MAX_MAIL_RETRIES = 10;
let instanceId = null; // Unique ID for this browser instance
let stats = {
    processed: 0,
    success: 0,
    failed: 0
};

// Generate unique instance ID for this browser tab
function getInstanceId() {
    if (!instanceId) {
        // Use tab ID + timestamp as unique identifier
        instanceId = `instance_${Date.now()}_${Math.random()
            .toString(36)
            .substr(2, 9)}`;
        console.log('🆔 Instance ID:', instanceId);
    }
    return instanceId;
}

// Auto-start when page loads if we have saved data
(function autoResumeVerification() {
    console.log('🔍 Checking if we need to auto-resume verification...');
    console.log('📍 Current URL:', window.location.href);

    // Listen for storage changes to sync data between instances
    chrome.storage.onChanged.addListener((changes, areaName) => {
        if (areaName === 'local') {
            if (changes['veterans-data-array']) {
                // Another instance updated the data, sync it
                console.log('🔄 Data updated by another instance, syncing...');
                const newDataArray = changes['veterans-data-array'].newValue;
                if (newDataArray && Array.isArray(newDataArray)) {
                    dataArray = newDataArray;
                    // Adjust current index if needed
                    if (
                        currentDataIndex >= dataArray.length &&
                        dataArray.length > 0
                    ) {
                        currentDataIndex = dataArray.length - 1;
                    }
                    console.log(
                        '✅ Data synced, new length:',
                        dataArray.length
                    );
                }
            }
            if (changes['veterans-data-list']) {
                // Data list updated, could notify popup if needed
                console.log('🔄 Data list updated in storage');
            }
        }
    });

    // Check if we have data from previous session
    chrome.storage.local.get(
        [
            'veterans-data-array',
            'veterans-current-index',
            'veterans-is-running',
            'veterans-stats'
        ],
        (result) => {
            console.log('📦 Storage data:', result);

            if (
                result['veterans-is-running'] &&
                result['veterans-data-array']
            ) {
                dataArray = result['veterans-data-array'];
                currentDataIndex = result['veterans-current-index'] || 0;
                // Restore stats if available
                if (result['veterans-stats']) {
                    stats = result['veterans-stats'];
                    console.log('📊 Restored stats:', stats);
                }
                isRunning = true;

                console.log('🔄 Auto-resuming verification...');
                console.log(
                    '📊 Data array length:',
                    dataArray.length,
                    'Current index:',
                    currentDataIndex
                );

                // Wait a bit for page to load, then continue
                setTimeout(() => {
                    if (
                        window.location.href.includes(
                            'services.sheerid.com/verify'
                        )
                    ) {
                        console.log('📍 On SheerID page, checking form...');
                        checkAndFillForm();
                    } else if (
                        window.location.href.includes(
                            'chatgpt.com/veterans-claim'
                        )
                    ) {
                        console.log(
                            '📍 On ChatGPT page, starting verification loop...'
                        );
                        startVerificationLoop();
                    } else {
                        console.log(
                            '📍 Unknown page, navigating to ChatGPT...'
                        );
                        window.location.href =
                            'https://chatgpt.com/veterans-claim';
                        setTimeout(() => {
                            startVerificationLoop();
                        }, 3000);
                    }
                }, 2000);
            } else {
                console.log(
                    '⚠️ No saved data found, waiting for manual start...'
                );
            }
        }
    );
})();

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'ping') {
        sendResponse({ success: true });
    } else if (message.action === 'startVerification') {
        console.log('🚀 Received startVerification message');
        const instanceId = getInstanceId();
        dataArray = message.data;
        currentEmail = ''; // Will be auto-generated when needed
        mailRetryCount = 0;
        stats = { processed: 0, success: 0, failed: 0 };
        isRunning = true;

        // Update panel UI
        const startBtn = document.getElementById('veterans-start-btn');
        const stopBtn = document.getElementById('veterans-stop-btn');
        const skipBtn = document.getElementById('veterans-skip-btn');
        // Nút START và STOP luôn hiển thị, chỉ disable/enable
        if (startBtn) startBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = false;
        // Disable và hiển thị nút SKIP khi tool RUNNING
        if (skipBtn) {
            skipBtn.style.display = 'block';
            skipBtn.disabled = true;
        }

        console.log(
            '💾 Saving data to storage, array length:',
            dataArray.length
        );

        // Rebuild data list string for storage
        const dataListString = dataArray
            .map((data) => data.original)
            .join('\n');

        // Use lock mechanism to prevent race condition and assign starting index
        chrome.storage.local.get(
            ['veterans-data-lock', 'veterans-active-instances'],
            (lockResult) => {
                if (lockResult['veterans-data-lock']) {
                    // Wait and retry if locked
                    setTimeout(() => {
                        chrome.runtime.sendMessage({
                            action: 'startVerification',
                            data: dataArray
                        });
                    }, 200);
                    return;
                }

                // Calculate starting index based on active instances
                const activeInstances =
                    lockResult['veterans-active-instances'] || {};
                const instanceCount = Object.keys(activeInstances).length;

                // Each instance starts from a different position to avoid overlap
                // Instance 0: index 0, Instance 1: index 1, etc.
                // Then each instance processes every Nth item (where N = number of instances)
                currentDataIndex = instanceCount;

                // Register this instance
                activeInstances[instanceId] = {
                    startIndex: currentDataIndex,
                    startTime: Date.now(),
                    totalInstances: instanceCount + 1
                };

                console.log(
                    `🆔 Instance ${
                        instanceCount + 1
                    } starting at index ${currentDataIndex}`
                );

                // Set lock
                chrome.storage.local.set(
                    {
                        'veterans-data-lock': true,
                        'veterans-active-instances': activeInstances
                    },
                    () => {
                        // Save state to storage
                        chrome.storage.local.set(
                            {
                                'veterans-data-array': dataArray,
                                'veterans-data-list': dataListString,
                                'veterans-current-index': currentDataIndex,
                                'veterans-is-running': true,
                                'veterans-stats': stats
                            },
                            () => {
                                console.log('✅ Data saved to storage');
                                // Release lock after 500ms
                                setTimeout(() => {
                                    chrome.storage.local.remove(
                                        'veterans-data-lock'
                                    );
                                }, 500);

                                startVerificationLoop();
                                sendResponse({ success: true });
                            }
                        );
                    }
                );
            }
        );
    } else if (message.action === 'stopVerification') {
        console.log('⏹️ Stop verification requested');
        isRunning = false;
        chrome.storage.local.set({ 'veterans-is-running': false });

        // Update UI panel
        updateUIOnStop();

        // Unregister this instance
        const instanceId = getInstanceId();
        chrome.storage.local.get(['veterans-active-instances'], (result) => {
            const activeInstances = result['veterans-active-instances'] || {};
            delete activeInstances[instanceId];
            chrome.storage.local.set({
                'veterans-active-instances': activeInstances
            });
        });

        // Update panel UI
        const startBtn = document.getElementById('veterans-start-btn');
        const stopBtn = document.getElementById('veterans-stop-btn');
        // Nút START và STOP luôn hiển thị, chỉ disable/enable
        if (startBtn) {
            const hasData = dataArray && dataArray.length > 0;
            startBtn.disabled = !hasData;
        }
        if (stopBtn) stopBtn.disabled = true;

        sendStatus('⏹️ Verification stopped by user', 'info');
        sendResponse({ success: true });
    }
    return true;
});

async function startVerificationLoop() {
    // Check if stopped - FORCE STOP check
    if (!isRunning) {
        console.log('⏹️ Tool stopped, exiting loop');
        return;
    }

    if (currentDataIndex >= dataArray.length) {
        isRunning = false;
        chrome.storage.local.set({ 'veterans-is-running': false });
        
        // Update UI panel
        const startBtn = document.getElementById('veterans-start-btn');
        const stopBtn = document.getElementById('veterans-stop-btn');
        // Nút START và STOP luôn hiển thị, chỉ disable/enable
        if (startBtn) {
            const hasData = dataArray && dataArray.length > 0;
            startBtn.disabled = !hasData;
        }
        if (stopBtn) stopBtn.disabled = true;
        
        sendStatus('✅ All data processed', 'success');
        updateUIPanel();
        return;
    }

    const currentData = dataArray[currentDataIndex];
    mailRetryCount = 0; // Reset mail retry count for new data
    currentEmail = ''; // Reset email for new data (will be auto-generated)
    sendStatus(
        `🔄 Processing ${currentDataIndex + 1}/${dataArray.length}: ${
            currentData.first
        } ${currentData.last}`,
        'info'
    );
    updateStats();

    // Save current state
    chrome.storage.local.set({
        'veterans-current-index': currentDataIndex,
        'veterans-is-running': true
    });

    try {
        // Check current URL
        const currentUrl = window.location.href;
        console.log('📍 Current URL:', currentUrl);
        
        // Check for sourcesUnavailable error in URL
        if (currentUrl.includes('sourcesUnavailable') || currentUrl.includes('Error sourcesUnavailable')) {
            console.log('🚫 sourcesUnavailable error detected in URL, stopping tool...');
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            sendStatus(
                '🚫 VPN Error: sourcesUnavailable detected. Please change VPN and restart.',
                'error'
            );
            
            // Notify popup to show VPN warning
            chrome.runtime
                .sendMessage({
                    action: 'vpnError',
                    message:
                        "Error sourcesUnavailable detected. Please change VPN and restart the tool."
                })
                .catch(() => {});
            
            return;
        }

        if (currentUrl.includes('chatgpt.com/veterans-claim')) {
            // Step 1: Click verify button
            console.log('🔍 On ChatGPT page, clicking verify button...');
            console.log(
                `📊 Current data index: ${currentDataIndex + 1}/${
                    dataArray.length
                }`
            );
            if (currentDataIndex < dataArray.length) {
                const currentData = dataArray[currentDataIndex];
                console.log(
                    `📋 Processing: ${currentData.first} ${currentData.last}`
                );
            }
            await clickVerifyButton();
        } else if (currentUrl.includes('services.sheerid.com/verify')) {
            // Step 2: Check if we're on verification page
            console.log('🔍 On SheerID page, checking form...');
            // Auto-generate email if not already set
            if (!currentEmail) {
                console.log('📧 Generating new email...');
                await generateNewEmail();
            }
            console.log('📝 Starting to fill form...');
            await checkAndFillForm();
        } else {
            // Navigate to start page
            console.log('🌐 Navigating to ChatGPT page...');
            window.location.href = 'https://chatgpt.com/veterans-claim';
            await delay(5000); // Wait longer for page to load
            // The auto-resume function will handle continuing
            // But also try to continue directly
            await startVerificationLoop();
            return;
        }
    } catch (error) {
        // Check if stopped before processing error
        if (!isRunning) {
            console.log('⏹️ Tool stopped during error handling, exiting');
            return;
        }
        
        console.error('❌ Error in verification loop:', error);
        sendStatus('❌ Error: ' + error.message, 'error');
        // Remove processed data and move to next
        removeProcessedData();
        stats.processed++;
        stats.failed++;
        updateStats();
        
        // Only continue if still running
        if (isRunning) {
            chrome.storage.local.set({
                'veterans-current-index': currentDataIndex,
                'veterans-is-running': true
            });
            await delay(2000);
            await startVerificationLoop();
        }
    }
}

async function generateNewEmail() {
    // FORCE STOP check at the start
    if (!isRunning) {
        console.log('⏹️ Tool stopped, exiting generateNewEmail');
        return;
    }
    
    try {
        sendStatus('📧 Generating new email...', 'info');

        // Get random domains
        const domainsResponse = await fetch(
            'https://tinyhost.shop/api/random-domains/?limit=10'
        );
        if (!domainsResponse.ok) {
            throw new Error('Failed to fetch domains');
        }

        const domainsData = await domainsResponse.json();
        const domains = domainsData.domains || [];

        if (domains.length === 0) {
            throw new Error('No domains available');
        }

        // Filter out blocked domains
        const blockedDomains = ['tempmail.com', 'guerrillamail.com'];
        const filteredDomains = domains.filter(
            (domain) =>
                !blockedDomains.some((blocked) => domain.endsWith(blocked))
        );

        if (filteredDomains.length === 0) {
            throw new Error('No valid domains available');
        }

        // Pick random domain
        const domain =
            filteredDomains[Math.floor(Math.random() * filteredDomains.length)];

        // Generate random username
        const username = generateRandomString(16);
        const email = `${username}@${domain}`;

        // Set current email
        currentEmail = email;

        // Save to localStorage
        localStorage.setItem('veterans-saved-email', email);
        localStorage.setItem('veterans-email-domain', domain);
        localStorage.setItem('veterans-email-username', username);

        // Notify popup to update email display
        chrome.runtime
            .sendMessage({
                action: 'updateEmail',
                email: email
            })
            .catch(() => {
                // Ignore if popup is closed
            });

        // Update UI panel email
        const emailEl = document.getElementById('veterans-panel-email');
        if (emailEl) emailEl.textContent = email;
        const emailInput = document.getElementById('veterans-email-input');
        if (emailInput) emailInput.value = email;

        sendStatus('✅ Email generated: ' + email, 'success');
    } catch (error) {
        console.error('Error generating email:', error);
        sendStatus('❌ Failed to generate email: ' + error.message, 'error');
        throw error;
    }
}

function generateRandomString(length = 12) {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

async function clickVerifyButton() {
    // FORCE STOP check at the start
    if (!isRunning) {
        console.log('⏹️ Tool stopped, exiting clickVerifyButton');
        return;
    }
    
    sendStatus('🔍 Looking for verify button...', 'info');
    console.log('🔍 Searching for verify button...');

    // Wait for page to fully load first
    await delay(2000);
    
    // Check again after delay
    if (!isRunning) {
        console.log('⏹️ Tool stopped during delay, exiting clickVerifyButton');
        return;
    }
    
    console.log('⏳ Waiting for page to load...');

    // Wait for button with specific selector and text
    let button = null;
    let attempts = 0;
    const maxAttempts = 10;

    while (attempts < maxAttempts && !button) {
        attempts++;
        console.log(
            `🔍 Attempt ${attempts}/${maxAttempts}: Looking for button...`
        );

        // Try to find button with exact structure
        const buttons = document.querySelectorAll(
            'button.btn-primary, button[class*="btn-primary"]'
        );
        console.log(
            `📊 Found ${buttons.length} button(s) with btn-primary class`
        );

        for (let btn of buttons) {
            const buttonText = btn.innerText || btn.textContent || '';
            console.log(`🔍 Checking button text: "${buttonText}"`);

            // Check if button contains the exact text
            if (
                buttonText.includes('Xác minh tư cách đủ điều kiện') ||
                buttonText.includes('Xác minh') ||
                buttonText.includes('Verify')
            ) {
                // Check if button is visible and enabled
                const isVisible = btn.offsetParent !== null;
                const isEnabled = !btn.disabled;

                console.log(
                    `✅ Found matching button! Visible: ${isVisible}, Enabled: ${isEnabled}`
                );

                if (isVisible && isEnabled) {
                    button = btn;
                    break;
                }
            }
        }

        if (!button) {
            console.log(
                `⏳ Button not ready yet, waiting... (${attempts}/${maxAttempts})`
            );
            await delay(1000);
        }
    }

    if (!button) {
        console.error('❌ Verify button not found after all attempts!');
        // Try one more time with broader search
        const allButtons = Array.from(document.querySelectorAll('button'));
        button = allButtons.find((btn) => {
            const text = btn.innerText || btn.textContent || '';
            return text.includes('Xác minh') || text.includes('Verify');
        });
    }

    if (!button) {
        console.error('❌ Verify button not found!');
        throw new Error('Verify button not found');
    }

    // Double check button is ready
    const buttonText = button.innerText || button.textContent || '';
    console.log('✅ Button found! Text:', buttonText);
    console.log('✅ Button visible:', button.offsetParent !== null);
    console.log('✅ Button enabled:', !button.disabled);

    // Wait a bit more to ensure button is fully interactive
    await delay(1000);
    
    // Check again after delay
    if (!isRunning) {
        console.log('⏹️ Tool stopped during delay, exiting clickVerifyButton');
        return;
    }

    if (
        buttonText.includes('Xác minh') ||
        buttonText.includes('Verify') ||
        buttonText.includes('verify')
    ) {
        console.log('✅ Clicking verify button...');
        button.click();
        sendStatus('✅ Clicked verify button', 'success');
        await delay(3000);

        // Wait for redirect to SheerID
        console.log('⏳ Waiting for redirect to SheerID...');
        
        // Check if stopped before waiting
        if (!isRunning) {
            console.log('⏹️ Tool stopped before redirect, exiting');
            return;
        }
        
        const urlChanged = await waitForUrlChange('services.sheerid.com', 15000);
        
        // Check if stopped after waiting
        if (!isRunning || !urlChanged) {
            console.log('⏹️ Tool stopped or URL did not change, exiting');
            return;
        }
        
        await delay(3000); // Wait longer for page to load
        
        // Check again after delay
        if (!isRunning) {
            console.log('⏹️ Tool stopped after delay, exiting');
            return;
        }
        
        // Auto-generate email when arriving at SheerID page
        await generateNewEmail();
        
        // Check again after generating email
        if (!isRunning) {
            console.log('⏹️ Tool stopped after generating email, exiting');
            return;
        }
        
        await delay(1000); // Wait after generating email
        
        // Check again before filling form
        if (!isRunning) {
            console.log('⏹️ Tool stopped before filling form, exiting');
            return;
        }
        
        await checkAndFillForm();
    } else {
        console.error('❌ Button text does not match:', buttonText);
        throw new Error(
            'Verify button not found with correct text: ' + buttonText
        );
    }
}

async function checkAndFillForm() {
    // FORCE STOP check at the start
    if (!isRunning) {
        console.log('⏹️ Tool stopped, exiting checkAndFillForm');
        return;
    }
    
    console.log('🔍 checkAndFillForm() called');
    sendStatus('🔍 Checking verification page...', 'info');

    // Wait longer for page to fully load
    await delay(3000);
    
    // Check again after delay
    if (!isRunning) {
        console.log('⏹️ Tool stopped during delay, exiting checkAndFillForm');
        return;
    }
    
    console.log('✅ Page should be loaded now');
    
    // Check URL for sourcesUnavailable error
    const currentUrl = window.location.href;
    if (currentUrl.includes('sourcesUnavailable') || currentUrl.includes('Error sourcesUnavailable')) {
        console.log('🚫 sourcesUnavailable error detected in URL, stopping tool...');
        isRunning = false;
        chrome.storage.local.set({ 'veterans-is-running': false });
        updateUIOnStop();
        sendStatus(
            '🚫 VPN Error: sourcesUnavailable detected. Please change VPN and restart.',
            'error'
        );
        
        // Notify popup to show VPN warning
        chrome.runtime
            .sendMessage({
                action: 'vpnError',
                message:
                    "Error sourcesUnavailable detected. Please change VPN and restart the tool."
            })
            .catch(() => {});
        
        return;
    }

    try {
        // Check for error div structure first
        const errorDiv = document.querySelector('.sid-error-msg');
        if (errorDiv) {
            const errorText = errorDiv.innerText || errorDiv.textContent || '';
            console.log('🔍 Error div text:', errorText);

            // Check for VPN/blocking error - stop tool immediately
            if (
                errorText.includes(
                    'We are unable to verify you at this time'
                ) ||
                errorText.includes('unable to verify you') ||
                errorText.includes('contact SheerID support') ||
                errorText.includes(
                    "It looks like we're having difficulty verifying you"
                ) ||
                errorText.includes('having difficulty verifying') ||
                errorText.includes('sourcesUnavailable') ||
                errorText.includes('Error sourcesUnavailable') ||
                errorText.toLowerCase().includes('sources unavailable')
            ) {
                console.log('🚫 VPN/Blocking error detected, stopping tool...');
                isRunning = false;
                chrome.storage.local.set({ 'veterans-is-running': false });
                updateUIOnStop();
                sendStatus(
                    '🚫 VPN Error: Unable to verify. Please change VPN and restart.',
                    'error'
                );

                // Notify popup to show VPN warning
                chrome.runtime
                    .sendMessage({
                        action: 'vpnError',
                        message:
                            "It looks like we're having difficulty verifying you. Please change VPN and restart the tool."
                    })
                    .catch(() => {});

                return;
            }

            if (
                errorText.includes('Not approved') ||
                errorText.includes('Verification Limit Exceeded') ||
                errorText.includes('verification limit exceeded') ||
                errorText.includes('limit exceeded')
            ) {
                const errorType = errorText.includes('Not approved')
                    ? 'Not approved'
                    : 'Verification Limit Exceeded';
                console.log(`❌ ${errorType} detected, moving to next data...`);
                sendStatus(`❌ Verification failed: ${errorType}`, 'error');

                // Check if there's more data
                if (currentDataIndex + 1 >= dataArray.length) {
                    console.log('❌ No more data to process');
                    isRunning = false;
                    chrome.storage.local.set({ 'veterans-is-running': false });
                    updateUIOnStop();
                    sendStatus('❌ All data failed, no more to try', 'error');
                    return;
                }

                // Mark as failed and move to next
                // Remove processed data first
                removeProcessedData();
                stats.processed++;
                stats.failed++;
                updateStats();

                // Save updated state (index stays same since we removed one)
                chrome.storage.local.set({
                    'veterans-current-index': currentDataIndex,
                    'veterans-is-running': true
                });

                console.log(
                    `🔄 Moving to next data: ${currentDataIndex + 1}/${
                        dataArray.length
                    }`
                );
                sendStatus(
                    `🔄 Trying next data: ${currentDataIndex + 1}/${
                        dataArray.length
                    }`,
                    'info'
                );

                // Go back to start page and continue
                await delay(2000);
                
                // Check if stopped before navigating
                if (!isRunning) {
                    console.log('⏹️ Tool stopped, exiting');
                    return;
                }
                
                console.log('🌐 Navigating back to ChatGPT page...');
                window.location.href = 'https://chatgpt.com/veterans-claim';
                await delay(5000); // Wait longer for page to fully load
                
                // Check again after navigation
                if (!isRunning) {
                    console.log('⏹️ Tool stopped after navigation, exiting');
                    return;
                }
                
                console.log('✅ Page should be loaded, continuing...');

                // Continue with next data
                await startVerificationLoop();
                return;
            }
        }

        // Check if we see "Unlock this Military-Only Offer" - try multiple times
        let heading = null;
        let headingText = '';

        for (let i = 0; i < 5; i++) {
            try {
                heading = await waitForElement('h1', 5000);
                if (heading) {
                    headingText =
                        heading.innerText || heading.textContent || '';
                    if (headingText) break;
                }
            } catch (e) {
                console.log('Waiting for heading, attempt', i + 1);
                await delay(1000);
            }
        }

        // If still no heading, check body text
        if (!heading || !headingText) {
            const bodyText =
                document.body.innerText || document.body.textContent || '';

            // Check for VPN/blocking error in body text - stop tool immediately
            if (
                bodyText.includes('We are unable to verify you at this time') ||
                bodyText.includes('unable to verify you') ||
                bodyText.includes('contact SheerID support') ||
                bodyText.includes(
                    "It looks like we're having difficulty verifying you"
                ) ||
                bodyText.includes('having difficulty verifying') ||
                bodyText.includes('sourcesUnavailable') ||
                bodyText.includes('Error sourcesUnavailable') ||
                bodyText.toLowerCase().includes('sources unavailable')
            ) {
                console.log(
                    '🚫 VPN/Blocking error detected in body text, stopping tool...'
                );
                isRunning = false;
                chrome.storage.local.set({ 'veterans-is-running': false });
                updateUIOnStop();
                sendStatus(
                    '🚫 VPN Error: Unable to verify. Please change VPN and restart.',
                    'error'
                );

                // Notify popup to show VPN warning
                chrome.runtime
                    .sendMessage({
                        action: 'vpnError',
                        message:
                            "It looks like we're having difficulty verifying you. Please change VPN and restart the tool."
                    })
                    .catch(() => {});

                return;
            }

            // Check for error messages in body text
            if (
                bodyText.includes('Not approved') ||
                bodyText.includes('Verification Limit Exceeded') ||
                bodyText.includes('verification limit exceeded') ||
                bodyText.includes('limit exceeded')
            ) {
                const errorType = bodyText.includes('Not approved')
                    ? 'Not approved'
                    : 'Verification Limit Exceeded';
                console.log(
                    `❌ ${errorType} detected in body text, moving to next data...`
                );
                sendStatus(`❌ Verification failed: ${errorType}`, 'error');

                // Check if there's more data
                if (currentDataIndex + 1 >= dataArray.length) {
                    console.log('❌ No more data to process');
                    isRunning = false;
                    chrome.storage.local.set({ 'veterans-is-running': false });
                    updateUIOnStop();
                    sendStatus('❌ All data failed, no more to try', 'error');
                    return;
                }

                // Mark as failed and move to next
                // Remove processed data first
                removeProcessedData();
                stats.processed++;
                stats.failed++;
                updateStats();

                // Save updated state (index stays same since we removed one)
                chrome.storage.local.set({
                    'veterans-current-index': currentDataIndex,
                    'veterans-is-running': true
                });

                console.log(
                    `🔄 Moving to next data: ${currentDataIndex + 1}/${
                        dataArray.length
                    }`
                );
                sendStatus(
                    `🔄 Trying next data: ${currentDataIndex + 1}/${
                        dataArray.length
                    }`,
                    'info'
                );

                // Go back to start page and continue
                await delay(2000);
                
                // Check if stopped before navigating
                if (!isRunning) {
                    console.log('⏹️ Tool stopped, exiting');
                    return;
                }
                
                window.location.href = 'https://chatgpt.com/veterans-claim';
                await delay(4000);
                
                // Check again after navigation
                if (!isRunning) {
                    console.log('⏹️ Tool stopped after navigation, exiting');
                    return;
                }

                // Continue with next data
                await startVerificationLoop();
                return;
            }

            if (
                bodyText.includes("You've been verified") ||
                bodyText.includes('verified')
            ) {
                sendStatus('✅ Verification successful!', 'success');
                console.log(
                    '✅ Verification successful, removing processed data...'
                );
                // Remove processed data first
                removeProcessedData();
                stats.processed++;
                stats.success++;
                updateStats();
                // FORCE STOP - ngừng toàn bộ hoạt động tool
                isRunning = false;
                chrome.storage.local.set({ 'veterans-is-running': false });
                updateUIOnStop();
                console.log('✅ Data removed and tool stopped completely');
                // Không tiếp tục vòng lặp, dừng hoàn toàn
                return;
            }
            if (bodyText.includes('Check your email')) {
                sendStatus(
                    '📧 Email check page detected, reading mail...',
                    'info'
                );
                await readMailAndVerify();
                return;
            }
            // Try to find form directly
            const formExists = document.querySelector(
                '#sid-military-status + button'
            );
            if (formExists) {
                sendStatus(
                    '✅ Found verification form directly, filling...',
                    'success'
                );
                if (!currentEmail) {
                    await generateNewEmail();
                }
                
                // Check if stopped after generating email
                if (!isRunning) {
                    console.log('⏹️ Tool stopped after generating email, exiting');
                    return;
                }
                
                await fillForm();
                return;
            }
            throw new Error('Page heading not found and form not detected');
        }

        if (headingText.includes('Unlock this Military-Only Offer')) {
            console.log('✅ Found "Unlock this Military-Only Offer" heading');
            // Ensure email is generated before filling form
            if (!currentEmail) {
                console.log('📧 No email yet, generating...');
                await generateNewEmail();
            } else {
                console.log('📧 Using existing email:', currentEmail);
            }
            sendStatus('✅ Found verification form, filling...', 'success');
            await delay(1000); // Extra delay before filling
            
            // Check if stopped before filling
            if (!isRunning) {
                console.log('⏹️ Tool stopped before filling form, exiting');
                return;
            }
            
            console.log('📝 Starting fillForm()...');
            await fillForm();
        } else if (headingText.includes('Check your email')) {
            sendStatus('📧 Email check page detected, reading mail...', 'info');
            await readMailAndVerify();
        } else if (
            headingText.includes('We are unable to verify you at this time') ||
            headingText.includes('unable to verify you') ||
            headingText.includes(
                "It looks like we're having difficulty verifying you"
            ) ||
            headingText.includes('having difficulty verifying') ||
            headingText.includes('sourcesUnavailable') ||
            headingText.includes('Error sourcesUnavailable') ||
            headingText.toLowerCase().includes('sources unavailable')
        ) {
            // VPN/Blocking error - stop tool immediately
            console.log(
                '🚫 VPN/Blocking error detected in heading, stopping tool...'
            );
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            sendStatus(
                '🚫 VPN Error: Unable to verify. Please change VPN and restart.',
                'error'
            );

            // Notify popup to show VPN warning
            chrome.runtime
                .sendMessage({
                    action: 'vpnError',
                    message:
                        "It looks like we're having difficulty verifying you. Please change VPN and restart the tool."
                })
                .catch(() => {});

            return;
        } else if (
            headingText.includes('Error') ||
            headingText.includes('Verification Limit Exceeded') ||
            headingText.includes('verification limit exceeded') ||
            headingText.includes('limit exceeded')
        ) {
            const errorType =
                headingText.includes('Verification Limit Exceeded') ||
                headingText.includes('limit exceeded')
                    ? 'Verification Limit Exceeded'
                    : 'Error';
            console.log(`❌ ${errorType} detected, moving to next data...`);
            sendStatus(`❌ Verification failed: ${errorType}`, 'error');

            // Check if there's more data
            if (currentDataIndex + 1 >= dataArray.length) {
                console.log('❌ No more data to process');
                isRunning = false;
                chrome.storage.local.set({ 'veterans-is-running': false });
                sendStatus('❌ All data failed, no more to try', 'error');
                return;
            }

            // Mark as failed and move to next
            // Remove processed data first (for Verification Limit Exceeded)
            removeProcessedData();
            stats.processed++;
            stats.failed++;
            updateStats();

            // Save updated state (index stays same since we removed one)
            chrome.storage.local.set({
                'veterans-current-index': currentDataIndex,
                'veterans-is-running': true
            });

            console.log(
                `🔄 Moving to next data: ${currentDataIndex + 1}/${
                    dataArray.length
                }`
            );
            sendStatus(
                `🔄 Trying next data: ${currentDataIndex + 1}/${
                    dataArray.length
                }`,
                'info'
            );

            // Go back to start page and continue
            await delay(2000);
            
            // Check if stopped before navigating
            if (!isRunning) {
                console.log('⏹️ Tool stopped, exiting');
                return;
            }
            
            window.location.href = 'https://chatgpt.com/veterans-claim';
            await delay(4000); // Wait longer for page to load
            
            // Check again after navigation
            if (!isRunning) {
                console.log('⏹️ Tool stopped after navigation, exiting');
                return;
            }

            // Continue with next data
            await startVerificationLoop();
        } else if (
            headingText.includes('verified') ||
            headingText.includes("You've been verified")
        ) {
            sendStatus('✅ Verification successful!', 'success');
            console.log(
                '✅ Verification successful, removing processed data...'
            );
            // Remove processed data first
            removeProcessedData();
            stats.processed++;
            stats.success++;
            updateStats();
            // FORCE STOP - ngừng toàn bộ hoạt động tool
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            console.log('✅ Data removed and tool stopped completely');
            // Không tiếp tục vòng lặp, dừng hoàn toàn
            return;
        } else {
            // Try to find form directly even if heading doesn't match
            console.log('🔍 Trying to find form by selector...');
            const formExists = document.querySelector(
                '#sid-military-status + button'
            );
            if (formExists) {
                console.log('✅ Found form by selector!');
                sendStatus(
                    '✅ Found verification form (by selector), filling...',
                    'success'
                );
                if (!currentEmail) {
                    await generateNewEmail();
                }
                
                // Check if stopped after generating email
                if (!isRunning) {
                    console.log('⏹️ Tool stopped after generating email, exiting');
                    return;
                }
                
                await delay(1000);
                
                // Check again before filling form
                if (!isRunning) {
                    console.log('⏹️ Tool stopped before filling form, exiting');
                    return;
                }
                
                await fillForm();
            } else {
                sendStatus('⚠️ Unknown page state: ' + headingText, 'info');
                await delay(2000);
                
                // Check if stopped before retrying
                if (!isRunning) {
                    console.log('⏹️ Tool stopped, exiting checkAndFillForm');
                    return;
                }
                
                await checkAndFillForm();
            }
        }
    } catch (error) {
        // Check if stopped before handling error
        if (!isRunning) {
            console.log('⏹️ Tool stopped during error handling, exiting');
            return;
        }
        
        console.error('Error in checkAndFillForm:', error);
        sendStatus('❌ Error checking page: ' + error.message, 'error');
        // Try to find form directly as fallback
        console.log('🔄 Retrying to find form...');
        await delay(2000);
        
        // Check again after delay
        if (!isRunning) {
            console.log('⏹️ Tool stopped during retry, exiting');
            return;
        }
        
        const formExists = document.querySelector(
            '#sid-military-status + button'
        );
        console.log('Form exists?', !!formExists);
        if (formExists) {
            console.log('✅ Found form on retry!');
            sendStatus('✅ Found form on retry, filling...', 'success');
            if (!currentEmail) {
                await generateNewEmail();
            }
            
            // Check if stopped after generating email
            if (!isRunning) {
                console.log('⏹️ Tool stopped after generating email, exiting');
                return;
            }
            
            await fillForm();
        } else {
            console.error('❌ Form not found even on retry');
            throw error;
        }
    }
}

async function fillForm() {
    // FORCE STOP check at the start
    if (!isRunning) {
        console.log('⏹️ Tool stopped, exiting fillForm');
        return;
    }
    
    console.log('📝 fillForm() called');
    if (!dataArray || dataArray.length === 0) {
        console.error('❌ No data array!');
        sendStatus('❌ No data available', 'error');
        return;
    }
    if (currentDataIndex >= dataArray.length) {
        console.error('❌ Data index out of range!');
        sendStatus('❌ Data index out of range', 'error');
        return;
    }

    const data = dataArray[currentDataIndex];
    console.log('📊 Current data:', data);
    const first = data.first;
    const last = data.last;
    const branch = data.branch.trim();
    const monthName = data.month.trim();
    const day = data.day.trim();
    const year = data.year.trim();
    
    // Convert month name to index (0-11)
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                        'July', 'August', 'September', 'October', 'November', 'December'];
    const monthIndex = monthNames.findIndex(m => 
        m.toLowerCase() === monthName.toLowerCase()
    );
    
    if (monthIndex === -1) {
        throw new Error('Invalid month name: ' + monthName);
    }
    
    console.log('📋 Parsed data:', { first, last, branch, month: monthName, monthIndex, day, year });

    try {
        // 1. Status
        sendStatus('📝 Selecting status...', 'info');
        console.log('🔍 Looking for status button...');
        // Check if stopped before waiting for element
        if (!isRunning) {
            console.log('⏹️ Tool stopped, exiting fillForm');
            return;
        }
        
        const statusButton = await waitForElement(
            '#sid-military-status + button',
            10000
        ).catch((error) => {
            if (error === 'Tool stopped') {
                console.log('⏹️ Tool stopped during waitForElement');
                return null;
            }
            throw error;
        });
        
        if (!statusButton) {
            if (!isRunning) return;
            console.error('❌ Status button not found!');
            throw new Error('Status button not found');
        }
        
        // Check again before clicking
        if (!isRunning) {
            console.log('⏹️ Tool stopped, exiting fillForm');
            return;
        }
        
        console.log('✅ Found status button, clicking...');
        statusButton.click();
        console.log('⏳ Waiting for status menu...');
        
        // Check again before waiting
        if (!isRunning) {
            console.log('⏹️ Tool stopped, exiting fillForm');
            return;
        }
        
        await waitForElement('#sid-military-status-item-1', 10000).catch((error) => {
            if (error === 'Tool stopped') {
                console.log('⏹️ Tool stopped during waitForElement');
                return null;
            }
            throw error;
        });
        await delay(1000);
        const statusItem = document.getElementById(
            'sid-military-status-item-1'
        );
        if (!statusItem) {
            console.error('❌ Status item not found!');
            throw new Error('Status item not found');
        }
        console.log('✅ Found status item, clicking...');
        statusItem.click();
        console.log('✅ Chọn status xong');
        await delay(1500);

        // 2. Branch
        sendStatus('📝 Selecting branch...', 'info');
        const branchButton = await waitForElement(
            '#sid-branch-of-service + button',
            10000
        );
        if (!branchButton) {
            throw new Error('Branch button not found');
        }
        branchButton.click();
        await waitForElement('#sid-branch-of-service-menu', 10000);
        await delay(1000);
        const branchItems = document.querySelectorAll(
            '#sid-branch-of-service-menu .sid-input-select-list__item'
        );
        if (branchItems.length === 0) {
            throw new Error('Branch items not found');
        }
        let matched = false;
        // Match branch name (case insensitive, handles with/without "US" prefix)
        const branchUpper = branch.toUpperCase().trim();
        // Remove "US " prefix if exists for comparison
        const branchNoPrefix = branchUpper.replace(/^US\s+/, '');
        
        for (let item of branchItems) {
            let itemText = item.innerText.toUpperCase().trim();
            // Remove "US " prefix from item text for comparison
            const itemTextNoPrefix = itemText.replace(/^US\s+/, '');
            
            // Try multiple matching strategies:
            // 1. Exact match
            // 2. Match after removing "US " prefix
            // 3. Partial match (branch is substring of item)
            // 4. Partial match reversed (item is substring of branch)
            if (itemText === branchUpper || 
                itemTextNoPrefix === branchNoPrefix ||
                itemText.includes(branchUpper) ||
                branchUpper.includes(itemTextNoPrefix) ||
                itemTextNoPrefix.includes(branchNoPrefix) ||
                branchNoPrefix.includes(itemTextNoPrefix)) {
                item.click();
                matched = true;
                console.log(`✅ Matched branch: "${branch}" with item: "${item.innerText}"`);
                break;
            }
        }
        if (!matched) {
            throw new Error('Branch not found: ' + branch);
        }
        console.log('✅ Chọn branch xong');
        await delay(200);

        // 3. First & Last name
        sendStatus('📝 Entering name...', 'info');
        const firstNameInput = document.getElementById('sid-first-name');
        const lastNameInput = document.getElementById('sid-last-name');

        if (!firstNameInput || !lastNameInput) {
            throw new Error('Name inputs not found');
        }

        firstNameInput.value = first;
        firstNameInput.dispatchEvent(new Event('input', { bubbles: true }));
        firstNameInput.dispatchEvent(new Event('change', { bubbles: true }));
        await delay(200);

        lastNameInput.value = last;
        lastNameInput.dispatchEvent(new Event('input', { bubbles: true }));
        lastNameInput.dispatchEvent(new Event('change', { bubbles: true }));
        console.log('✅ Nhập tên xong');
        await delay(200);

        // 4. DOB
        sendStatus('📝 Entering date of birth...', 'info');
        const dayInput = document.getElementById('sid-birthdate-day');
        const yearInput = document.getElementById('sid-birthdate-year');
        const dayValue = parseInt(day).toString();
        const yearValue = year;

        const monthButton = await waitForElement(
            '#sid-birthdate__month + button',
            10000
        );
        if (!monthButton) {
            throw new Error('Month button not found');
        }
        monthButton.click();
        await waitForElement('#sid-birthdate__month-menu', 10000);
        await delay(200);
        const monthItem = document.getElementById(
            `sid-birthdate__month-item-${monthIndex}`
        );
        if (!monthItem) {
            throw new Error('Month item not found: ' + monthIndex);
        }
        monthItem.click();
        await delay(200);

        if (!dayInput || !yearInput) {
            throw new Error('Date inputs not found');
        }
        dayInput.value = dayValue;
        dayInput.dispatchEvent(new Event('input', { bubbles: true }));
        dayInput.dispatchEvent(new Event('change', { bubbles: true }));
        await delay(200);

        yearInput.value = yearValue;
        yearInput.dispatchEvent(new Event('input', { bubbles: true }));
        yearInput.dispatchEvent(new Event('change', { bubbles: true }));
        console.log('✅ Ngày sinh xong');
        await delay(200);

        // 5. Discharge Date (2/1/2025)
        sendStatus('📝 Entering discharge date...', 'info');
        const dischargeDayInput = document.getElementById(
            'sid-discharge-date-day'
        );
        const dischargeYearInput = document.getElementById(
            'sid-discharge-date-year'
        );

        const dischargeMonthButton = await waitForElement(
            '#sid-discharge-date__month + button',
            10000
        );
        if (!dischargeMonthButton) {
            throw new Error('Discharge month button not found');
        }
        dischargeMonthButton.click();
        await waitForElement('#sid-discharge-date__month-menu', 10000);
        await delay(200);
        const dischargeMonthItem = document.getElementById(
            'sid-discharge-date__month-item-1'
        );
        if (!dischargeMonthItem) {
            throw new Error('Discharge month item not found');
        }
        dischargeMonthItem.click();
        await delay(200);

        if (!dischargeDayInput || !dischargeYearInput) {
            throw new Error('Discharge date inputs not found');
        }
        dischargeDayInput.value = '1';
        dischargeDayInput.dispatchEvent(new Event('input', { bubbles: true }));
        dischargeDayInput.dispatchEvent(new Event('change', { bubbles: true }));
        await delay(200);

        dischargeYearInput.value = '2025';
        dischargeYearInput.dispatchEvent(new Event('input', { bubbles: true }));
        dischargeYearInput.dispatchEvent(
            new Event('change', { bubbles: true })
        );
        console.log('✅ Discharge date xong');
        await delay(200);

        // 6. Email
        sendStatus('📝 Entering email...', 'info');
        const emailInput = document.getElementById('sid-email');
        if (!emailInput) {
            throw new Error('Email input not found');
        }
        emailInput.value = currentEmail;
        emailInput.dispatchEvent(new Event('input', { bubbles: true }));
        emailInput.dispatchEvent(new Event('change', { bubbles: true }));
        console.log('✅ Nhập email xong');
        await delay(200);

        // 7. Submit
        sendStatus('🚀 Submitting form...', 'info');
        const submitBtn = document.getElementById(
            'sid-submit-btn-collect-info'
        );
        if (!submitBtn) {
            throw new Error('Submit button not found');
        }
        submitBtn.click();
        console.log('🚀 Đã nhấn Submit');
        sendStatus('✅ Form submitted, waiting for response...', 'success');

        // Wait for page to change
        await delay(5000);
        
        // Check if stopped before checking form
        if (!isRunning) {
            console.log('⏹️ Tool stopped after form submission, exiting');
            return;
        }

        // Check for "Check your email" or error
        await checkAndFillForm();
    } catch (error) {
        console.error('Error filling form:', error);
        throw error;
    }
}

async function readMailAndVerify() {
    // FORCE STOP check at the start
    if (!isRunning) {
        console.log('⏹️ Tool stopped, exiting readMailAndVerify');
        return;
    }
    
    try {
        sendStatus('📧 Reading emails...', 'info');

        // Parse email
        const [username, domain] = currentEmail.split('@');
        if (!username || !domain) {
            throw new Error('Invalid email format');
        }

        // Get emails from API
        const emailsResponse = await fetch(
            `https://tinyhost.shop/api/email/${domain}/${username}/?page=1&limit=20`
        );

        if (!emailsResponse.ok) {
            throw new Error('Failed to fetch emails');
        }

        const emailsData = await emailsResponse.json();
        const emails = emailsData.emails || [];

        if (emails.length === 0) {
            mailRetryCount++;
            if (mailRetryCount >= MAX_MAIL_RETRIES) {
                sendStatus(
                    '❌ Max retries reached for reading mail, moving to next data',
                    'error'
                );
                // Move to next data
                currentDataIndex++;
                stats.processed++;
                stats.failed++;
                updateStats();
                mailRetryCount = 0;
                await delay(2000);
                window.location.href = 'https://chatgpt.com/veterans-claim';
                await delay(3000);
                await startVerificationLoop();
                return;
            }
            sendStatus(
                `📭 No emails found, retrying... (${mailRetryCount}/${MAX_MAIL_RETRIES})`,
                'info'
            );
            await delay(5000);
            await readMailAndVerify();
            return;
        }

        mailRetryCount = 0; // Reset on success

        // Sort by date (newest first)
        emails.sort((a, b) => {
            const dateA = new Date(a.date);
            const dateB = new Date(b.date);
            return dateB - dateA;
        });

        // Find verification link
        let verificationLink = null;
        for (const email of emails) {
            if (email.html_body) {
                const htmlLinkMatch = email.html_body.match(
                    /https:\/\/services\.sheerid\.com\/verify\/[^"'\s<>]+/i
                );
                if (htmlLinkMatch) {
                    verificationLink = htmlLinkMatch[0].replace(/&amp;/g, '&');
                    break;
                }
            }

            if (email.body) {
                const bodyLinkMatch = email.body.match(
                    /https:\/\/services\.sheerid\.com\/verify\/[^"'\s<>()]+/i
                );
                if (bodyLinkMatch) {
                    verificationLink = bodyLinkMatch[0].replace(/&amp;/g, '&');
                    break;
                }
            }
        }

        if (verificationLink) {
            // Check if stopped before opening link
            if (!isRunning) {
                console.log('⏹️ Tool stopped, exiting readMailAndVerify');
                return;
            }
            
            sendStatus('✅ Verification link found, opening...', 'success');
            mailRetryCount = 0; // Reset on success
            window.location.href = verificationLink;
            await delay(5000);
            
            // Check again after navigation
            if (!isRunning) {
                console.log('⏹️ Tool stopped after navigation, exiting');
                return;
            }
            
            await checkAndFillForm();
        } else {
            // Check if stopped before retrying
            if (!isRunning) {
                console.log('⏹️ Tool stopped, exiting readMailAndVerify');
                return;
            }
            
            mailRetryCount++;
            if (mailRetryCount >= MAX_MAIL_RETRIES) {
                sendStatus(
                    '❌ Max retries reached, moving to next data',
                    'error'
                );
                // Move to next data
                currentDataIndex++;
                stats.processed++;
                stats.failed++;
                updateStats();
                mailRetryCount = 0;
                await delay(2000);
                
                // Check if stopped before navigating
                if (!isRunning) {
                    console.log('⏹️ Tool stopped, exiting');
                    return;
                }
                
                window.location.href = 'https://chatgpt.com/veterans-claim';
                await delay(3000);
                
                // Check again after navigation
                if (!isRunning) {
                    console.log('⏹️ Tool stopped after navigation, exiting');
                    return;
                }
                
                await startVerificationLoop();
                return;
            }
            sendStatus(
                `⚠️ No verification link found, retrying... (${mailRetryCount}/${MAX_MAIL_RETRIES})`,
                'info'
            );
            await delay(5000);
            
            // Check again before retrying
            if (!isRunning) {
                console.log('⏹️ Tool stopped, exiting readMailAndVerify');
                return;
            }
            
            await readMailAndVerify();
        }
    } catch (error) {
        // Check if stopped before handling error
        if (!isRunning) {
            console.log('⏹️ Tool stopped during error handling, exiting');
            return;
        }
        
        console.error('Error reading mail:', error);
        mailRetryCount++;
        if (mailRetryCount >= MAX_MAIL_RETRIES) {
            sendStatus('❌ Max retries reached, moving to next data', 'error');
            // Move to next data
            currentDataIndex++;
            stats.processed++;
            stats.failed++;
            updateStats();
            mailRetryCount = 0;
            await delay(2000);
            
            // Check if stopped before navigating
            if (!isRunning) {
                console.log('⏹️ Tool stopped, exiting');
                return;
            }
            
            window.location.href = 'https://chatgpt.com/veterans-claim';
            await delay(3000);
            
            // Check again after navigation
            if (!isRunning) {
                console.log('⏹️ Tool stopped after navigation, exiting');
                return;
            }
            
            await startVerificationLoop();
            return;
        }
        sendStatus(
            `❌ Error reading mail, retrying... (${mailRetryCount}/${MAX_MAIL_RETRIES}): ` +
                error.message,
            'error'
        );
        // Retry after delay
        await delay(5000);
        
        // Check again before retrying
        if (!isRunning) {
            console.log('⏹️ Tool stopped, exiting readMailAndVerify');
            return;
        }
        
        await readMailAndVerify();
    }
}

// Helper functions
function waitForElement(selector, timeout = 10000) {
    return new Promise((resolve, reject) => {
        // Check if stopped before starting
        if (!isRunning) {
            reject('Tool stopped');
            return;
        }
        
        // Check immediately first
        const check = () => {
            // Check isRunning before checking element
            if (!isRunning) {
                observer.disconnect();
                reject('Tool stopped');
                return false;
            }
            
            const element = document.querySelector(selector);
            if (element) {
                resolve(element);
                return true;
            }
            return false;
        };

        if (check()) {
            return;
        }

        // Use MutationObserver to watch for changes
        const observer = new MutationObserver(() => {
            if (check()) {
                observer.disconnect();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class', 'style']
        });

        // Check isRunning periodically during wait
        const checkInterval = setInterval(() => {
            if (!isRunning) {
                clearInterval(checkInterval);
                observer.disconnect();
                reject('Tool stopped');
            }
        }, 500); // Check every 500ms

        setTimeout(() => {
            clearInterval(checkInterval);
            observer.disconnect();
            reject('Timeout for: ' + selector);
        }, timeout);
    });
}

function waitForUrlChange(contains, timeout = 15000) {
    return new Promise((resolve) => {
        // Check if stopped before starting
        if (!isRunning) {
            resolve(false);
            return;
        }
        
        if (window.location.href.includes(contains)) {
            resolve(true);
            return;
        }

        const checkInterval = setInterval(() => {
            // Check isRunning during wait
            if (!isRunning) {
                clearInterval(checkInterval);
                resolve(false);
                return;
            }
            
            if (window.location.href.includes(contains)) {
                clearInterval(checkInterval);
                resolve(true);
            }
        }, 500);

        setTimeout(() => {
            clearInterval(checkInterval);
            resolve(false);
        }, timeout);
    });
}

function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function sendStatus(message, type = 'info') {
    // Update UI panel if exists
    updateUIPanelStatus(message, type);
    
    // Send to background, which will forward to popup
    chrome.runtime
        .sendMessage({
            action: 'updateStatus',
            status: message,
            type: type
        })
        .catch(() => {
            // Ignore errors if popup is closed
        });
}

function updateStats() {
    // Save stats to storage
    chrome.storage.local.set({
        'veterans-stats': stats
    });

    // Update UI panel if exists
    updateUIPanel();

    chrome.runtime
        .sendMessage({
            action: 'updateStats',
            processed: stats.processed,
            success: stats.success,
            failed: stats.failed,
            current:
                currentDataIndex < dataArray.length
                    ? `${dataArray[currentDataIndex].first} ${dataArray[currentDataIndex].last}`
                    : '-'
        })
        .catch(() => {
            // Ignore errors if popup is closed
        });
}

// Helper function to update UI when verification stops
function updateUIOnStop() {
    const startBtn = document.getElementById('veterans-start-btn');
    const stopBtn = document.getElementById('veterans-stop-btn');
    const skipBtn = document.getElementById('veterans-skip-btn');
    // Nút START và STOP luôn hiển thị, chỉ disable/enable
    if (startBtn) {
        const hasData = dataArray && dataArray.length > 0;
        startBtn.disabled = !hasData;
    }
    if (stopBtn) stopBtn.disabled = true;
    // Enable và hiển thị nút SKIP khi tool STOP
    if (skipBtn) {
        skipBtn.style.display = 'block';
        skipBtn.disabled = false;
    }
    updateUIPanel();
}

function removeProcessedData() {
    // Remove the current data from array and update storage
    if (currentDataIndex < dataArray.length) {
        const processedData = dataArray[currentDataIndex];
        dataArray.splice(currentDataIndex, 1);

        // Rebuild data list string from remaining data
        const updatedDataList = dataArray
            .map((data) => data.original)
            .join('\n');

        // Use atomic operation to prevent race condition when multiple browsers run
        chrome.storage.local.get(['veterans-data-lock'], (lockResult) => {
            // Simple lock mechanism - wait if locked
            if (lockResult['veterans-data-lock']) {
                setTimeout(() => removeProcessedData(), 100);
                return;
            }

            // Set lock
            chrome.storage.local.set({ 'veterans-data-lock': true }, () => {
                // Update storage with new array and updated data list
                chrome.storage.local.set(
                    {
                        'veterans-data-array': dataArray,
                        'veterans-data-list': updatedDataList, // Save updated data list as string
                        'veterans-current-index': currentDataIndex, // Keep same index since we removed one
                        'veterans-is-running': true
                    },
                    () => {
                        // Release lock after 500ms
                        setTimeout(() => {
                            chrome.storage.local.remove('veterans-data-lock');
                        }, 500);
                    }
                );
            });
        });

        // Notify popup to remove the line from textarea and auto-save file
        chrome.runtime
            .sendMessage({
                action: 'removeDataLine',
                original: processedData.original,
                updatedDataList: updatedDataList, // Also send updated list
                autoSave: true // Flag to auto-save file
            })
            .catch(() => {
                // Ignore if popup is closed - data is already saved to storage
            });

        console.log('🗑️ Removed processed data:', processedData.original);
        console.log('💾 Updated data list saved to storage');
    }
}


// ==================== UI Panel Functions ====================
let uiPanel = null;
let uiToggleBtn = null;
let isPanelOpen = false;
let isPanelPinned = false;

// Initialize UI Panel
function initUIPanel() {
    // Check if panel already exists - if so, just update it
    const existingPanel = document.getElementById('veterans-extension-panel');
    if (existingPanel) {
        console.log('⚠️ Panel already exists, updating...');
        // Update existing panel instead of creating new one
        loadPanelData();
        updateUIPanel();
        return;
    }

    // Create toggle button
    uiToggleBtn = document.createElement('div');
    uiToggleBtn.id = 'veterans-toggle-btn';
    uiToggleBtn.innerHTML = '🚀';
    uiToggleBtn.title = 'ChatGPT Veterans Auto Verify';
    
    // Create panel
    uiPanel = document.createElement('div');
    uiPanel.id = 'veterans-extension-panel';
    uiPanel.innerHTML = `
        <div class="veterans-panel-header">
            <div class="veterans-panel-title">
                <span>🚀 ChatGPT Veterans</span>
            </div>
            <div class="veterans-panel-actions">
                <button class="veterans-panel-pin" id="veterans-panel-pin-btn" title="Ghim panel">
                    📌
                </button>
                <button class="veterans-panel-close" id="veterans-panel-close-btn" title="Đóng panel">×</button>
            </div>
        </div>
        <div class="veterans-panel-content">
            <div class="veterans-form-section">
                <label class="veterans-form-label">Data List</label>
                <div class="veterans-file-buttons">
                    <input type="file" id="veterans-file-input" accept=".txt" style="display: none;" />
                    <button id="veterans-load-btn" class="veterans-btn veterans-btn-load">📁 Load File</button>
                    <button id="veterans-save-btn" class="veterans-btn veterans-btn-save">💾 Save</button>
                </div>
                <div class="veterans-data-info" id="veterans-data-info">
                    <span id="veterans-data-count">0</span> data loaded
                </div>
            </div>
            
            <div class="veterans-form-section">
                <label class="veterans-form-label">DATA RANGE (OPTIONAL)</label>
                <div class="veterans-range-inputs">
                    <div class="veterans-range-item">
                        <label class="veterans-range-label">FROM:</label>
                        <input type="number" id="veterans-range-from" class="veterans-range-input" min="1" value="1" />
                    </div>
                    <div class="veterans-range-item">
                        <label class="veterans-range-label">TO:</label>
                        <input type="number" id="veterans-range-to" class="veterans-range-input" min="1" value="100" />
                    </div>
                </div>
                <div class="veterans-range-info" id="veterans-range-info" style="display: none;">
                    <span id="veterans-range-text">Will process: 0 data</span>
                </div>
            </div>
            
            <div class="veterans-button-group">
                <div class="veterans-start-stop-row">
                    <button id="veterans-start-btn" class="veterans-btn veterans-btn-start" disabled>▶️ Start Verification</button>
                    <button id="veterans-stop-btn" class="veterans-btn veterans-btn-stop">⏹️ Stop</button>
                </div>
                <button id="veterans-skip-btn" class="veterans-btn veterans-btn-skip" style="display: none;">⏭️ Skip</button>
            </div>
            
            <div class="veterans-status-section">
                <div class="veterans-status-label">Status:</div>
                <div id="veterans-panel-status" class="veterans-status-text">Ready</div>
            </div>
            
            <div class="veterans-stats-section">
                <div class="veterans-stats-item">
                    <span class="veterans-stats-label">Total:</span>
                    <span id="veterans-panel-total" class="veterans-stats-value">0</span>
                </div>
                <div class="veterans-stats-item">
                    <span class="veterans-stats-label">Processed:</span>
                    <span id="veterans-panel-processed" class="veterans-stats-value">0</span>
                </div>
                <div class="veterans-stats-item">
                    <span class="veterans-stats-label">Success:</span>
                    <span id="veterans-panel-success" class="veterans-stats-value success">0</span>
                </div>
                <div class="veterans-stats-item">
                    <span class="veterans-stats-label">Failed:</span>
                    <span id="veterans-panel-failed" class="veterans-stats-value error">0</span>
                </div>
            </div>
            
            <div class="veterans-form-section">
                <label class="veterans-form-label">Veteran</label>
                <input id="veterans-panel-current" type="text" class="veterans-input" value="-" readonly />
            </div>
            
            <div class="veterans-form-section">
                <label class="veterans-form-label">Current Email</label>
                <input id="veterans-email-input" type="text" class="veterans-input" placeholder="Email will be auto-generated..." readonly />
            </div>
        </div>
    `;

    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        #veterans-toggle-btn {
            position: fixed;
            right: 20px;
            top: 50%;
            transform: translateY(-50%);
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            cursor: pointer;
            z-index: 999998;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        
        #veterans-toggle-btn:hover {
            transform: translateY(-50%) scale(1.1);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
            border-color: rgba(99, 102, 241, 0.5);
        }
        
        #veterans-extension-panel {
            position: fixed;
            right: 0;
            top: 0;
            width: 320px;
            height: 100vh;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            border-left: 2px solid rgba(255, 255, 255, 0.1);
            z-index: 999999;
            display: none;
            flex-direction: column;
            box-shadow: -4px 0 20px rgba(0, 0, 0, 0.5);
            transition: transform 0.3s ease;
            color: #e4e4e7;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }
        
        #veterans-extension-panel.panel-open {
            display: flex;
        }
        
        .veterans-panel-header {
            padding: 16px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(30, 30, 46, 0.5);
        }
        
        .veterans-panel-title {
            font-size: 16px;
            font-weight: 700;
            color: #ffffff;
        }
        
        .veterans-panel-actions {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        .veterans-panel-pin {
            background: transparent;
            border: none;
            color: #a1a1aa;
            font-size: 18px;
            cursor: pointer;
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 4px;
            transition: all 0.2s;
            opacity: 0.6;
            padding: 0;
            line-height: 1;
        }
        
        .veterans-panel-pin:hover {
            background: rgba(245, 158, 11, 0.2);
            color: #f59e0b;
            opacity: 1;
        }
        
        .veterans-panel-pin.pinned {
            opacity: 1;
            color: #f59e0b;
        }
        
        .veterans-panel-close {
            background: transparent;
            border: none;
            color: #a1a1aa;
            font-size: 28px;
            cursor: pointer;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 4px;
            transition: all 0.2s;
        }
        
        .veterans-panel-close:hover {
            background: rgba(239, 68, 68, 0.2);
            color: #f87171;
        }
        
        .veterans-panel-content {
            padding: 16px;
            flex: 1;
            overflow-y: auto;
        }
        
        .veterans-status-section {
            margin-bottom: 20px;
            padding: 12px;
            background: rgba(30, 30, 46, 0.6);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .veterans-status-label {
            font-size: 11px;
            color: #a1a1aa;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .veterans-status-text {
            font-size: 13px;
            color: #e4e4e7;
            word-break: break-word;
        }
        
        .veterans-status-text.success {
            color: #34d399;
        }
        
        .veterans-status-text.error {
            color: #f87171;
        }
        
        .veterans-stats-section {
            margin-bottom: 20px;
            padding: 12px;
            background: rgba(30, 30, 46, 0.6);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .veterans-stats-item {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .veterans-stats-item:last-child {
            border-bottom: none;
        }
        
        .veterans-stats-label {
            font-size: 12px;
            color: #a1a1aa;
        }
        
        .veterans-stats-value {
            font-size: 12px;
            font-weight: 600;
            color: #ffffff;
        }
        
        .veterans-stats-value.success {
            color: #34d399;
        }
        
        .veterans-stats-value.error {
            color: #f87171;
        }
        
        .veterans-email-section {
            padding: 12px;
            background: rgba(30, 30, 46, 0.6);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .veterans-email-label {
            font-size: 11px;
            color: #a1a1aa;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .veterans-email-text {
            font-size: 12px;
            color: #e4e4e7;
            word-break: break-all;
        }
        
        .veterans-form-section {
            margin-bottom: 16px;
        }
        
        .veterans-form-label {
            display: block;
            font-size: 11px;
            color: #a1a1aa;
            margin-bottom: 6px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .veterans-file-buttons {
            display: flex;
            gap: 6px;
            margin-bottom: 8px;
        }
        
        .veterans-btn {
            padding: 8px 12px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            font-size: 11px;
            transition: all 0.2s;
            white-space: nowrap;
            flex: 1;
        }
        
        .veterans-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            filter: brightness(1.1);
        }
        
        .veterans-btn:active {
            transform: translateY(0);
        }
        
        .veterans-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .veterans-btn-load {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        
        .veterans-btn-save {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        
        .veterans-start-stop-row {
            display: flex;
            gap: 8px;
            margin-bottom: 8px;
        }
        
        .veterans-btn-start {
            flex: 1;
            padding: 10px;
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            border: 1px solid rgba(245, 158, 11, 0.3);
            font-weight: 700;
            font-size: 12px;
        }
        
        .veterans-btn-start:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
            border-color: rgba(107, 114, 128, 0.3);
        }
        
        .veterans-btn-start:disabled:hover {
            transform: none;
            box-shadow: none;
            filter: none;
        }
        
        .veterans-btn-stop {
            flex: 1;
            padding: 10px;
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            border: 1px solid rgba(239, 68, 68, 0.3);
            font-weight: 700;
            font-size: 12px;
        }
        
        .veterans-btn-stop:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
            border-color: rgba(107, 114, 128, 0.3);
        }
        
        .veterans-btn-stop:disabled:hover {
            transform: none;
            box-shadow: none;
            filter: none;
        }
        
        .veterans-btn-skip {
            width: 100%;
            padding: 5px;
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
            color: white;
            border: 1px solid rgba(139, 92, 246, 0.3);
            font-weight: 700;
            font-size: 12px;
        }
        
        .veterans-btn-skip:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
            border-color: rgba(107, 114, 128, 0.3);
        }
        
        .veterans-btn-skip:disabled:hover {
            transform: none;
            box-shadow: none;
            filter: none;
        }
        
        .veterans-data-info {
            font-size: 11px;
            color: #34d399;
            margin-top: 8px;
            padding: 6px 10px;
            background: rgba(16, 185, 129, 0.1);
            border-radius: 4px;
            border: 1px solid rgba(16, 185, 129, 0.2);
            display: none;
        }
        
        .veterans-data-info.show {
            display: block;
        }
        
        .veterans-input {
            width: 100%;
            padding: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            background: rgba(30, 30, 46, 0.6);
            color: #e4e4e7;
            font-size: 11px;
            font-family: inherit;
            transition: all 0.2s ease;
        }
        
        .veterans-input:focus {
            outline: none;
            border-color: rgba(99, 102, 241, 0.5);
            background: rgba(30, 30, 46, 0.8);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }
        
        .veterans-input::placeholder {
            color: #71717a;
        }
        
        .veterans-input[readonly] {
            cursor: not-allowed;
            border-color: rgba(255, 255, 255, 0.05);
        }
        
        .veterans-button-group {
            margin-bottom: 16px;
        }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(uiToggleBtn);
    document.body.appendChild(uiPanel);

    // Event listeners
    uiToggleBtn.addEventListener('click', togglePanel);
    document.getElementById('veterans-panel-close-btn').addEventListener('click', togglePanel);
    document.getElementById('veterans-panel-pin-btn').addEventListener('click', togglePin);
    
    // Prevent panel from closing when clicking inside
    uiPanel.addEventListener('click', (e) => {
        e.stopPropagation();
    });
    
    // Prevent panel from closing when clicking on toggle button
    uiToggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
    });
    
    // Load pinned state from storage and auto-open if pinned
    chrome.storage.local.get(['veterans-panel-pinned'], (result) => {
        if (result['veterans-panel-pinned']) {
            isPanelPinned = true;
            updatePinButton();
            // Auto-open panel if it was pinned
            if (!isPanelOpen) {
                togglePanel();
            }
        }
        updatePinButton();
    });
    
    // Setup panel event handlers
    setupPanelHandlers();
    
    // Load saved data
    loadPanelData();
    
    // Close panel when clicking outside (only if not pinned)
    document.addEventListener('click', (e) => {
        if (isPanelOpen && 
            !isPanelPinned &&
            !uiPanel.contains(e.target) && 
            !uiToggleBtn.contains(e.target)) {
            togglePanel();
        }
    });
    
    // Load initial data
    updateUIPanel();
}

function togglePanel() {
    isPanelOpen = !isPanelOpen;
    if (isPanelOpen) {
        uiPanel.classList.add('panel-open');
        uiToggleBtn.style.display = 'none';
    } else {
        uiPanel.classList.remove('panel-open');
        uiToggleBtn.style.display = 'flex';
    }
}

function togglePin() {
    isPanelPinned = !isPanelPinned;
    updatePinButton();
    
    // Save pinned state to storage
    chrome.storage.local.set({ 'veterans-panel-pinned': isPanelPinned });
    
    // Show feedback
    const pinBtn = document.getElementById('veterans-panel-pin-btn');
    if (pinBtn) {
        pinBtn.style.transform = 'scale(1.2)';
        setTimeout(() => {
            pinBtn.style.transform = 'scale(1)';
        }, 200);
    }
}

function updatePinButton() {
    const pinBtn = document.getElementById('veterans-panel-pin-btn');
    if (pinBtn) {
        if (isPanelPinned) {
            pinBtn.classList.add('pinned');
            pinBtn.innerHTML = '📌';
            pinBtn.title = 'Bỏ ghim panel';
            pinBtn.style.opacity = '1';
            pinBtn.style.color = '#f59e0b';
        } else {
            pinBtn.classList.remove('pinned');
            pinBtn.innerHTML = '📌';
            pinBtn.title = 'Ghim panel';
            pinBtn.style.opacity = '0.6';
            pinBtn.style.color = '#a1a1aa';
        }
    }
}

function updateUIPanel() {
    if (!uiPanel) return;
    
    const totalEl = document.getElementById('veterans-panel-total');
    const processedEl = document.getElementById('veterans-panel-processed');
    const successEl = document.getElementById('veterans-panel-success');
    const failedEl = document.getElementById('veterans-panel-failed');
    const currentEl = document.getElementById('veterans-panel-current');
    
    if (totalEl) totalEl.textContent = dataArray.length || 0;
    if (processedEl) processedEl.textContent = stats.processed || 0;
    if (successEl) successEl.textContent = stats.success || 0;
    if (failedEl) failedEl.textContent = stats.failed || 0;
    if (currentEl) {
        currentEl.value = currentDataIndex < dataArray.length && dataArray.length > 0
            ? `${dataArray[currentDataIndex].first} ${dataArray[currentDataIndex].last}`
            : '-';
    }
}

function updateUIPanelStatus(message, type = 'info') {
    if (!uiPanel) return;
    
    const statusEl = document.getElementById('veterans-panel-status');
    if (statusEl) {
        statusEl.textContent = message;
        statusEl.className = 'veterans-status-text ' + 
            (type === 'success' ? 'success' : type === 'error' ? 'error' : '');
    }
    
    // Update email if exists
    if (currentEmail) {
        const emailEl = document.getElementById('veterans-panel-email');
        const emailInput = document.getElementById('veterans-email-input');
        if (emailEl) emailEl.textContent = currentEmail;
        if (emailInput) emailInput.value = currentEmail;
    }
}

// Setup panel event handlers
function setupPanelHandlers() {
    // Load file button
    const loadBtn = document.getElementById('veterans-load-btn');
    const fileInput = document.getElementById('veterans-file-input');
    
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
                
                // Parse and count valid data lines
                const dataLines = content.split('\n').filter((line) => line.trim());
                const validData = dataLines.filter((line) => {
                    const parts = line.trim().split('|');
                    return parts.length === 6;
                });
                
                // Save to storage
                chrome.storage.local.set({ 'veterans-data-list': content });
                localStorage.setItem('veterans-data-list', content);
                
                // Show data count
                const dataInfo = document.getElementById('veterans-data-info');
                const dataCount = document.getElementById('veterans-data-count');
                if (dataInfo && dataCount) {
                    dataCount.textContent = validData.length;
                    dataInfo.classList.add('show');
                }
                
                // Enable nút START khi đã load file thành công
                const startBtn = document.getElementById('veterans-start-btn');
                if (startBtn) {
                    startBtn.disabled = validData.length === 0;
                }
                
                updateUIPanelStatus(`✅ Loaded ${validData.length} data entries`, 'success');
                
                // Reset file input
                fileInput.value = '';
            };
            reader.readAsText(file);
        });
    }
    
    // Save file button
    const saveBtn = document.getElementById('veterans-save-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            chrome.storage.local.get(['veterans-data-list'], (result) => {
                let dataList = result['veterans-data-list'];
                
                if (!dataList || !dataList.trim()) {
                    updateUIPanelStatus('❌ No data to save', 'error');
                    return;
                }
                
                const blob = new Blob([dataList], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'data.txt';
                a.click();
                URL.revokeObjectURL(url);
                updateUIPanelStatus('✅ File saved successfully', 'success');
            });
        });
    }
    
    // Start button
    const startBtn = document.getElementById('veterans-start-btn');
    if (startBtn) {
        startBtn.addEventListener('click', async () => {
            // Get data from storage
            chrome.storage.local.get(['veterans-data-list'], async (result) => {
                let dataList = result['veterans-data-list'];
                
                if (!dataList || !dataList.trim()) {
                    updateUIPanelStatus('❌ Please load data first', 'error');
                    return;
                }
                
                // Parse data
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
                    updateUIPanelStatus('❌ No valid data found', 'error');
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
                
                // Start verification directly
                updateUIPanelStatus('🚀 Starting verification...', 'info');
                
                // Set data and start verification
                const instanceId = getInstanceId();
                // Set global variables
                dataArray = parsedDataArray;
                currentEmail = '';
                mailRetryCount = 0;
                stats = { processed: 0, success: 0, failed: 0 };
                isRunning = true;
                currentDataIndex = 0;
                
                // Rebuild data list string for storage
                const dataListString = parsedDataArray
                    .map((data) => data.original)
                    .join('\n');
                
                // Save to storage
                chrome.storage.local.set({
                    'veterans-data-array': parsedDataArray,
                    'veterans-data-list': dataListString,
                    'veterans-current-index': 0,
                    'veterans-is-running': true,
                    'veterans-stats': stats
                }, () => {
                    console.log('✅ Data saved to storage');
                    
                    // Navigate to ChatGPT page if not already there
                    if (!window.location.href.includes('chatgpt.com/veterans-claim')) {
                        updateUIPanelStatus('🌐 Navigating to ChatGPT page...', 'info');
                        window.location.href = 'https://chatgpt.com/veterans-claim';
                        // Will auto-resume after navigation
                    } else {
                        // Already on the right page, start directly
                        setTimeout(() => {
                            startVerificationLoop();
                        }, 1000);
                    }
                });
            });
        });
    }
    
    // Stop button
    const stopBtn = document.getElementById('veterans-stop-btn');
    if (stopBtn) {
        stopBtn.addEventListener('click', async () => {
            updateUIPanelStatus('⏹️ Stopping verification...', 'info');
            
            // FORCE STOP: Set isRunning = false immediately
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            
            // Unregister this instance
            const instanceId = getInstanceId();
            chrome.storage.local.get(['veterans-active-instances'], (result) => {
                const activeInstances = result['veterans-active-instances'] || {};
                delete activeInstances[instanceId];
                chrome.storage.local.set({
                    'veterans-active-instances': activeInstances
                });
            });
            
            // Update UI
            updateUIOnStop();
            stopBtn.disabled = true;
            const startBtn = document.getElementById('veterans-start-btn');
            // Nút START và STOP luôn hiển thị, chỉ disable/enable
            if (startBtn) {
                const hasData = dataArray && dataArray.length > 0;
                startBtn.disabled = !hasData;
            }
            
            updateUIPanelStatus('✅ Verification stopped', 'success');
            sendStatus('⏹️ Verification stopped by user', 'info');
        });
    }
    
    // Skip button - chỉ hoạt động khi tool STOP
    const skipBtn = document.getElementById('veterans-skip-btn');
    if (skipBtn) {
        skipBtn.addEventListener('click', async () => {
            // Chỉ cho phép skip khi tool đang STOP
            if (isRunning) {
                updateUIPanelStatus('⚠️ Cannot skip while tool is running. Please stop first.', 'info');
                return;
            }
            
            if (dataArray.length === 0) {
                updateUIPanelStatus('⚠️ No data to skip', 'info');
                return;
            }
            
            if (currentDataIndex >= dataArray.length) {
                updateUIPanelStatus('⚠️ No more data to skip', 'info');
                return;
            }
            
            updateUIPanelStatus('⏭️ Skipping current data...', 'info');
            sendStatus('⏭️ Skipping current data...', 'info');
            
            // Remove current data (skip it)
            const skippedData = dataArray[currentDataIndex];
            console.log('⏭️ Skipping data:', skippedData.original);
            dataArray.splice(currentDataIndex, 1);
            
            // Rebuild data list string
            const updatedDataList = dataArray
                .map((data) => data.original)
                .join('\n');
            
            // Update stats
            stats.processed++;
            stats.failed++; // Count skipped as failed
            updateStats();
            
            // Reset email and retry count for next data
            currentEmail = '';
            mailRetryCount = 0;
            
            // Save to storage (tool vẫn STOP)
            chrome.storage.local.set({
                'veterans-data-array': dataArray,
                'veterans-data-list': updatedDataList,
                'veterans-current-index': currentDataIndex, // Keep same index since we removed one
                'veterans-is-running': false, // Tool vẫn STOP
                'veterans-stats': stats
            });
            
            // Check if there's more data
            if (currentDataIndex >= dataArray.length) {
                // No more data
                updateUIOnStop();
                sendStatus('✅ All data processed', 'success');
                updateUIPanelStatus('✅ All data processed', 'success');
                return;
            }
            
            // Log next data info
            const nextData = dataArray[currentDataIndex];
            console.log(`⏭️ Next data after skip: ${nextData.first} ${nextData.last} (index ${currentDataIndex})`);
            
            // Update UI to show next data
            updateUIPanel();
            sendStatus(
                `⏭️ Skipped. Next data: ${currentDataIndex + 1}/${dataArray.length}: ${
                    nextData.first
                } ${nextData.last}`,
                'info'
            );
            updateUIPanelStatus(
                `⏭️ Skipped. Next data: ${currentDataIndex + 1}/${dataArray.length}: ${nextData.first} ${nextData.last}`,
                'success'
            );
        });
    }
}

// Load saved data into panel
function loadPanelData() {
    chrome.storage.local.get(
        ['veterans-data-list', 'veterans-saved-email', 'veterans-is-running'],
        (result) => {
            const startBtn = document.getElementById('veterans-start-btn');
            const stopBtn = document.getElementById('veterans-stop-btn');
            
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
                    
                    // Enable nút START nếu có data và không đang chạy
                    if (startBtn) {
                        if (validData.length > 0 && !result['veterans-is-running']) {
                            startBtn.disabled = false;
                        } else {
                            startBtn.disabled = true;
                        }
                    }
                } else {
                    // Không có data hợp lệ, disable nút START
                    if (startBtn) startBtn.disabled = true;
                    updateUIPanelStatus('⚠️ Please load data file first', 'info');
                }
            } else {
                // Không có data, disable nút START và yêu cầu load file
                if (startBtn) startBtn.disabled = true;
                updateUIPanelStatus('⚠️ Please load data file first', 'info');
            }
            
            // Update email
            if (result['veterans-saved-email']) {
                const emailInput = document.getElementById('veterans-email-input');
                if (emailInput) {
                    emailInput.value = result['veterans-saved-email'];
                }
                currentEmail = result['veterans-saved-email'];
            }
            
            // Update button states
            const skipBtn = document.getElementById('veterans-skip-btn');
            if (result['veterans-is-running']) {
                // Nút START và STOP luôn hiển thị, chỉ disable/enable
                if (startBtn) startBtn.disabled = true;
                if (stopBtn) stopBtn.disabled = false;
                // Disable SKIP khi tool đang running
                if (skipBtn) {
                    skipBtn.style.display = 'block';
                    skipBtn.disabled = true;
                }
            } else {
                if (stopBtn) stopBtn.disabled = true;
                // Enable SKIP khi tool stop
                if (skipBtn) {
                    skipBtn.style.display = 'block';
                    skipBtn.disabled = false;
                }
                // Enable nút START nếu có data và tool không chạy
                if (startBtn && result['veterans-data-list']) {
                    const dataLines = result['veterans-data-list'].split('\n').filter((line) => line.trim());
                    const validData = dataLines.filter((line) => {
                        const parts = line.trim().split('|');
                        return parts.length === 6;
                    });
                    startBtn.disabled = validData.length === 0;
                } else if (startBtn) {
                    startBtn.disabled = true;
                }
            }
        }
    );
}

// Initialize UI panel when page loads (handles page reload)
(function() {
    let initAttempts = 0;
    const maxAttempts = 50; // Max 5 seconds (50 * 100ms)
    
    function initPanelWhenReady() {
        initAttempts++;
        
        if (document.body && document.head) {
            try {
                initUIPanel();
                
                // Load saved email if exists
                chrome.storage.local.get(['veterans-saved-email'], (result) => {
                    if (result['veterans-saved-email']) {
                        currentEmail = result['veterans-saved-email'];
                        const emailEl = document.getElementById('veterans-panel-email');
                        const emailInput = document.getElementById('veterans-email-input');
                        if (emailEl) emailEl.textContent = currentEmail;
                        if (emailInput) emailInput.value = currentEmail;
                    }
                });
                
                // Restore verification state if running
                chrome.storage.local.get(['veterans-is-running', 'veterans-data-array', 'veterans-stats'], (result) => {
                    if (result['veterans-is-running'] && result['veterans-data-array']) {
                        dataArray = result['veterans-data-array'];
                        if (result['veterans-stats']) {
                            stats = result['veterans-stats'];
                        }
                        
                        // Update UI to show stop button
                        const startBtn = document.getElementById('veterans-start-btn');
                        const stopBtn = document.getElementById('veterans-stop-btn');
                        const skipBtn = document.getElementById('veterans-skip-btn');
                        // Nút START và STOP luôn hiển thị, chỉ disable/enable
                        if (startBtn) startBtn.disabled = true;
                        if (stopBtn) stopBtn.disabled = false;
                        // Disable SKIP khi tool đang running
                        if (skipBtn) {
                            skipBtn.style.display = 'block';
                            skipBtn.disabled = true;
                        }
                        
                        // Update panel stats
                        updateUIPanel();
                    }
                });
                
                console.log('✅ UI Panel initialized successfully');
            } catch (error) {
                console.error('❌ Error initializing UI panel:', error);
                if (initAttempts < maxAttempts) {
                    setTimeout(initPanelWhenReady, 100);
                }
            }
        } else if (initAttempts < maxAttempts) {
            setTimeout(initPanelWhenReady, 100);
        } else {
            console.error('❌ Failed to initialize UI panel: document.body not ready');
        }
    }
    
    // Try to initialize immediately if page is already loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(initPanelWhenReady, 100);
        });
    } else {
        // Page already loaded, wait a bit for everything to settle
        setTimeout(initPanelWhenReady, 300);
    }
    
    // Also listen for page visibility changes (handles tab switching/reload)
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            // Re-check if panel exists, reinitialize if needed
            if (!document.getElementById('veterans-extension-panel')) {
                setTimeout(initPanelWhenReady, 200);
            } else {
                // Panel exists, just update it
                updateUIPanel();
                loadPanelData();
            }
        }
    });
})();
