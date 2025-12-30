// Background service worker for ChatGPT Auto Signup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'updateStatus' || message.action === 'updateStats' || message.action === 'updatePanel') {
        // Messages will be handled via storage changes in side panel
    }
    return true;
});

// Open side panel when extension icon is clicked
chrome.action.onClicked.addListener(async (tab) => {
    try {
        await chrome.sidePanel.open({ windowId: tab.windowId });
    } catch (error) {
        console.error('Error opening side panel:', error);
    }
});

