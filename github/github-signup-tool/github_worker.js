/**
 * GitHub Signup Worker - Puppeteer Automation
 * Fills signup form and waits for manual completion
 *
 * GitHub signup is a multi-step wizard:
 *   Step 1: Enter email → Continue
 *   Step 2: Enter password → Continue
 *   Step 3: Enter username → Continue
 *   Step 4: Email preferences → Continue
 *   Step 5: Captcha verification → "Create account" (manual)
 *   Step 6: STOP - keep browser open for user
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');

class GitHubWorker {
    constructor(mainWindow, options = {}) {
        this.mainWindow = mainWindow;
        this.browsers = [];
        this.isRunning = false;
        this.headless = options.headless || false;
        this.keepBrowserOpen = (options.keepBrowser !== undefined) ? options.keepBrowser : (options.keepBrowserOpen !== false);
        this.autofillDelay = options.autofillDelay || 1;
        this.results = { success: 0, failed: 0, total: 0 };

        // Manual wait signal mechanism
        this._manualResolve = null;
    }

    log(message, type = 'info') {
        console.log(message);
        if (this.mainWindow && this.mainWindow.webContents) {
            this.mainWindow.webContents.send('log', message);
        }
    }

    updateProgress(current, total, text) {
        if (this.mainWindow && this.mainWindow.webContents) {
            this.mainWindow.webContents.send('progress', { current, total, text });
        }
    }

    updateBrowserCount() {
        if (this.mainWindow && this.mainWindow.webContents) {
            this.mainWindow.webContents.send('browser-count', {
                active: this.browsers.length,
                max: 1
            });
        }
    }

    saveResult(account, status, extraData = {}) {
        const timestamp = new Date().toISOString();
        if (status === 'success') {
            const line = `${account.email}|${account.password}\n`;
            fs.appendFileSync('success.txt', line);
            this.results.success++;
        } else {
            const line = `${account.email}|${account.password}|${extraData.error || 'unknown'}|${timestamp}\n`;
            fs.appendFileSync('failed.txt', line);
            this.results.failed++;
        }
        if (this.mainWindow && this.mainWindow.webContents) {
            // Send individual result for UI text update
            this.mainWindow.webContents.send('result', {
                email: account.email,
                password: account.password,
                username: account.username,
                status,
                error: extraData.error || '',
                timestamp,
                totals: { ...this.results }
            });
        }
    }

    // Called from main process when user clicks "Next Account"
    resolveManualWait(status) {
        if (this._manualResolve) {
            this._manualResolve(status);
            this._manualResolve = null;
        }
    }

    // Wait for user to signal they're done
    waitForManualCompletion() {
        return new Promise((resolve) => {
            this._manualResolve = resolve;
        });
    }

    async start(accounts) {
        this.isRunning = true;
        this.results = { success: 0, failed: 0, total: accounts.length };
        const startTime = Date.now();

        this.log(`🚀 Bắt đầu đăng ký ${accounts.length} GitHub accounts...`, 'info');

        // Process accounts one by one (sequential)
        for (let i = 0; i < accounts.length && this.isRunning; i++) {
            const account = accounts[i];
            const accountNum = i + 1;

            this.log(`\n━━ [${accountNum}/${accounts.length}] ${account.email} ━━`, 'info');
            this.updateProgress(accountNum, accounts.length, `Account ${accountNum}/${accounts.length}`);

            await this.processAccount(account, accountNum, accounts.length);
        }

        const totalTime = Math.round((Date.now() - startTime) / 1000);
        this.log(`\n🎉 Hoàn thành! Success: ${this.results.success}, Failed: ${this.results.failed} (${totalTime}s)`, 'success');

        if (this.mainWindow && this.mainWindow.webContents) {
            this.mainWindow.webContents.send('complete', { ...this.results, totalTime });
        }
    }

    async processAccount(account, accountNum, total) {
        const { email, password, username } = account;
        let browser = null;

        try {
            // Step 1: Launch browser
            this.log('🌐 1/7: Launching browser...', 'info');
            const chromePaths = [
                'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
                process.env.LOCALAPPDATA + '\\Google\\Chrome\\Application\\chrome.exe'
            ];
            const executablePath = chromePaths.find(p => fs.existsSync(p));
            if (!executablePath) throw new Error('Chrome not found');

            browser = await puppeteer.launch({
                executablePath,
                headless: this.headless ? 'new' : false,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled'
                ],
                defaultViewport: { width: 1280, height: 800 }
            });
            this.browsers.push({ browser, email });
            this.updateBrowserCount();

            const page = await browser.newPage();

            // Stealth: hide webdriver flag
            await page.evaluateOnNewDocument(() => {
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            });

            // Step 2: Navigate to GitHub signup
            this.log('🔗 2/7: Navigating to GitHub signup...', 'info');
            await page.goto('https://github.com/signup?ref_cta=Sign+up&ref_loc=header+logged+out&ref_page=%2F&source=header-home', {
                waitUntil: 'networkidle2',
                timeout: 30000
            });

            // Small delay to let page fully render
            await this.sleep(this.autofillDelay * 1000);

            // Step 3: Enter email
            this.log(`📧 3/7: Entering email: ${email}`, 'info');
            await page.waitForSelector('#email', { timeout: 15000, visible: true });
            await this.sleep(500);
            await page.click('#email');
            await page.type('#email', email, { delay: 60 });
            await this.sleep(1000);

            // Click Continue button after email
            this.log('➡️ Clicking Continue...', 'info');
            await this.clickContinueButton(page);
            await this.sleep(2000);

            // Step 4: Enter password
            this.log('🔑 4/7: Entering password...', 'info');
            await page.waitForSelector('#password', { timeout: 15000, visible: true });
            await this.sleep(500);
            await page.click('#password');
            await page.type('#password', password, { delay: 40 });
            await this.sleep(1000);

            // Click Continue button after password
            this.log('➡️ Clicking Continue...', 'info');
            await this.clickContinueButton(page);
            await this.sleep(2000);

            // Step 5: Enter username
            this.log(`👤 5/7: Entering username: ${username}`, 'info');
            await page.waitForSelector('#login', { timeout: 15000, visible: true });
            await this.sleep(500);
            await page.click('#login');
            await page.type('#login', username, { delay: 60 });
            await this.sleep(1500);

            // Click Continue button after username
            this.log('➡️ Clicking Continue...', 'info');
            await this.clickContinueButton(page);
            await this.sleep(2000);

            // Step 6: Email preferences (opt out) → Continue
            this.log('📩 6/7: Handling email preferences...', 'info');
            try {
                // Look for the opt-in field and enter 'n'
                const optField = await page.$('#opt_in');
                if (optField) {
                    await optField.click();
                    await optField.type('n', { delay: 50 });
                    await this.sleep(500);
                }
            } catch (e) {
                this.log('⚠️ Email preferences field not found, skipping...', 'warning');
            }

            // Click Continue
            await this.clickContinueButton(page);
            await this.sleep(2000);

            // Step 7: We're now at captcha/verification step
            // Try to click "Create account" button
            this.log('🖱️ 7/7: Looking for Create account button...', 'info');
            try {
                const createBtn = await page.$('button[data-target="signup-form.SignupButton"]');
                if (createBtn) {
                    await createBtn.click();
                    this.log('✅ Clicked "Create account" button!', 'success');
                } else {
                    this.log('⚠️ Create account button not found (may need manual captcha first)', 'warning');
                }
            } catch (e) {
                this.log('⚠️ Could not click Create account: ' + e.message, 'warning');
            }

            // ========== STOP HERE - WAIT FOR USER ==========
            this.log('', 'info');
            this.log('⏸️ ═══════════════════════════════════════', 'warning');
            this.log('⏸️ FORM ĐÃ ĐIỀN XONG! Đang chờ bạn...', 'warning');
            this.log('⏸️ Hãy hoàn thành captcha/verify thủ công', 'warning');
            this.log('⏸️ Rồi bấm "✅ Done" hoặc "❌ Failed" trên UI', 'warning');
            this.log('⏸️ ═══════════════════════════════════════', 'warning');

            // Notify renderer that we're waiting
            if (this.mainWindow && this.mainWindow.webContents) {
                this.mainWindow.webContents.send('waiting-manual', {
                    email,
                    accountNum,
                    total
                });
            }

            // Wait for user signal
            const userStatus = await this.waitForManualCompletion();

            if (userStatus === 'done' || userStatus === 'success') {
                this.log(`🎉 SUCCESS: ${email}`, 'success');
                this.saveResult(account, 'success');
            } else {
                this.log(`❌ FAILED (user marked): ${email}`, 'error');
                this.saveResult(account, 'failed', { error: 'User marked as failed' });
            }

            // Close browser for this account (unless keepBrowserOpen)
            if (!this.keepBrowserOpen) {
                await browser.close();
                this.browsers = this.browsers.filter(b => b.browser !== browser);
                this.updateBrowserCount();
            }

        } catch (error) {
            this.log(`❌ ERROR: ${email} - ${error.message}`, 'error');
            this.saveResult(account, 'failed', { error: error.message });

            // Still wait for user if browser is open and visible
            if (browser && !this.headless) {
                this.log('⏸️ Browser vẫn mở. Bấm "Done" hoặc "Failed" để tiếp tục...', 'warning');
                if (this.mainWindow && this.mainWindow.webContents) {
                    this.mainWindow.webContents.send('waiting-manual', {
                        email,
                        accountNum,
                        total,
                        hasError: true
                    });
                }
                // Wait but don't override the saved result
                await this.waitForManualCompletion();
            }
        }
    }

    // Click the Continue/Submit button in GitHub's multi-step form
    async clickContinueButton(page) {
        // Try multiple selectors for the Continue button
        const selectors = [
            'button[data-continue-to]',                    // GitHub's data attribute
            'button.js-continue-btn',                       // Class-based
            'button[type="submit"]',                        // Submit button
            'button.signup-continue-button',                // Signup specific
        ];

        for (const selector of selectors) {
            try {
                const btn = await page.$(selector);
                if (btn) {
                    const isVisible = await page.evaluate(el => {
                        const style = window.getComputedStyle(el);
                        return style.display !== 'none' && style.visibility !== 'hidden' && el.offsetParent !== null;
                    }, btn);

                    if (isVisible) {
                        await btn.click();
                        return;
                    }
                }
            } catch (e) { }
        }

        // Fallback: find any visible button with Continue-like text
        try {
            await page.evaluate(() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const continueBtn = buttons.find(b => {
                    const text = b.textContent.trim().toLowerCase();
                    const isVisible = b.offsetParent !== null;
                    return isVisible && (text.includes('continue') || text.includes('next'));
                });
                if (continueBtn) continueBtn.click();
            });
        } catch (e) { }
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async stop() {
        this.isRunning = false;
        this.log('⏸️ Stopping...', 'warning');
        // Resolve any pending manual wait
        if (this._manualResolve) {
            this._manualResolve('stopped');
        }
        await this.closeAllBrowsers();
    }

    async closeAllBrowsers() {
        this.log(`🗑️ Closing ${this.browsers.length} browser(s)...`, 'warning');
        for (const b of this.browsers) {
            try {
                await b.browser.close();
                this.log(`✅ Closed: ${b.email}`, 'success');
            } catch (e) { }
        }
        this.browsers = [];
        this.updateBrowserCount();
    }
}

module.exports = { GitHubWorker };
