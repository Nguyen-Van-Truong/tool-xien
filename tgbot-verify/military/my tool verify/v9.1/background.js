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
    } else if (message.action === 'sheeridVerify') {
        // SheerID API verification (bypass CORS)
        (async () => {
            try {
                const SHEERID_BASE_URL = "https://services.sheerid.com/rest/v2/verification";
                const ORGANIZATIONS = {
                    "Army": {id: 4070, name: "Army"},
                    "Navy": {id: 4072, name: "Navy"},
                    "Air Force": {id: 4073, name: "Air Force"},
                    "Marine Corps": {id: 4071, name: "Marine Corps"},
                    "Coast Guard": {id: 4074, name: "Coast Guard"}
                };
                
                const { verificationId, veteranData, email } = message;
                
                console.log('🚀 SheerID Verify - Starting...');
                console.log('   verificationId:', verificationId);
                console.log('   veteran:', veteranData.first, veteranData.last);
                console.log('   branch:', veteranData.branch);
                console.log('   email:', email);
                
                // Step 1: collectMilitaryStatus
                console.log('📤 Step 1: collectMilitaryStatus...');
                const step1Url = `${SHEERID_BASE_URL}/${verificationId}/step/collectMilitaryStatus`;
                console.log('   URL:', step1Url);
                
                const step1Response = await fetch(step1Url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: "VETERAN" })
                });
                
                console.log('   Response status:', step1Response.status);
                
                if (!step1Response.ok) {
                    const errorText = await step1Response.text();
                    console.log('❌ Step 1 failed:', errorText);
                    sendResponse({ success: false, error: `Step 1 failed: ${step1Response.status}`, details: errorText });
                    return;
                }
                
                const step1Result = await step1Response.json();
                console.log('✅ Step 1 result:', JSON.stringify(step1Result).substring(0, 200));
                
                const currentStep = step1Result.currentStep;
                console.log('   currentStep:', currentStep);
                
                // Check if step 1 succeeded - allow different valid steps
                if (currentStep !== 'collectInactiveMilitaryPersonalInfo') {
                    // If already at success or emailLoop, return that
                    if (currentStep === 'success' || currentStep === 'emailLoop') {
                        console.log('✅ Already completed:', currentStep);
                        sendResponse({ success: true, result: step1Result });
                        return;
                    }
                    console.log('❌ Unexpected step:', currentStep);
                    sendResponse({ success: false, error: 'Unexpected step after Step 1', step: currentStep, result: step1Result });
                    return;
                }
                
                // Step 2: collectInactiveMilitaryPersonalInfo
                console.log('📤 Step 2: collectInactiveMilitaryPersonalInfo...');
                const submissionUrl = step1Result.submissionUrl || 
                    `${SHEERID_BASE_URL}/${verificationId}/step/collectInactiveMilitaryPersonalInfo`;
                console.log('   URL:', submissionUrl);
                
                const org = ORGANIZATIONS[veteranData.branch] || ORGANIZATIONS["Navy"];
                console.log('   organization:', org);
                
                const payload = {
                    firstName: veteranData.first,
                    lastName: veteranData.last,
                    birthDate: veteranData.birthDate,
                    email: email,
                    organization: org,
                    dischargeDate: veteranData.dischargeDate || "2025-12-01",
                    metadata: {}
                };
                console.log('   payload:', JSON.stringify(payload));
                
                const step2Response = await fetch(submissionUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                console.log('   Response status:', step2Response.status);
                
                if (!step2Response.ok) {
                    const errorText = await step2Response.text();
                    console.log('❌ Step 2 failed:', errorText);
                    sendResponse({ success: false, error: `Step 2 failed: ${step2Response.status}`, details: errorText });
                    return;
                }
                
                const step2Result = await step2Response.json();
                console.log('✅ Step 2 result:', JSON.stringify(step2Result).substring(0, 200));
                console.log('   Final step:', step2Result.currentStep);
                
                sendResponse({ success: true, result: step2Result });
                
            } catch (error) {
                console.error('❌ SheerID Verify Error:', error);
                sendResponse({ success: false, error: error.message });
            }
        })();
        return true; // Keep channel open for async
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

