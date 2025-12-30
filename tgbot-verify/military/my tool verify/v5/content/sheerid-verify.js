// SheerID Verification Status Detection Content Script
// Monitors the page for verification results and reports back

console.log('[SheerID Verify] Status detection script loaded');

let checkInterval = null;
let checkCount = 0;
const MAX_CHECKS = 60; // 60 seconds max wait

// Start monitoring when page loads
window.addEventListener('load', () => {
    setTimeout(startMonitoring, 2000);
});

function startMonitoring() {
    console.log('[SheerID Verify] Starting status monitoring...');

    // Check immediately
    checkStatus();

    // Then check every second
    checkInterval = setInterval(() => {
        checkCount++;
        checkStatus();

        if (checkCount >= MAX_CHECKS) {
            console.log('[SheerID Verify] Timeout - stopping checks');
            stopMonitoring();
            reportResult('timeout', 'Verification timeout');
        }
    }, 1000);
}

function stopMonitoring() {
    if (checkInterval) {
        clearInterval(checkInterval);
        checkInterval = null;
    }
}

function checkStatus() {
    const html = document.documentElement.innerHTML.toLowerCase();
    const bodyText = document.body?.innerText?.toLowerCase() || '';

    // === CHECK FOR VERIFIED / SUCCESS ===
    const verifiedPatterns = [
        /you['']?ve\s+been\s+verified/i,
        /verification\s+(is\s+)?complete/i,
        /successfully\s+verified/i,
        /status.*verified/i,
        /sid-success/i,
        /verification-success/i,
        /thank\s+you.*verified/i
    ];

    for (const pattern of verifiedPatterns) {
        if (pattern.test(bodyText) || pattern.test(html)) {
            console.log('[SheerID Verify] VERIFIED detected!');
            stopMonitoring();
            reportResult('verified', 'Verification successful');
            return;
        }
    }

    // === CHECK FOR NOT APPROVED ===
    const notApprovedPatterns = [
        /not\s+approved/i,
        /could\s+not\s+be\s+verified/i,
        /unable\s+to\s+verify/i,
        /verification\s+failed/i,
        /not\s+eligible/i,
        /sid-error/i,
        /verification-error/i,
        /sorry.*cannot\s+verify/i
    ];

    for (const pattern of notApprovedPatterns) {
        if (pattern.test(bodyText) || pattern.test(html)) {
            console.log('[SheerID Verify] NOT APPROVED detected!');
            stopMonitoring();

            // Try to click OK/Close button
            tryClickOkButton();

            reportResult('not_approved', 'Not approved');
            return;
        }
    }

    // === CHECK FOR PENDING / EMAIL REQUIRED ===
    const pendingPatterns = [
        /check\s+your\s+email/i,
        /email\s+has\s+been\s+sent/i,
        /verify\s+your\s+email/i,
        /pending\s+verification/i,
        /processing/i,
        /please\s+wait/i
    ];

    for (const pattern of pendingPatterns) {
        if (pattern.test(bodyText) || pattern.test(html)) {
            console.log('[SheerID Verify] PENDING/EMAIL detected');
            stopMonitoring();
            reportResult('pending', 'Email verification required');
            return;
        }
    }

    // === CHECK FOR CONNECTION/VPN ERRORS ===
    const errorPatterns = [
        /connection\s+error/i,
        /network\s+error/i,
        /403/i,
        /blocked/i,
        /access\s+denied/i,
        /too\s+many\s+requests/i,
        /rate\s+limit/i,
        /service\s+unavailable/i
    ];

    for (const pattern of errorPatterns) {
        if (pattern.test(bodyText) || pattern.test(html)) {
            console.log('[SheerID Verify] ERROR detected');
            stopMonitoring();
            reportResult('error', 'Connection/VPN error');
            return;
        }
    }

    // Still loading or form visible - continue waiting
    // console.log('[SheerID Verify] No result yet, continuing...');
}

// Try to click OK/Close/Continue button after Not Approved
function tryClickOkButton() {
    const buttonTexts = ['ok', 'close', 'continue', 'try again', 'got it', 'dismiss'];
    const buttons = document.querySelectorAll('button, a[role="button"], div[role="button"]');

    for (const btn of buttons) {
        const text = btn.textContent?.toLowerCase().trim();
        if (buttonTexts.some(t => text?.includes(t))) {
            console.log('[SheerID Verify] Clicking button:', btn.textContent);
            setTimeout(() => btn.click(), 500);
            return true;
        }
    }

    // Also try to close any modal
    const closeButtons = document.querySelectorAll('[aria-label="close"], [aria-label="Close"], .close-button, .modal-close');
    for (const btn of closeButtons) {
        console.log('[SheerID Verify] Clicking close button');
        setTimeout(() => btn.click(), 500);
        return true;
    }

    return false;
}

// Report result to background script
function reportResult(status, message) {
    console.log(`[SheerID Verify] Reporting: ${status} - ${message}`);

    chrome.runtime.sendMessage({
        type: 'VERIFY_RESULT',
        result: {
            status: status,
            message: message,
            url: window.location.href,
            timestamp: Date.now()
        }
    }).catch(err => {
        console.log('[SheerID Verify] Could not send message:', err);
    });
}

// Also listen for manual trigger
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'CHECK_STATUS') {
        checkStatus();
    }
});
