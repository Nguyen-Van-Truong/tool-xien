// Side Panel JavaScript - Controls the extension UI
// Real-time log updates via polling

class PopupController {
    constructor() {
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.skipBtn = document.getElementById('skipBtn');
        this.importBtn = document.getElementById('importBtn');
        this.fileInput = document.getElementById('fileInput');
        this.prevBtn = document.getElementById('prevBtn');
        this.nextBtn = document.getElementById('nextBtn');

        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusText = document.getElementById('statusText');
        this.attemptsEl = document.getElementById('attempts');
        this.successEl = document.getElementById('success');
        this.failedEl = document.getElementById('failed');
        this.logContainer = document.getElementById('logContainer');

        // Veteran display elements
        this.veteranCount = document.getElementById('veteranCount');
        this.vetName = document.getElementById('vetName');
        this.vetBranch = document.getElementById('vetBranch');
        this.vetBirth = document.getElementById('vetBirth');
        this.vetDischarge = document.getElementById('vetDischarge');
        this.vetIndex = document.getElementById('vetIndex');

        // Cookie elements
        this.exportCookieBtn = document.getElementById('exportCookieBtn');
        this.importCookieBtn = document.getElementById('importCookieBtn');
        this.cookieTextarea = document.getElementById('cookieTextarea');
        this.cookieStatus = document.getElementById('cookieStatus');

        // SheerID link and email
        this.sheeridLink = document.getElementById('sheeridLink');
        this.emailInput = document.getElementById('emailInput');

        // Email API elements
        this.emailAccount = document.getElementById('emailAccount');
        this.checkEmailBtn = document.getElementById('checkEmailBtn');
        this.emailStatus = document.getElementById('emailStatus');

        // Email API URL
        this.EMAIL_API_URL = 'https://tools.dongvanfb.net/api/get_messages_oauth2';

        // Track last log count for polling
        this.lastLogCount = 0;

        this.init();
    }

    async init() {
        // Load saved state
        await this.loadState();

        // Bind events
        this.startBtn.addEventListener('click', () => this.start());
        this.stopBtn.addEventListener('click', () => this.stop());
        this.skipBtn.addEventListener('click', () => this.skip());
        this.importBtn.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileImport(e));
        this.prevBtn.addEventListener('click', () => this.prevVeteran());
        this.nextBtn.addEventListener('click', () => this.nextVeteran());

        // Cookie events
        this.exportCookieBtn.addEventListener('click', () => this.exportCookies());
        this.importCookieBtn.addEventListener('click', () => this.importCookies());

        // Email API events
        this.checkEmailBtn.addEventListener('click', () => this.checkEmail());

        // AUTO-SAVE inputs on change
        this.sheeridLink?.addEventListener('input', async (e) => {
            await chrome.storage.local.set({ sheeridLink: e.target.value });
        });

        this.emailInput?.addEventListener('input', async (e) => {
            await chrome.storage.local.set({ verifyEmail: e.target.value });
        });

        this.emailAccount?.addEventListener('input', async (e) => {
            await chrome.storage.local.set({ emailAccount: e.target.value });
        });

        // Listen for messages from background (instant updates)
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            if (message.type === 'STATE_UPDATE') {
                this.updateUI(message.state);
            }
            if (message.type === 'LOG') {
                this.addLog(message.text, message.level);
            }
        });

        // POLLING: Also poll for state every 500ms (for real-time updates)
        this.startPolling();
    }

    startPolling() {
        setInterval(async () => {
            try {
                const response = await chrome.runtime.sendMessage({ type: 'GET_STATE' });
                if (response && response.state) {
                    this.updateUI(response.state);
                }
            } catch (e) {
                // Extension might not be ready
            }
        }, 500);
    }

    async loadState() {
        const result = await chrome.storage.local.get(['verifyState', 'veterans', 'currentIndex', 'sheeridLink', 'verifyEmail', 'emailAccount', 'debugMode']);
        if (result.verifyState) {
            this.updateUI(result.verifyState);
        }
        if (result.veterans) {
            this.updateVeteranDisplay(result.veterans, result.currentIndex || 0);
        }
        // Restore saved link and email
        if (result.sheeridLink && this.sheeridLink) {
            this.sheeridLink.value = result.sheeridLink;
        }
        if (result.verifyEmail && this.emailInput) {
            this.emailInput.value = result.verifyEmail;
        }
        // Restore email account
        if (result.emailAccount && this.emailAccount) {
            this.emailAccount.value = result.emailAccount;
        }
        // Restore debug mode
        if (this.debugMode) {
            this.debugMode.checked = result.debugMode || false;
        }
    }

    updateUI(state) {
        // Update stats
        this.attemptsEl.textContent = state.attempts || 0;
        this.successEl.textContent = state.success || 0;
        this.failedEl.textContent = state.failed || 0;

        // Update status
        this.statusText.textContent = state.statusText || 'Ready';

        // Update indicator
        this.statusIndicator.className = 'status-indicator';
        if (state.isRunning) {
            this.statusIndicator.classList.add('running');
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
        } else if (state.hasError) {
            this.statusIndicator.classList.add('error');
            this.startBtn.disabled = false;
            this.stopBtn.disabled = true;
        } else if (state.success > 0) {
            this.statusIndicator.classList.add('success');
            this.startBtn.disabled = false;
            this.stopBtn.disabled = true;
        } else {
            this.startBtn.disabled = false;
            this.stopBtn.disabled = true;
        }

        // Update logs
        if (state.logs && state.logs.length > 0) {
            this.logContainer.innerHTML = '';
            state.logs.forEach(log => {
                this.addLog(log.text, log.level, false);
            });
        }
    }

    updateVeteranDisplay(veterans, currentIndex) {
        if (!veterans || veterans.length === 0) {
            this.veteranCount.textContent = 'No data loaded';
            this.vetName.textContent = '---';
            this.vetBranch.textContent = '---';
            this.vetBirth.textContent = '---';
            this.vetDischarge.textContent = '---';
            this.vetIndex.textContent = '0/0';
            return;
        }

        this.veteranCount.textContent = `${veterans.length} veterans loaded`;
        this.vetIndex.textContent = `${currentIndex + 1}/${veterans.length}`;

        const vet = veterans[currentIndex];
        if (vet) {
            this.vetName.textContent = `${vet.firstName} ${vet.lastName}`;
            this.vetBranch.textContent = vet.branch;
            this.vetBirth.textContent = `${vet.birthMonth} ${vet.birthDay}, ${vet.birthYear}`;
            this.vetDischarge.textContent = `${vet.dischargeMonth} ${vet.dischargeDay}, ${vet.dischargeYear}`;
        }
    }

    async handleFileImport(event) {
        const file = event.target.files[0];
        if (!file) return;

        const text = await file.text();
        const lines = text.split('\n').filter(line => line.trim() && line.includes('|'));

        const veterans = lines.map(line => {
            const parts = line.split('|');
            if (parts.length < 10) return null;
            return {
                firstName: parts[0].trim(),
                lastName: parts[1].trim(),
                branch: parts[2].trim(),
                birthMonth: parts[3].trim(),
                birthDay: parts[4].trim(),
                birthYear: parts[5].trim(),
                dischargeMonth: parts[6].trim(),
                dischargeDay: parts[7].trim(),
                dischargeYear: parts[8].trim(),
                email: parts[9].trim()
            };
        }).filter(v => v !== null);

        if (veterans.length === 0) {
            this.addLog('Invalid file format!', 'error');
            return;
        }

        // Save to storage
        await chrome.storage.local.set({ veterans, currentIndex: 0 });
        this.updateVeteranDisplay(veterans, 0);
        this.addLog(`Imported ${veterans.length} veterans`, 'success');

        // Notify background
        chrome.runtime.sendMessage({ type: 'VETERANS_LOADED', count: veterans.length });
    }

    async prevVeteran() {
        const result = await chrome.storage.local.get(['veterans', 'currentIndex']);
        if (!result.veterans || result.veterans.length === 0) return;

        let newIndex = (result.currentIndex || 0) - 1;
        if (newIndex < 0) newIndex = result.veterans.length - 1;

        await chrome.storage.local.set({ currentIndex: newIndex });
        this.updateVeteranDisplay(result.veterans, newIndex);
    }

    async nextVeteran() {
        const result = await chrome.storage.local.get(['veterans', 'currentIndex']);
        if (!result.veterans || result.veterans.length === 0) return;

        let newIndex = (result.currentIndex || 0) + 1;
        if (newIndex >= result.veterans.length) newIndex = 0;

        await chrome.storage.local.set({ currentIndex: newIndex });
        this.updateVeteranDisplay(result.veterans, newIndex);
    }

    addLog(text, level = 'info', save = true) {
        const entry = document.createElement('div');
        entry.className = `log-entry ${level}`;
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
        this.logContainer.appendChild(entry);
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
    }

    async start() {
        // Check if veterans loaded
        const result = await chrome.storage.local.get(['veterans']);
        if (!result.veterans || result.veterans.length === 0) {
            this.addLog('Please import veterans data first!', 'error');
            return;
        }

        // Get SheerID link and email
        const sheeridLink = this.sheeridLink?.value?.trim();
        const email = this.emailInput?.value?.trim();

        if (!sheeridLink) {
            this.addLog('Please enter SheerID verification link!', 'error');
            return;
        }

        if (!email) {
            this.addLog('Please enter email!', 'error');
            return;
        }

        // Validate email format - reject if contains | (wrong field)
        if (email.includes('|')) {
            this.addLog('❌ Email format wrong! Only enter email, NOT password!', 'error');
            this.addLog('   Example: user@outlook.com', 'warning');
            return;
        }

        // Basic email validation
        if (!email.includes('@') || !email.includes('.')) {
            this.addLog('❌ Invalid email format!', 'error');
            return;
        }

        // Save link and email
        await chrome.storage.local.set({ sheeridLink, verifyEmail: email });

        chrome.runtime.sendMessage({ type: 'START_VERIFY' });
        this.addLog('Starting API verification...', 'info');
    }

    async stop() {
        chrome.runtime.sendMessage({ type: 'STOP_VERIFY' });
        this.addLog('Stopping...', 'info');
    }

    async skip() {
        chrome.runtime.sendMessage({ type: 'SKIP_VETERAN' });
        this.addLog('Skipping current veteran...', 'info');
        await this.nextVeteran();
    }

    // ========== COOKIE MANAGEMENT ==========

    async exportCookies() {
        try {
            this.setCookieStatus('Exporting...', '');

            // Get all cookies from chatgpt.com
            const cookies = await chrome.cookies.getAll({ domain: '.chatgpt.com' });

            if (cookies.length === 0) {
                // Try chat.openai.com
                const openaiCookies = await chrome.cookies.getAll({ domain: '.openai.com' });
                if (openaiCookies.length > 0) {
                    this.cookieTextarea.value = JSON.stringify(openaiCookies, null, 2);
                    this.setCookieStatus(`Exported ${openaiCookies.length} cookies (openai.com)`, 'success');
                    return;
                }
                this.setCookieStatus('No cookies found. Please login first.', 'error');
                return;
            }

            this.cookieTextarea.value = JSON.stringify(cookies, null, 2);
            this.setCookieStatus(`Exported ${cookies.length} cookies`, 'success');
            this.addLog(`Exported ${cookies.length} ChatGPT cookies`, 'success');

        } catch (error) {
            this.setCookieStatus(`Error: ${error.message}`, 'error');
            console.error('Export error:', error);
        }
    }

    async importCookies() {
        try {
            const cookieJson = this.cookieTextarea.value.trim();

            if (!cookieJson) {
                this.setCookieStatus('Please paste cookies JSON first!', 'error');
                return;
            }

            this.setCookieStatus('Importing...', '');

            let cookies;
            try {
                cookies = JSON.parse(cookieJson);
            } catch (e) {
                this.setCookieStatus('Invalid JSON format!', 'error');
                return;
            }

            if (!Array.isArray(cookies)) {
                this.setCookieStatus('JSON must be an array of cookies!', 'error');
                return;
            }

            let successCount = 0;
            let failCount = 0;

            for (const cookie of cookies) {
                try {
                    // Prepare cookie for setting
                    const newCookie = {
                        url: `https://${cookie.domain.replace(/^\./, '')}${cookie.path || '/'}`,
                        name: cookie.name,
                        value: cookie.value,
                        domain: cookie.domain,
                        path: cookie.path || '/',
                        secure: cookie.secure !== false,
                        httpOnly: cookie.httpOnly || false,
                        sameSite: cookie.sameSite || 'lax'
                    };

                    // Set expiration if present
                    if (cookie.expirationDate) {
                        newCookie.expirationDate = cookie.expirationDate;
                    }

                    await chrome.cookies.set(newCookie);
                    successCount++;
                } catch (e) {
                    console.warn(`Failed to set cookie ${cookie.name}:`, e);
                    failCount++;
                }
            }

            this.setCookieStatus(`Imported ${successCount} cookies (${failCount} failed)`, successCount > 0 ? 'success' : 'error');
            this.addLog(`Imported ${successCount} cookies to ChatGPT`, 'success');

        } catch (error) {
            this.setCookieStatus(`Error: ${error.message}`, 'error');
            console.error('Import error:', error);
        }
    }

    setCookieStatus(message, type) {
        this.cookieStatus.textContent = message;
        this.cookieStatus.className = `cookie-status ${type}`;
    }

    // ========== EMAIL API ==========

    async checkEmail() {
        try {
            const accountStr = this.emailAccount?.value?.trim();
            if (!accountStr) {
                this.setEmailStatus('Please enter email account!', 'error');
                return;
            }

            // Parse: email|password|refresh_token|client_id
            const parts = accountStr.split('|');
            if (parts.length < 4) {
                this.setEmailStatus('Format: email|password|refresh_token|client_id', 'error');
                return;
            }

            const [userEmail, password, refreshToken, clientId] = parts;

            // Save account
            await chrome.storage.local.set({ emailAccount: accountStr });

            this.setEmailStatus('Checking email...', '');
            this.addLog(`Checking email: ${userEmail}`, 'info');

            // Call API
            const response = await fetch(this.EMAIL_API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: userEmail,
                    refresh_token: refreshToken,
                    client_id: clientId
                })
            });

            if (!response.ok) {
                this.setEmailStatus(`API error: ${response.status}`, 'error');
                return;
            }

            const data = await response.json();

            if (!data.status || !data.messages) {
                this.setEmailStatus(`API failed: ${data.code || 'Unknown'}`, 'error');
                this.addLog(`Email API error: ${JSON.stringify(data).substring(0, 200)}`, 'error');
                return;
            }

            // Find SheerID verify link in emails
            const verifyLink = this.findSheerIdLink(data.messages);

            if (verifyLink) {
                this.setEmailStatus('Found verify link!', 'success');
                this.addLog(`Found: ${verifyLink.substring(0, 60)}...`, 'success');

                // Auto-fill SheerID link
                if (this.sheeridLink) {
                    this.sheeridLink.value = verifyLink;
                    await chrome.storage.local.set({ sheeridLink: verifyLink });
                }
            } else {
                this.setEmailStatus(`No verify link in ${data.messages.length} emails`, 'error');
                this.addLog(`Checked ${data.messages.length} emails, no SheerID link found`, 'warning');
            }

        } catch (error) {
            this.setEmailStatus(`Error: ${error.message}`, 'error');
            this.addLog(`Email check error: ${error.message}`, 'error');
        }
    }

    findSheerIdLink(messages) {
        // Sort by date descending (newest first)
        const sortedMessages = [...messages].sort((a, b) => {
            const dateA = a.date || '';
            const dateB = b.date || '';
            return dateB.localeCompare(dateA);
        });

        for (const msg of sortedMessages) {
            // Get 'from' address - handle multiple formats
            let fromAddr = '';
            const fromField = msg.from;
            if (Array.isArray(fromField) && fromField.length > 0) {
                fromAddr = fromField[0]?.address || fromField[0] || '';
            } else if (typeof fromField === 'string') {
                fromAddr = fromField;
            }
            fromAddr = String(fromAddr).toLowerCase();

            const subject = (msg.subject || '').toLowerCase();

            // Match: from contains "sheerid" or "verify@" AND subject contains relevant keywords
            const isFromSheerID = fromAddr.includes('sheerid') || fromAddr.includes('verify@');
            const hasVerifySubject = subject.includes('verified') || subject.includes('verify') || subject.includes('openai');

            if (isFromSheerID && hasVerifySubject) {
                // Get body - check multiple field names
                const body = msg.message || msg.body || msg.snippet || msg.content || '';

                // Find link
                const linkMatch = body.match(/https:\/\/services\.sheerid\.com\/verify\/[^\s<>"'\]]+/);
                if (linkMatch) {
                    // Clean up link
                    let link = linkMatch[0].replace(/[.,;:!?]+$/, '');
                    return link;
                }
            }
        }
        return null;
    }

    setEmailStatus(message, type) {
        this.emailStatus.textContent = message;
        this.emailStatus.className = `email-status ${type}`;
    }
}

// Initialize popup
document.addEventListener('DOMContentLoaded', () => {
    new PopupController();
});
