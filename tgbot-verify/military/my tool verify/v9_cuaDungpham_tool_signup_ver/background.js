// Background service worker
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'updateStatus' || message.action === 'updateStats' || message.action === 'updatePanel') {
        // Messages will be handled via storage changes in side panel
        // No need to forward since side panel listens to storage changes
    } else if (message.action === 'clearCookies') {
        // Clear cookies for ChatGPT and SheerID for multi-account switching
        (async () => {
            try {
                const allCookies = await chrome.cookies.getAll({});
                const cookiesToDelete = allCookies.filter(cookie => {
                    return cookie.domain.includes('chatgpt.com') ||
                        cookie.domain.includes('sheerid.com') ||
                        cookie.domain.includes('openai.com');
                });

                let deletedCount = 0;
                for (const cookie of cookiesToDelete) {
                    try {
                        const protocol = cookie.secure ? 'https' : 'http';
                        const domain = cookie.domain.startsWith('.') ? cookie.domain.substring(1) : cookie.domain;
                        const url = `${protocol}://${domain}${cookie.path || '/'}`;

                        await chrome.cookies.remove({
                            url: url,
                            name: cookie.name
                        });
                        deletedCount++;
                    } catch (e) {
                        console.log('Error deleting cookie:', e);
                    }
                }

                console.log(`✅ Cleared ${deletedCount} cookies for multi-account switch`);
                sendResponse({ success: true, deletedCount });
            } catch (error) {
                console.error('Error clearing cookies:', error);
                sendResponse({ success: false, error: error.message });
            }
        })();
        return true; // Keep channel open for async response
    }
    return true;
});

// Open side panel when extension icon is clicked (only for current tab's window)
chrome.action.onClicked.addListener(async (tab) => {
    try {
        // Only open side panel for the current tab's window
        await chrome.sidePanel.open({ windowId: tab.windowId });
    } catch (error) {
        console.error('Error opening side panel:', error);
    }
});

