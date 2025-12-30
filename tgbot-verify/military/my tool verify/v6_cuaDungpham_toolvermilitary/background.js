// Background service worker
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'updateStatus' || message.action === 'updateStats' || message.action === 'updatePanel') {
        // Messages will be handled via storage changes in side panel
        // No need to forward since side panel listens to storage changes
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

