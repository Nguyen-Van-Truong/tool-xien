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

// Listen for messages from side panel
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

        // UI is now handled by side panel, no need to update inline panel

        console.log(
            '💾 Saving data to storage, array length:',
            dataArray.length
        );

        // Rebuild data list string for storage
        const dataListString = dataArray
            .map((data) => data.original)
            .join('\n');

        // Use lock mechanism to prevent race condition
        chrome.storage.local.get(
            ['veterans-data-lock'],
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

                // Always start from index 0 when user clicks START
                currentDataIndex = 0;
                console.log('🚀 Starting verification from index 0');

                // Set lock (simplified, no need for active-instances tracking)
                chrome.storage.local.set(
                    {
                        'veterans-data-lock': true
                    },
                    () => {
                        // Save state to storage
                        // Always start from index 0 when user clicks START
                        chrome.storage.local.set(
                            {
                                'veterans-data-array': dataArray,
                                'veterans-data-list': dataListString,
                                'veterans-current-index': 0,
                                'veterans-is-running': true,
                                'veterans-stats': { processed: 0, success: 0, failed: 0 }
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

        // UI is now handled by side panel, no need to update inline panel

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
        
        sendStatus('✅ All data processed', 'success');
        return;
    }

    const currentData = dataArray[currentDataIndex];
    mailRetryCount = 0; // Reset mail retry count for new data
    currentEmail = ''; // Reset email for new data (will be auto-generated)
    
    // Calculate the correct position: stats.processed is the number already processed
    // So the current one is stats.processed + 1
    // We need the original total count, which is stats.processed + dataArray.length (remaining)
    const originalTotal = stats.processed + dataArray.length;
    const currentPosition = stats.processed + 1;
    
    sendStatus(
        `🔄 Processing ${currentPosition}/${originalTotal}: ${
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
            
            
            return;
        }

        if (currentUrl.includes('chatgpt.com/veterans-claim')) {
            // Step 1: Click verify button
            console.log('🔍 On ChatGPT page, clicking verify button...');
            // Calculate the correct position
            const originalTotal = stats.processed + dataArray.length;
            const currentPosition = stats.processed + 1;
            
            console.log(
                `📊 Current data index: ${currentPosition}/${originalTotal}`
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
        
        // Extract error message
        let errorMessage = 'Unknown error';
        if (error) {
            if (typeof error === 'string') {
                errorMessage = error;
            } else if (error.message) {
                errorMessage = error.message;
            } else {
                errorMessage = String(error);
            }
        }
        
        // Check if it's a Status-related error (CRITICAL - must stop)
        const isStatusError = errorMessage.toLowerCase().includes('status') || 
                             errorMessage.toLowerCase().includes('không tìm thấy') ||
                             (error && error.name && (
                                 error.name === 'StatusMenuNotFound' ||
                                 error.name === 'StatusButtonNotFound' ||
                                 error.name === 'StatusItemNotFound'
                             ));
        
        // Status errors are critical - stop tool immediately (don't retry)
        if (isStatusError) {
            console.log('🚫 Critical Status error detected in verification loop, stopping tool...');
            // Ensure status message is sent with proper format
            const finalStatusMsg = errorMessage.toLowerCase().includes('❌') 
                ? errorMessage 
                : '❌ Lỗi nghiêm trọng: ' + errorMessage;
            sendStatus(finalStatusMsg, 'error');
            // Small delay to ensure status message is saved
            await delay(100);
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            return; // Exit completely - don't retry
        }
        
        // For other errors, stop tool - DO NOT change data
        sendStatus('❌ Error: ' + errorMessage, 'error');
        // CRITICAL ERROR - Stop tool without changing data
        isRunning = false;
        chrome.storage.local.set({ 'veterans-is-running': false });
        updateUIOnStop();
        return; // Exit completely - don't change data
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

        // Save to chrome.storage.local for side panel
        chrome.storage.local.set({ 'veterans-saved-email': email });

        sendStatus('✅ Email generated: ' + email, 'success');
    } catch (error) {
        console.error('Error generating email:', error);
        const errorMsg = error && error.message ? error.message : 'Unknown error';
        sendStatus('❌ Failed to generate email: ' + errorMsg, 'error');
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

                return;
            }

            // Only change data for "Not approved", not for Verification Limit Exceeded
            if (errorText.includes('Not approved')) {
                console.log('❌ Not approved detected, moving to next data...');
                sendStatus('❌ Verification failed: Not approved', 'error');

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

                // Calculate the correct position: stats.processed is the number already processed
                // So the next one is stats.processed + 1
                // We need the original total count, which is stats.processed + dataArray.length (remaining)
                const originalTotal = stats.processed + dataArray.length;
                const nextPosition = stats.processed + 1;
                
                console.log(
                    `🔄 Moving to next data: ${nextPosition}/${originalTotal}`
                );
                sendStatus(
                    `🔄 Trying next data: ${nextPosition}/${originalTotal}`,
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

                return;
            }

            // Only change data for "Not approved", not for Verification Limit Exceeded
            if (bodyText.includes('Not approved')) {
                console.log('❌ Not approved detected in body text, moving to next data...');
                sendStatus('❌ Verification failed: Not approved', 'error');

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

                // Calculate the correct position: stats.processed is the number already processed
                // So the next one is stats.processed + 1
                // We need the original total count, which is stats.processed + dataArray.length (remaining)
                const originalTotal = stats.processed + dataArray.length;
                const nextPosition = stats.processed + 1;
                
                console.log(
                    `🔄 Moving to next data: ${nextPosition}/${originalTotal}`
                );
                sendStatus(
                    `🔄 Trying next data: ${nextPosition}/${originalTotal}`,
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
                // FORCE STOP first - ngừng toàn bộ hoạt động tool
                isRunning = false;
                chrome.storage.local.set({ 'veterans-is-running': false });
                
                // Remove processed data (pass false to keepRunning so it doesn't set is-running back to true)
                removeProcessedData(false);
                stats.processed++;
                stats.success++;
                updateStats();
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


            return;
        } else if (
            headingText.includes('Error') ||
            headingText.includes('Verification Limit Exceeded') ||
            headingText.includes('verification limit exceeded') ||
            headingText.includes('limit exceeded')
        ) {
            // DO NOT change data for these errors - stop tool
            const errorType =
                headingText.includes('Verification Limit Exceeded') ||
                headingText.includes('limit exceeded')
                    ? 'Verification Limit Exceeded'
                    : 'Error';
            console.log(`❌ ${errorType} detected, stopping tool...`);
            sendStatus(`❌ Verification failed: ${errorType}`, 'error');
            // Stop tool without changing data
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            return;
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
        
        // Extract error message properly
        let errorMessage = 'Unknown error';
        if (error) {
            if (typeof error === 'string') {
                errorMessage = error;
            } else if (error.message) {
                errorMessage = error.message;
            } else {
                errorMessage = String(error);
            }
        }
        
        // Check if it's a Status-related error (CRITICAL - must stop)
        const isStatusError = errorMessage.toLowerCase().includes('status') || 
                             errorMessage.toLowerCase().includes('không tìm thấy') ||
                             (error && error.name && (
                                 error.name === 'StatusMenuNotFound' ||
                                 error.name === 'StatusButtonNotFound' ||
                                 error.name === 'StatusItemNotFound'
                             ));
        
        // Status errors are critical - stop tool immediately
        if (isStatusError) {
            console.log('🚫 Critical Status error detected in checkAndFillForm, stopping tool...');
            // Ensure status message is sent before stopping
            if (!errorMessage.toLowerCase().includes('❌')) {
                // If error message doesn't already have error prefix, add it
                sendStatus('❌ ' + errorMessage, 'error');
            }
            // Small delay to ensure status message is saved
            await delay(100);
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            // Status message already sent, just return
            return;
        }
        
        // For other errors, add context and send status
        const errorMsg = `❌ Lỗi khi kiểm tra trang: ${errorMessage}`;
        sendStatus(errorMsg, 'error');
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
            // Timeout or element not found - CRITICAL ERROR
            const errorMsg = '❌ NOT FOUND STATUS MENU. Có thể trang chưa load xong hoặc form không tồn tại.';
            console.error(errorMsg, error);
            sendStatus(errorMsg, 'error');
            // CRITICAL ERROR - Stop tool
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            return null; // Return null to exit gracefully
        });
        
        // Check if tool was stopped due to critical error
        if (!isRunning || !statusButton) {
            if (!isRunning) {
                console.log('⏹️ Tool stopped due to error');
            }
            return;
        }
        
        // Check again before clicking
        if (!isRunning) {
            console.log('⏹️ Tool stopped, exiting fillForm');
            return;
        }
        
        // Check if status item already exists (menu might already be open)
        let statusItem = document.getElementById('sid-military-status-item-1');
        const menuAlreadyOpen = statusItem !== null && statusItem.offsetParent !== null;
        
        if (!menuAlreadyOpen) {
            // Menu is closed, need to click button to open it
            console.log('✅ Found status button, clicking to open menu...');
            statusButton.click();
            console.log('⏳ Waiting for status menu...');
            
            // Check again before waiting
            if (!isRunning) {
                console.log('⏹️ Tool stopped, exiting fillForm');
                return;
            }
            
            const statusMenuItem = await waitForElement('#sid-military-status-item-1', 10000).catch((error) => {
                if (error === 'Tool stopped') {
                    console.log('⏹️ Tool stopped during waitForElement');
                    return null;
                }
                // Timeout or element not found - CRITICAL ERROR - Stop tool
                const errorMsg = '❌ NOT FOUND STATUS MENU. Menu có thể không hiển thị hoặc trang chưa load xong.';
                console.error(errorMsg, error);
                sendStatus(errorMsg, 'error');
                isRunning = false;
                chrome.storage.local.set({ 'veterans-is-running': false });
                updateUIOnStop();
                return null; // Return null to exit gracefully
            });
            
            // Check if tool was stopped due to critical error
            if (!isRunning) {
                // Tool was stopped due to error
                return;
            }
            await delay(1000);
            statusItem = document.getElementById('sid-military-status-item-1');
        } else {
            console.log('✅ Status menu already open, skipping button click');
            await delay(500);
        }
        
        if (!statusItem) {
            const errorMsg = '❌ NOT FOUND STATUS MENU. Menu có thể chưa mở hoặc trang chưa load đầy đủ.';
            console.error(errorMsg);
            sendStatus(errorMsg, 'error');
            // CRITICAL ERROR - Stop tool
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            return;
        }
        
        // Check if status is already selected by checking button text or aria attributes
        const statusButtonText = statusButton.innerText || statusButton.textContent || '';
        const isAlreadySelected = statusButtonText.toLowerCase().includes('veteran') || 
                                  statusButtonText.toLowerCase().includes('retiree');
        
        if (!isAlreadySelected) {
            console.log('✅ Found status item, clicking...');
            statusItem.click();
            console.log('✅ Chọn status xong, đợi BRANCH reload...');
            await delay(3000); // Đợi 3s để BRANCH reload
        } else {
            console.log('✅ Status already selected, skipping click');
            await delay(3000); // Vẫn đợi 3s để đảm bảo BRANCH đã reload
        }

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
        
        // Extract error message
        let errorMessage = 'Unknown error';
        if (error) {
            if (typeof error === 'string') {
                errorMessage = error;
            } else if (error.message) {
                errorMessage = error.message;
            } else {
                errorMessage = String(error);
            }
        }
        
        // Check if it's a Status-related error (CRITICAL - must stop)
        const isStatusError = errorMessage.toLowerCase().includes('status') || 
                             errorMessage.toLowerCase().includes('không tìm thấy') ||
                             (error && error.name && (
                                 error.name === 'StatusMenuNotFound' ||
                                 error.name === 'StatusButtonNotFound' ||
                                 error.name === 'StatusItemNotFound'
                             ));
        
        // Status errors are critical - stop tool immediately
        if (isStatusError) {
            console.log('🚫 Critical Status error detected, stopping tool...');
            // Ensure status message is sent before stopping
            if (!errorMessage.toLowerCase().includes('❌')) {
                // If error message doesn't already have error prefix, add it
                sendStatus('❌ ' + errorMessage, 'error');
            }
            // Small delay to ensure status message is saved
            await delay(100);
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            return; // Exit without throwing - tool already stopped
        }
        
        // For other errors, add more context and send status, then throw
        sendStatus(`❌ Lỗi khi điền form: ${errorMessage}`, 'error');
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
                    '❌ Max retries reached for reading mail, stopping tool',
                    'error'
                );
                // DO NOT change data - stop tool
                mailRetryCount = 0;
                isRunning = false;
                chrome.storage.local.set({ 'veterans-is-running': false });
                updateUIOnStop();
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
                    '❌ Max retries reached, stopping tool',
                    'error'
                );
                // DO NOT change data - stop tool
                mailRetryCount = 0;
                isRunning = false;
                chrome.storage.local.set({ 'veterans-is-running': false });
                updateUIOnStop();
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
            sendStatus('❌ Max retries reached, stopping tool', 'error');
            // DO NOT change data - stop tool
            mailRetryCount = 0;
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
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
    // Save status to storage so side panel can listen for changes
    chrome.storage.local.set({
        'veterans-status': {
            message: message,
            type: type,
            timestamp: Date.now()
        }
    });
}

function updateStats() {
    // Save stats to storage
    chrome.storage.local.set({
        'veterans-stats': stats
    });
}

// Helper function to update UI when verification stops
// Note: UI is now handled by side panel, this function is kept for compatibility but does nothing
function updateUIOnStop() {
    // UI updates are handled by side panel via storage changes
}

function removeProcessedData(keepRunning = true) {
    // Remove the current data from array and update storage
    // keepRunning: if false, don't update 'veterans-is-running' (used when stopping after verified)
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
                setTimeout(() => removeProcessedData(keepRunning), 100);
                return;
            }

            // Set lock
            chrome.storage.local.set({ 'veterans-data-lock': true }, () => {
                // Prepare storage update object
                const storageUpdate = {
                    'veterans-data-array': dataArray,
                    'veterans-data-list': updatedDataList, // Save updated data list as string
                    'veterans-current-index': currentDataIndex // Keep same index since we removed one
                };
                
                // Only update 'veterans-is-running' if keepRunning is true
                if (keepRunning) {
                    storageUpdate['veterans-is-running'] = true;
                }
                
                // Update storage with new array and updated data list
                chrome.storage.local.set(
                    storageUpdate,
                    () => {
                        // Release lock after 500ms
                        setTimeout(() => {
                            chrome.storage.local.remove('veterans-data-lock');
                        }, 500);
                    }
                );
            });
        });

        console.log('🗑️ Removed processed data:', processedData.original);
        console.log('💾 Updated data list saved to storage');
    }
}
