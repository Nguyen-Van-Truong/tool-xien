// Background Service Worker - Main logic for auto-verification
// Uses SheerID API directly like Python tools (v1.1/v4)

// State management
let state = {
    isRunning: false,
    attempts: 0,
    success: 0,
    failed: 0,
    statusText: 'Ready',
    hasError: false,
    logs: []
};

// SheerID API Base URL
const SHEERID_BASE_URL = "https://services.sheerid.com/rest/v2/verification";

// Email API for auto-polling verify links
const EMAIL_API_URL = "https://tools.dongvanfb.net/api/get_messages_oauth2";

// Branch ID mapping (same as v1.1 Python tool)
const ORGANIZATIONS = {
    "Army": { id: 4070, name: "Army" },
    "Navy": { id: 4072, name: "Navy" },
    "Air Force": { id: 4073, name: "Air Force" },
    "Marine Corps": { id: 4071, name: "Marine Corps" },
    "Coast Guard": { id: 4074, name: "Coast Guard" }
};

// Month name to number
const MONTH_TO_NUM = {
    "January": "01", "February": "02", "March": "03", "April": "04",
    "May": "05", "June": "06", "July": "07", "August": "08",
    "September": "09", "October": "10", "November": "11", "December": "12"
};

// Initialize
chrome.runtime.onInstalled.addListener(() => {
    console.log('Military Auto Verify V3 - Side Panel Mode installed');
    saveState();

    // Enable side panel
    chrome.sidePanel.setOptions({
        enabled: true
    });
});

// Open side panel when extension icon is clicked
chrome.action.onClicked.addListener((tab) => {
    chrome.sidePanel.open({ windowId: tab.windowId });
});

// Listen for messages
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    switch (message.type) {
        case 'START_VERIFY':
            startVerification();
            break;
        case 'STOP_VERIFY':
            stopVerification();
            break;
        case 'SKIP_VETERAN':
            skipAndNext();
            break;
        case 'VETERANS_LOADED':
            log(`Loaded ${message.count} veterans`, 'success');
            break;
        case 'GET_STATE':
            // Return current state when popup opens
            sendResponse({ state, logs: state.logs });
            break;
        case 'GET_LOGS':
            // Return all logs
            sendResponse({ logs: state.logs });
            break;
    }
    return true;
});

// ===================== MAIN VERIFICATION =====================

async function startVerification() {
    state.isRunning = true;
    state.hasError = false;
    state.statusText = 'Starting...';
    saveState();
    broadcastState();

    // Get data
    const result = await chrome.storage.local.get(['veterans', 'currentIndex', 'sheeridLink', 'verifyEmail']);

    if (!result.veterans || result.veterans.length === 0) {
        log('No veterans data! Please import first.', 'error');
        state.hasError = true;
        state.isRunning = false;
        state.statusText = 'No data';
        saveState();
        broadcastState();
        return;
    }

    const sheeridLink = result.sheeridLink;
    const email = result.verifyEmail;

    // Try to get verification ID
    let verificationId = null;

    // First, try from saved link
    if (sheeridLink) {
        verificationId = extractVerificationId(sheeridLink);
        if (verificationId) {
            log(`Using saved link, verificationId: ${verificationId}`, 'info');
        }
    }

    // If no verificationId from link, try to find from open tabs
    if (!verificationId) {
        log('No valid link, searching for SheerID tab...', 'info');
        const sheerIdTab = await findSheerIdTab();

        if (sheerIdTab && sheerIdTab.verificationId) {
            verificationId = sheerIdTab.verificationId;
            log(`Auto-detected from tab: ${verificationId}`, 'success');
            // Save for next time
            await chrome.storage.local.set({ sheeridLink: sheerIdTab.url });
        } else if (sheerIdTab) {
            log('Found SheerID tab but no verificationId param. Click verify link on ChatGPT first!', 'error');
            state.hasError = true;
            state.isRunning = false;
            state.statusText = 'No verificationId in tab';
            saveState();
            broadcastState();
            return;
        } else {
            log('No SheerID tab found. Paste link or open verify page first!', 'error');
            state.hasError = true;
            state.isRunning = false;
            state.statusText = 'No SheerID link';
            saveState();
            broadcastState();
            return;
        }
    }

    if (!email) {
        log('Please enter email!', 'error');
        state.hasError = true;
        state.isRunning = false;
        state.statusText = 'No email';
        saveState();
        broadcastState();
        return;
    }

    const currentIndex = result.currentIndex || 0;
    const currentVet = result.veterans[currentIndex];

    log(`Starting verification for: ${currentVet.firstName} ${currentVet.lastName}`, 'info');
    log(`Verification ID: ${verificationId}`, 'info');

    state.statusText = `Verifying ${currentVet.firstName}...`;
    saveState();
    broadcastState();

    // Run verification
    await doVerification(verificationId, email, currentVet);
}

// Extract verification ID from SheerID link
// IMPORTANT: Query param ?verificationId= takes priority over path ID
function extractVerificationId(link) {
    // Priority 1: Query parameter ?verificationId=xxx (this is the REAL verification ID)
    const queryMatch = link.match(/verificationId=([a-f0-9]+)/i);
    if (queryMatch) {
        return queryMatch[1];
    }

    // Priority 2: Path format /verify/xxx (only if no query param)
    // Note: This may be program ID, not verification ID
    const pathPatterns = [
        /\/verify\/([a-f0-9]{24})/i,
        /\/([a-f0-9]{24})(?:\/|$|\?)/i
    ];

    for (const pattern of pathPatterns) {
        const match = link.match(pattern);
        if (match) {
            return match[1];
        }
    }
    return null;
}

// Auto-detect SheerID tab and get verification ID
async function findSheerIdTab() {
    try {
        const tabs = await chrome.tabs.query({ url: "*://services.sheerid.com/*" });
        for (const tab of tabs) {
            if (tab.url && tab.url.includes('verificationId=')) {
                const verificationId = extractVerificationId(tab.url);
                if (verificationId) {
                    log(`Found SheerID tab: ${tab.url.substring(0, 80)}...`, 'info');
                    return { tabId: tab.id, verificationId, url: tab.url };
                }
            }
        }

        // Also check for sheerid.com without query param
        for (const tab of tabs) {
            if (tab.url && tab.url.includes('/verify/')) {
                log(`Found SheerID tab (no verificationId param): ${tab.url.substring(0, 80)}...`, 'warning');
                return { tabId: tab.id, verificationId: null, url: tab.url };
            }
        }
    } catch (e) {
        log(`Error finding SheerID tab: ${e.message}`, 'error');
    }
    return null;
}

// Main verification process (like Python do_verification)
async function doVerification(verificationId, email, vet) {
    try {
        state.attempts++;

        // ===== STEP 1: collectMilitaryStatus =====
        log('Step 1: Checking military status...', 'info');
        const step1Result = await step1MilitaryStatus(verificationId);

        if (!step1Result) {
            log('❌ Step 1 FAILED! Check SheerID link.', 'error');
            onStep1Fail();
            return;
        }

        const currentStep = step1Result.currentStep || '';
        log(`✅ Step 1 OK - Next: ${currentStep}`, 'success');

        // ===== STEP 2: collectInactiveMilitaryPersonalInfo =====
        if (currentStep === 'collectInactiveMilitaryPersonalInfo') {
            log('Step 2: Submitting personal info...', 'info');

            const submissionUrl = step1Result.submissionUrl;
            const step2Result = await step2PersonalInfo(verificationId, vet, email, submissionUrl);

            if (step2Result) {
                const finalStep = step2Result.currentStep || '';
                const errorIds = step2Result.errorIds || [];

                if (finalStep === 'success') {
                    log('✅ Step 2 OK - Status: success', 'success');
                    log('🎉 VERIFIED! Success!', 'success');
                    onVerifySuccess();
                } else if (finalStep === 'emailLoop') {
                    log('✅ Step 2 OK - Status: emailLoop', 'success');
                    log('📧 Email verification sent - check inbox!', 'info');
                    log('⚠️ CHECK EMAIL to get NEW verificationId!', 'warning');
                    // EmailLoop = success but need NEW link for next veteran
                    await onEmailLoop();
                } else if (finalStep === 'error' || errorIds.length > 0) {
                    // Handle specific errors
                    if (errorIds.includes('verificationLimitExceeded')) {
                        log('❌ RATE LIMIT! verificationLimitExceeded', 'error');
                        log('⚠️ Link này đã hết lượt verify - KHÔNG có email mới!', 'warning');
                        log('👉 Cần lấy link MỚI từ ChatGPT', 'warning');
                        onRateLimitError();
                    } else if (errorIds.includes('invalidStep')) {
                        log('❌ INVALID STEP! Link đã được sử dụng', 'error');
                        log('⚠️ Cần link MỚI - Check Email hoặc lấy từ ChatGPT', 'warning');
                        onVerifyFail();
                    } else {
                        const errorMsg = step2Result.systemErrorMessage || errorIds.join(', ') || finalStep;
                        log(`❌ Verification failed: ${errorMsg}`, 'error');
                        onVerifyFail();
                    }
                } else {
                    log(`⚠️ Unknown status: ${finalStep}`, 'warning');
                    onVerifyFail();
                }
            } else {
                log('❌ Step 2 FAILED!', 'error');
                onVerifyFail();
            }
        } else {
            log(`⚠️ Unexpected flow: ${currentStep}`, 'warning');
            onVerifyFail();
        }

    } catch (error) {
        log(`❌ Error: ${error.message}`, 'error');
        onVerifyFail();
    }
}

// Step 1: POST to collectMilitaryStatus
async function step1MilitaryStatus(verificationId) {
    const url = `${SHEERID_BASE_URL}/${verificationId}/step/collectMilitaryStatus`;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: 'VETERAN' })
        });

        log(`   Step 1 Response: ${response.status}`, 'info');

        if (response.ok) {
            return await response.json();
        } else {
            const errorText = await response.text();
            log(`   Error: ${errorText.substring(0, 200)}`, 'error');
        }
    } catch (error) {
        log(`   Step 1 Exception: ${error.message}`, 'error');
    }

    return null;
}

// Step 2: POST to collectInactiveMilitaryPersonalInfo
async function step2PersonalInfo(verificationId, vet, email, submissionUrl) {
    const url = submissionUrl || `${SHEERID_BASE_URL}/${verificationId}/step/collectInactiveMilitaryPersonalInfo`;

    // Get organization
    const branch = vet.branch || 'Navy';
    const org = ORGANIZATIONS[branch] || ORGANIZATIONS['Navy'];

    // Format birth date
    const birthDate = formatDate(vet.birthYear, vet.birthMonth, vet.birthDay);

    // Discharge date - use Dec 1, 2025 if not 2025
    let dischargeDate;
    if (vet.dischargeYear === '2025') {
        dischargeDate = formatDate(vet.dischargeYear, vet.dischargeMonth, vet.dischargeDay);
    } else {
        dischargeDate = '2025-12-01';
        log(`   📅 Using discharge: Dec 1, 2025 (original: ${vet.dischargeYear})`, 'info');
    }

    const payload = {
        firstName: vet.firstName,
        lastName: vet.lastName,
        birthDate: birthDate,
        email: email,
        organization: org,
        dischargeDate: dischargeDate,
        metadata: {}
    };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        log(`   Step 2 Response: ${response.status}`, 'info');

        if (response.ok) {
            return await response.json();
        } else {
            const errorText = await response.text();
            log(`   Error: ${errorText.substring(0, 200)}`, 'error');
        }
    } catch (error) {
        log(`   Step 2 Exception: ${error.message}`, 'error');
    }

    return null;
}

// Format date to YYYY-MM-DD
function formatDate(year, month, day) {
    const monthNum = MONTH_TO_NUM[month] || '01';
    const dayPadded = String(day).padStart(2, '0');
    return `${year}-${monthNum}-${dayPadded}`;
}

// ===================== RESULT HANDLERS =====================

async function onVerifySuccess() {
    state.success++;
    state.statusText = '✅ Verified - Stopped';
    log('='.repeat(40), 'info');

    // Remove current veteran and move to next
    await removeCurrentAndNext();

    // Show notification
    chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icons/icon128.png',
        title: 'Verification Success!',
        message: 'Military status verified!'
    });

    // ALWAYS STOP - no auto-continue
    state.isRunning = false;

    // Show latest email details
    await showLatestEmailDetails();

    saveState();
    broadcastState();
}

// EmailLoop = success but verificationId is now used up
// Auto-poll email API to get NEW verificationId
async function onEmailLoop() {
    state.success++;
    state.statusText = '📧 Polling for new email...';
    log('='.repeat(40), 'info');

    // Remove current veteran
    await removeCurrentAndNext();

    // SAVE old verificationId for comparison
    const storageOld = await chrome.storage.local.get(['sheeridLink']);
    const oldVerificationId = storageOld.sheeridLink ? extractVerificationId(storageOld.sheeridLink) : null;
    log(`🔄 Old verificationId: ${oldVerificationId || 'none'}`, 'info');

    // CLEAR saved sheeridLink
    await chrome.storage.local.remove(['sheeridLink']);
    log('🔄 Cleared saved link', 'info');

    saveState();
    broadcastState();

    // Get email account from storage
    const storage = await chrome.storage.local.get(['emailAccount', 'debugMode']);
    const accountStr = storage.emailAccount;

    if (!accountStr) {
        log('⚠️ No email account configured - manual check needed', 'warning');
        state.isRunning = false;
        state.statusText = '📧 Need email account for auto-poll';
        saveState();
        broadcastState();
        return;
    }

    // Parse account: email|password|refresh_token|client_id
    const parts = accountStr.split('|');
    if (parts.length < 4) {
        log('⚠️ Invalid email account format', 'error');
        state.isRunning = false;
        saveState();
        broadcastState();
        return;
    }

    const [userEmail, password, refreshToken, clientId] = parts;

    // Get current email count for comparison
    log('📩 Getting current email count...', 'info');
    const initialResult = await fetchEmails(userEmail, refreshToken, clientId);
    const initialCount = initialResult?.messages?.length || 0;
    log(`   Current emails: ${initialCount}`, 'info');

    // Poll for new email (max 5 attempts = 75 seconds)
    const maxAttempts = 5;
    const pollInterval = 15000; // 15 seconds

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        log(`⏳ Waiting 15s... (attempt ${attempt}/${maxAttempts})`, 'info');
        state.statusText = `📧 Waiting 15s... (${attempt}/${maxAttempts})`;
        saveState();
        broadcastState();

        await sleep(pollInterval);

        log(`📩 Checking for new email...`, 'info');
        const result = await fetchEmails(userEmail, refreshToken, clientId);

        if (!result || !result.messages) {
            log('   ❌ Failed to fetch emails', 'error');
            continue;
        }

        const currentCount = result.messages.length;
        log(`   Emails: ${currentCount} (was ${initialCount})`, 'info');

        // Look for NEW verify email
        const verifyLink = findVerifyLinkInEmails(result.messages, initialCount);

        if (verifyLink) {
            log(`✅ Found verify link!`, 'success');
            log(`   ${verifyLink.substring(0, 80)}...`, 'info');

            // Extract NEW verificationId from the link
            const newVerificationId = extractVerificationId(verifyLink);
            if (!newVerificationId) {
                log('⚠️ Could not extract verificationId from link', 'warning');
                continue;
            }
            log(`   verificationId: ${newVerificationId}`, 'info');

            // CHECK: Is this actually a NEW verificationId?
            if (oldVerificationId && newVerificationId === oldVerificationId) {
                log(`⚠️ Same as old verificationId - still waiting for new email...`, 'warning');
                continue; // Keep polling
            }

            log(`🆕 NEW verificationId confirmed!`, 'success');

            // Save new link
            await chrome.storage.local.set({ sheeridLink: verifyLink });

            // OPEN LINK IN BROWSER TAB to "click" it (activate verification)
            log('🌐 Opening verify link in browser...', 'info');
            const tab = await chrome.tabs.create({ url: verifyLink, active: false });

            // Wait for tab to load
            await sleep(3000);

            // Close the tab
            try {
                await chrome.tabs.remove(tab.id);
                log('   Tab closed', 'info');
            } catch (e) {
                // Tab might already be closed
            }

            // Check debug mode
            if (storage.debugMode) {
                log('🔧 Debug mode - stopping here', 'warning');
                state.isRunning = false;
                state.statusText = '✅ Got new link (debug)';
                saveState();
                broadcastState();
                return;
            }

            // Continue verification with NEW verificationId
            log('🚀 Continuing with new verificationId...', 'info');
            state.statusText = 'Starting next verification...';
            saveState();
            broadcastState();

            setTimeout(() => startVerification(), 1000);
            return;
        }
    }

    // Max attempts reached
    log('⚠️ Timeout waiting for new email', 'warning');
    state.isRunning = false;
    state.statusText = '⏰ Email timeout - click Check Email';
    saveState();
    broadcastState();

    chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icons/icon128.png',
        title: '⏰ Email Timeout',
        message: 'No new verify email after 75s. Click Check Email manually.'
    });
}

// Fetch emails from API
async function fetchEmails(userEmail, refreshToken, clientId) {
    try {
        const response = await fetch(EMAIL_API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: userEmail,
                refresh_token: refreshToken,
                client_id: clientId
            })
        });

        if (response.ok) {
            return await response.json();
        }
    } catch (e) {
        log(`   Email API error: ${e.message}`, 'error');
    }
    return null;
}

// Find verify link in emails (only from emails NEWER than initialCount)
function findVerifyLinkInEmails(messages, initialCount) {
    // Sort by date descending (newest first)
    const sortedMessages = [...messages].sort((a, b) => {
        const dateA = a.date || '';
        const dateB = b.date || '';
        return dateB.localeCompare(dateA);
    });

    // Check newest emails first (ones that weren't there before)
    const newEmails = sortedMessages.slice(0, Math.max(0, messages.length - initialCount + 3));

    for (const msg of newEmails) {
        // Get 'from' address - handle multiple formats
        let fromAddr = '';
        const fromField = msg.from;
        if (Array.isArray(fromField) && fromField.length > 0) {
            // Format: [{address: "email@example.com"}]
            fromAddr = fromField[0]?.address || fromField[0] || '';
        } else if (typeof fromField === 'string') {
            // Format: "email@example.com"
            fromAddr = fromField;
        }
        fromAddr = String(fromAddr).toLowerCase();

        const subject = (msg.subject || '').toLowerCase();

        // Debug log
        log(`   Checking email: ${fromAddr} - "${subject.substring(0, 40)}"`, 'info');

        // Match: from contains "sheerid" AND subject contains "verified" or "verify" or "openai"
        const isFromSheerID = fromAddr.includes('sheerid') || fromAddr.includes('verify@');
        const hasVerifySubject = subject.includes('verified') || subject.includes('verify') || subject.includes('openai');

        if (isFromSheerID && hasVerifySubject) {
            log(`   ✓ Match! Extracting link...`, 'success');

            // Get email body - check multiple fields
            const body = msg.message || msg.body || msg.snippet || msg.content || '';

            // Find SheerID link
            const linkMatch = body.match(/https:\/\/services\.sheerid\.com\/verify\/[^\s<>"'\]]+/);
            if (linkMatch) {
                // Clean up link (remove trailing punctuation)
                let link = linkMatch[0].replace(/[.,;:!?]+$/, '');
                log(`   🔗 Found: ${link.substring(0, 60)}...`, 'success');
                return link;
            } else {
                log(`   ⚠️ No link found in body (${body.length} chars)`, 'warning');
            }
        }
    }

    log(`   No SheerID verify email found in ${newEmails.length} emails`, 'warning');
    return null;
}

// Sleep helper
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Rate limit error - link is exhausted, no email will be sent
async function onRateLimitError() {
    state.failed++;
    state.statusText = '⚠️ Rate Limit - Need NEW link!';
    log('='.repeat(40), 'info');

    // DON'T remove veteran - not their fault
    // Keep current veteran for retry with new link

    // Clear old link
    await chrome.storage.local.remove(['sheeridLink']);
    log('🔄 Cleared old link', 'info');

    // STOP
    state.isRunning = false;

    // Show notification
    chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icons/icon128.png',
        title: '⚠️ Rate Limit Exceeded',
        message: 'Link đã hết lượt! Lấy link MỚI từ ChatGPT.'
    });

    saveState();
    broadcastState();
}

async function onVerifyFail() {
    state.failed++;
    state.statusText = '❌ Failed - Stopped';
    log('='.repeat(40), 'info');

    // Remove current veteran and move to next
    await removeCurrentAndNext();

    // ALWAYS STOP - no auto-continue
    state.isRunning = false;

    // Fetch and show latest email for debugging
    await showLatestEmailDetails();

    saveState();
    broadcastState();
}

// Show latest email details in log for debugging
async function showLatestEmailDetails() {
    const storage = await chrome.storage.local.get(['emailAccount']);
    const accountStr = storage.emailAccount;

    if (!accountStr) {
        log('📧 No email account - cannot check email', 'warning');
        return;
    }

    const parts = accountStr.split('|');
    if (parts.length < 4) return;

    const [userEmail, password, refreshToken, clientId] = parts;

    log('📧 Fetching latest email...', 'info');
    const result = await fetchEmails(userEmail, refreshToken, clientId);

    if (!result || !result.messages || result.messages.length === 0) {
        log('   No emails found', 'warning');
        return;
    }

    // Show latest 3 emails
    log(`   Total emails: ${result.messages.length}`, 'info');

    const sortedMessages = [...result.messages].sort((a, b) => {
        const dateA = a.date || '';
        const dateB = b.date || '';
        return dateB.localeCompare(dateA);
    });

    for (let i = 0; i < Math.min(3, sortedMessages.length); i++) {
        const msg = sortedMessages[i];

        // Parse 'from' - handle multiple formats
        let from = '';
        const fromField = msg.from;
        if (Array.isArray(fromField) && fromField.length > 0) {
            from = fromField[0]?.address || fromField[0] || '';
        } else if (typeof fromField === 'string') {
            from = fromField;
        }
        from = String(from);

        const subject = msg.subject || 'No subject';
        const date = msg.date || '';
        log(`   [${i + 1}] ${from} - ${subject.substring(0, 40)}...`, 'info');

        // If from SheerID, show link
        if (from.toLowerCase().includes('sheerid') || from.toLowerCase().includes('verify@')) {
            const body = msg.message || msg.body || msg.snippet || msg.content || '';
            const linkMatch = body.match(/https:\/\/services\.sheerid\.com\/verify\/[^\s<>"'\]]+/);
            if (linkMatch) {
                log(`       🔗 Link: ${linkMatch[0].substring(0, 60)}...`, 'success');
            }
        }
    }
}

function onStep1Fail() {
    // Step 1 fail = link issue, DON'T remove veteran
    state.hasError = true;
    state.isRunning = false;
    state.statusText = '❌ Step 1 failed - Check link!';
    log('⚠️ Step 1 failed - veteran data kept. Please check/update SheerID link.', 'warning');
    log('='.repeat(40), 'info');

    saveState();
    broadcastState();
}

// ===================== UTILITIES =====================

function stopVerification() {
    state.isRunning = false;
    state.statusText = 'Stopped';
    log('Stopped by user', 'info');
    saveState();
    broadcastState();
}

async function skipAndNext() {
    const result = await chrome.storage.local.get(['veterans', 'currentIndex']);
    if (!result.veterans || result.veterans.length === 0) return;

    const veterans = result.veterans;
    const currentIndex = result.currentIndex || 0;

    const removed = veterans.splice(currentIndex, 1);
    log(`Skipped: ${removed[0]?.firstName || 'Unknown'}`, 'info');

    let newIndex = currentIndex;
    if (newIndex >= veterans.length) newIndex = 0;

    await chrome.storage.local.set({ veterans, currentIndex: newIndex });
    saveState();
    broadcastState();
}

async function removeCurrentAndNext() {
    const result = await chrome.storage.local.get(['veterans', 'currentIndex']);
    if (!result.veterans || result.veterans.length === 0) return;

    const veterans = result.veterans;
    const currentIndex = result.currentIndex || 0;

    // Remove current
    const removed = veterans.splice(currentIndex, 1);
    log(`Removed: ${removed[0]?.firstName || 'Unknown'}`, 'info');

    // Update index
    let newIndex = currentIndex;
    if (newIndex >= veterans.length) newIndex = 0;

    await chrome.storage.local.set({ veterans, currentIndex: newIndex });

    if (veterans.length === 0) {
        log('All veterans processed!', 'success');
        state.isRunning = false;
        state.statusText = 'All done!';
    }
}

function log(text, level = 'info') {
    const logEntry = { text, level, time: Date.now() };
    state.logs.push(logEntry);

    if (state.logs.length > 50) {
        state.logs = state.logs.slice(-50);
    }

    chrome.runtime.sendMessage({ type: 'LOG', text, level }).catch(() => { });
    console.log(`[${level.toUpperCase()}] ${text}`);
}

function saveState() {
    chrome.storage.local.set({ verifyState: state });
}

function broadcastState() {
    chrome.runtime.sendMessage({ type: 'STATE_UPDATE', state }).catch(() => { });
}

// Load state on startup
chrome.storage.local.get(['verifyState'], (result) => {
    if (result.verifyState) {
        state = { ...state, ...result.verifyState, isRunning: false };
    }
});
