// Background service worker
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'getTabId') {
        // Return the sender's tab ID so content script can identify itself
        sendResponse({ tabId: sender.tab?.id });
        return false; // Sync response
    } else if (message.action === 'updateStatus' || message.action === 'updateStats' || message.action === 'updatePanel') {
        // Messages will be handled via storage changes in side panel
        // No need to forward since side panel listens to storage changes
    } else if (message.action === 'clearCookies') {
        // Clear ALL browsing data (cookies, localStorage, indexedDB, cache, etc.) for ChatGPT, OpenAI, and SheerID
        (async () => {
            try {
                // Origins to clear completely (including SheerID)
                const origins = [
                    'https://chatgpt.com',
                    'https://auth.openai.com',
                    'https://openai.com',
                    'https://auth0.openai.com',
                    'https://services.sheerid.com'
                ];

                // Data types to remove - this is the comprehensive list from Chrome docs
                const dataToRemove = {
                    cookies: true,
                    localStorage: true,
                    indexedDB: true,
                    cacheStorage: true,
                    serviceWorkers: true,
                    fileSystems: true,
                    webSQL: true
                };

                // Clear data for each origin
                for (const origin of origins) {
                    try {
                        await chrome.browsingData.remove(
                            { origins: [origin] },
                            dataToRemove
                        );
                        console.log(`✅ Cleared all data for ${origin}`);
                    } catch (e) {
                        console.log(`⚠️ Error clearing data for ${origin}:`, e.message || e);
                    }
                }

                // Also clear cache globally (since cache: true with origins doesn't work well)
                try {
                    await chrome.browsingData.removeCache({});
                    console.log('✅ Cleared global cache');
                } catch (e) {
                    console.log('⚠️ Could not clear global cache:', e.message || e);
                }

                // Double check: Also manually remove any remaining cookies using cookies API
                let deletedCookies = 0;
                try {
                    const allCookies = await chrome.cookies.getAll({});
                    const cookiesToDelete = allCookies.filter(cookie => {
                        return cookie.domain.includes('chatgpt.com') ||
                            cookie.domain.includes('openai.com') ||
                            cookie.domain.includes('auth.openai.com') ||
                            cookie.domain.includes('auth0.openai.com') ||
                            cookie.domain.includes('sheerid.com');
                    });

                    for (const cookie of cookiesToDelete) {
                        try {
                            // Try multiple URL formats to ensure deletion
                            const urls = [];
                            const domain = cookie.domain.startsWith('.') ? cookie.domain.substring(1) : cookie.domain;
                            urls.push(`https://${domain}${cookie.path || '/'}`);
                            urls.push(`https://${domain}/`);
                            if (cookie.domain.startsWith('.')) {
                                urls.push(`https://${cookie.domain.substring(1)}/`);
                            }

                            for (const url of urls) {
                                try {
                                    await chrome.cookies.remove({ url: url, name: cookie.name });
                                    deletedCookies++;
                                    console.log(`✅ Removed cookie: ${cookie.name} from ${url}`);
                                    break; // Success, no need to try other URLs
                                } catch (e) { /* try next URL */ }
                            }
                        } catch (e) { /* ignore */ }
                    }
                    console.log(`✅ Manually removed ${deletedCookies} remaining cookies`);
                } catch (e) { console.log('⚠️ Error in manual cookie removal:', e); }

                console.log('✅ All browsing data cleared successfully');
                sendResponse({ success: true, deletedCookies, message: 'Cleared all data for ChatGPT/OpenAI/SheerID' });
            } catch (error) {
                console.error('Error clearing data:', error);
                sendResponse({ success: false, error: error.message });
            }
        })();
        return true; // Keep channel open for async response
    } else if (message.action === 'clearSheerID') {
        // Clear ONLY SheerID data (cookies, localStorage, indexedDB, etc.)
        (async () => {
            try {
                // Origins to clear
                const origins = [
                    'https://services.sheerid.com',
                    'https://sheerid.com'
                ];

                // Data types to remove
                const dataToRemove = {
                    cookies: true,
                    localStorage: true,
                    indexedDB: true,
                    cacheStorage: true,
                    serviceWorkers: true,
                    fileSystems: true,
                    webSQL: true
                };

                // Clear data for each origin
                for (const origin of origins) {
                    try {
                        await chrome.browsingData.remove(
                            { origins: [origin] },
                            dataToRemove
                        );
                        console.log(`✅ Cleared all data for ${origin}`);
                    } catch (e) {
                        console.log(`⚠️ Error clearing data for ${origin}:`, e.message || e);
                    }
                }

                // Also manually remove SheerID cookies
                let deletedCookies = 0;
                try {
                    const allCookies = await chrome.cookies.getAll({});
                    const cookiesToDelete = allCookies.filter(cookie => {
                        return cookie.domain.includes('sheerid.com');
                    });

                    for (const cookie of cookiesToDelete) {
                        try {
                            const domain = cookie.domain.startsWith('.') ? cookie.domain.substring(1) : cookie.domain;
                            const url = `https://${domain}${cookie.path || '/'}`;
                            await chrome.cookies.remove({ url: url, name: cookie.name });
                            deletedCookies++;
                            console.log(`✅ Removed SheerID cookie: ${cookie.name}`);
                        } catch (e) { /* ignore */ }
                    }
                    console.log(`✅ Manually removed ${deletedCookies} SheerID cookies`);
                } catch (e) { console.log('⚠️ Error in SheerID cookie removal:', e); }

                console.log('✅ SheerID data cleared successfully');
                sendResponse({ success: true, deletedCookies, message: 'Cleared all SheerID data' });
            } catch (error) {
                console.error('Error clearing SheerID data:', error);
                sendResponse({ success: false, error: error.message });
            }
        })();
        return true; // Keep channel open for async response
    } else if (message.action === 'enableProxy') {
        // Enable HTTP proxy with authentication
        (async () => {
            try {
                const { host, port, username, password } = message.proxy;

                // Store credentials for auth handler
                await chrome.storage.local.set({
                    'proxy-auth-username': username,
                    'proxy-auth-password': password
                });

                // Set proxy configuration
                const config = {
                    mode: "fixed_servers",
                    rules: {
                        singleProxy: {
                            scheme: "http",
                            host: host,
                            port: port
                        },
                        bypassList: ["localhost", "127.0.0.1"]
                    }
                };

                await chrome.proxy.settings.set({
                    value: config,
                    scope: 'regular'
                });

                console.log(`✅ Proxy enabled: ${host}:${port}`);
                sendResponse({ success: true, message: `Proxy enabled: ${host}:${port}` });
            } catch (error) {
                console.error('Error enabling proxy:', error);
                sendResponse({ success: false, error: error.message });
            }
        })();
        return true;
    } else if (message.action === 'disableProxy') {
        // Disable proxy - return to direct connection
        (async () => {
            try {
                await chrome.proxy.settings.set({
                    value: { mode: "direct" },
                    scope: 'regular'
                });

                // Clear stored credentials
                await chrome.storage.local.remove(['proxy-auth-username', 'proxy-auth-password']);

                console.log('✅ Proxy disabled');
                sendResponse({ success: true, message: 'Proxy disabled' });
            } catch (error) {
                console.error('Error disabling proxy:', error);
                sendResponse({ success: false, error: error.message });
            }
        })();
        return true;
    }
    return true;
});

// Handle proxy authentication
chrome.webRequest.onAuthRequired.addListener(
    async (details) => {
        // Get stored credentials
        const result = await chrome.storage.local.get(['proxy-auth-username', 'proxy-auth-password']);
        const username = result['proxy-auth-username'];
        const password = result['proxy-auth-password'];

        if (username && password) {
            console.log('🔐 Providing proxy authentication');
            return {
                authCredentials: {
                    username: username,
                    password: password
                }
            };
        }
        return {};
    },
    { urls: ["<all_urls>"] },
    ["asyncBlocking"]
);

// Open side panel when extension icon is clicked (only for current tab's window)
chrome.action.onClicked.addListener(async (tab) => {
    try {
        // Only open side panel for the current tab's window
        await chrome.sidePanel.open({ windowId: tab.windowId });
    } catch (error) {
        console.error('Error opening side panel:', error);
    }
});

