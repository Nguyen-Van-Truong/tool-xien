// Content script for ChatGPT veterans-claim page
// Finds and clicks verify links

(function () {
    'use strict';

    console.log('[Military Verify] Content script loaded on ChatGPT');

    // Listen for messages from background
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.type === 'CLICK_VERIFY_LINK') {
            clickVerifyLink();
        }
        return true;
    });

    // Find and click verify link
    function clickVerifyLink() {
        console.log('[Military Verify] Searching for verify link...');

        // Look for links containing "sheerid" or "verify"
        const allLinks = document.querySelectorAll('a');
        let verifyLink = null;

        for (const link of allLinks) {
            const href = link.href || '';
            const text = link.textContent || '';

            // Check if it's a SheerID verify link
            if (href.includes('sheerid.com') ||
                href.includes('verify') ||
                text.toLowerCase().includes('verify') ||
                text.toLowerCase().includes('claim')) {
                verifyLink = link;
                break;
            }
        }

        // Also look for buttons
        if (!verifyLink) {
            const buttons = document.querySelectorAll('button');
            for (const btn of buttons) {
                const text = btn.textContent || '';
                if (text.toLowerCase().includes('verify') ||
                    text.toLowerCase().includes('claim') ||
                    text.toLowerCase().includes('get started')) {
                    verifyLink = btn;
                    break;
                }
            }
        }

        if (verifyLink) {
            console.log('[Military Verify] Found verify link:', verifyLink);

            // Notify background that we found and will click
            chrome.runtime.sendMessage({ type: 'LINK_CLICKED' });

            // Click the link
            verifyLink.click();

        } else {
            console.log('[Military Verify] No verify link found');

            // Maybe need to scroll or wait for dynamic content
            // Try again after a short delay
            setTimeout(() => {
                const retryLinks = findVerifyElements();
                if (retryLinks) {
                    chrome.runtime.sendMessage({ type: 'LINK_CLICKED' });
                    retryLinks.click();
                } else {
                    // Send error to background
                    chrome.runtime.sendMessage({
                        type: 'VPN_ERROR',
                        error: 'No verify link found on page. Please check the page or refresh.'
                    });
                }
            }, 2000);
        }
    }

    // Helper to find verify elements
    function findVerifyElements() {
        // More comprehensive search
        const selectors = [
            'a[href*="sheerid"]',
            'a[href*="verify"]',
            'button:contains("Verify")',
            '[data-testid*="verify"]',
            '.verify-button',
            '#verify-btn'
        ];

        for (const selector of selectors) {
            try {
                const el = document.querySelector(selector);
                if (el) return el;
            } catch (e) {
                // Selector might be invalid
            }
        }

        // Fallback: search all clickable elements
        const clickables = document.querySelectorAll('a, button, [role="button"]');
        for (const el of clickables) {
            const text = (el.textContent || '').toLowerCase();
            if (text.includes('verify') || text.includes('claim') || text.includes('military')) {
                return el;
            }
        }

        return null;
    }

    // Auto-detect if we should click (for auto-mode)
    function checkForAutoClick() {
        // Get state from storage
        chrome.storage.local.get(['verifyState'], (result) => {
            if (result.verifyState && result.verifyState.isRunning) {
                // Auto mode is on, click the link
                setTimeout(clickVerifyLink, 1500);
            }
        });
    }

    // Check on page load
    if (document.readyState === 'complete') {
        checkForAutoClick();
    } else {
        window.addEventListener('load', checkForAutoClick);
    }

})();
