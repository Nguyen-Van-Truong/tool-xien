/**
 * Grok Login Worker - Puppeteer Automation Module
 * Handles mass login verification with parallel browser execution
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');

class GrokLoginWorker {
    constructor(mainWindow, options = {}) {
        this.mainWindow = mainWindow;
        this.browsers = [];
        this.isRunning = false;
        this.maxConcurrent = options.maxConcurrent || 5;
        this.keepBrowserOpen = options.keepBrowserOpen !== false;
        this.headless = options.headless || false;
        this.results = { success: 0, failed: 0, total: 0 };
    }

    log(message, type = 'info') {
        console.log(message);
        if (this.mainWindow) {
            this.mainWindow.webContents.send('log', { message, type });
        }
    }

    updateProgress(current, total, text) {
        if (this.mainWindow) {
            this.mainWindow.webContents.send('progress', { current, total, text });
        }
    }

    updateBrowserCount() {
        const count = this.browsers.length;
        if (this.mainWindow) {
            this.mainWindow.webContents.send('browser-count', {
                active: count,
                max: this.maxConcurrent
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
        if (this.mainWindow) {
            this.mainWindow.webContents.send('result', this.results);
        }
    }

    async start(accounts) {
        this.isRunning = true;
        this.results = { success: 0, failed: 0, total: accounts.length };
        const startTime = Date.now();

        this.log(`🚀 Starting login for ${accounts.length} accounts (max ${this.maxConcurrent} concurrent)...`, 'info');

        // Process in batches
        for (let i = 0; i < accounts.length && this.isRunning; i += this.maxConcurrent) {
            const batch = accounts.slice(i, i + this.maxConcurrent);
            const batchNum = Math.floor(i / this.maxConcurrent) + 1;
            const totalBatches = Math.ceil(accounts.length / this.maxConcurrent);

            this.log(`\n📦 Batch ${batchNum}/${totalBatches}: ${batch.length} account(s) with 1s stagger...`, 'info');

            // Staggered launch - 1 second delay between each browser
            const promises = batch.map((account, idx) => {
                const accountNum = i + idx + 1;
                return new Promise(async (resolve) => {
                    // Wait idx seconds before starting (0s, 1s, 2s, ...)
                    await new Promise(r => setTimeout(r, idx * 1000));
                    const result = await this.loginAccount(account, accountNum, accounts.length);
                    resolve(result);
                });
            });

            await Promise.allSettled(promises);
            this.log(`✅ Batch ${batchNum}/${totalBatches} completed!`, 'success');
        }

        const totalTime = Math.round((Date.now() - startTime) / 1000);
        this.log(`\n🎉 Done! Success: ${this.results.success}, Failed: ${this.results.failed} (${totalTime}s)`, 'success');

        if (this.keepBrowserOpen) {
            this.log(`🌐 ${this.browsers.length} browser(s) kept open. Use "Close All Browsers" to close.`, 'info');
        }

        if (this.mainWindow) {
            this.mainWindow.webContents.send('complete', { ...this.results, totalTime });
        }
    }

    async loginAccount(account, accountNum, total) {
        const { email, password } = account;
        let browser = null;

        try {
            this.log(`\n━━ [${accountNum}/${total}] ${email} ━━`, 'info');
            this.updateProgress(accountNum, total, `Processing ${accountNum}/${total}...`);

            // Step 1: Launch browser
            this.log('🌐 1/6: Launching browser...', 'info');
            const chromePaths = [
                'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
                process.env.LOCALAPPDATA + '\\Google\\Chrome\\Application\\chrome.exe'
            ];
            const executablePath = chromePaths.find(p => fs.existsSync(p));
            if (!executablePath) throw new Error('Chrome not found');

            browser = await puppeteer.launch({
                executablePath,
                headless: this.headless,
                args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled'],
                defaultViewport: { width: 1280, height: 720 }
            });
            this.browsers.push({ browser, email });
            this.updateBrowserCount();
            const page = await browser.newPage();

            // Step 2: Navigate to login page
            this.log('🔗 2/6: Navigating to login page...', 'info');
            await page.goto('https://accounts.x.ai/sign-in', { waitUntil: 'networkidle2', timeout: 30000 });

            // Step 3: Click "Login with email"
            this.log('🖱️ 3/6: Clicking "Login with email"...', 'info');
            await page.waitForSelector('button svg.lucide-mail', { timeout: 10000 });
            await page.evaluate(() => {
                const btn = document.querySelector('button svg.lucide-mail');
                if (btn) btn.closest('button').click();
            });
            await page.waitForTimeout(2000);

            // Step 4: Enter email and click Next
            this.log('📝 4/6: Entering email...', 'info');
            await page.waitForSelector('[data-testid="email"]', { timeout: 10000 });
            await page.type('[data-testid="email"]', email, { delay: 50 });
            await page.waitForTimeout(500);
            
            // Click Next button
            await page.evaluate(() => {
                const btn = document.querySelector('button[type="submit"]');
                if (btn) btn.click();
            });
            await page.waitForTimeout(2000);

            // Step 5: Enter password and click Login
            this.log('🔑 5/6: Entering password...', 'info');
            await page.waitForSelector('input[name="password"]', { timeout: 10000 });
            await page.type('input[name="password"]', password, { delay: 50 });
            await page.waitForTimeout(500);
            
            // Click Login button
            await page.evaluate(() => {
                const btn = document.querySelector('button[type="submit"]');
                if (btn) btn.click();
            });
            await page.waitForTimeout(3000);

            // Step 6: Verify login result
            this.log('🔍 6/6: Verifying login...', 'info');
            
            // Check for error message
            const errorMessage = await page.evaluate(() => {
                const errorEl = document.body.innerText;
                if (errorEl.includes('Wrong email address or password')) {
                    return 'Wrong email address or password';
                }
                if (errorEl.includes('too many requests') || errorEl.includes('rate limit')) {
                    return 'Rate limited';
                }
                return null;
            });

            if (errorMessage) {
                throw new Error(errorMessage);
            }

            // Wait a bit and check current URL
            await page.waitForTimeout(2000);
            const currentUrl = page.url();
            this.log(`📍 Current URL: ${currentUrl}`, 'info');

            // Check if on accept-tos page (means login success, need to accept ToS)
            if (currentUrl.includes('accept-tos')) {
                this.log('📜 Accepting Terms of Service...', 'info');
                await page.waitForSelector('button[role="checkbox"]', { timeout: 5000 });
                await page.evaluate(() => {
                    const checkboxes = document.querySelectorAll('button[role="checkbox"]');
                    checkboxes.forEach(cb => cb.click());
                });
                await page.waitForTimeout(1000);
                await page.evaluate(() => {
                    const btn = document.querySelector('button[type="submit"]');
                    if (btn) btn.click();
                });
                await page.waitForTimeout(3000);
            }

            // Verify by checking profile API
            const response = await page.goto('https://grok.com/rest/suggestions/profile', { timeout: 10000 });
            const contentType = response.headers()['content-type'] || '';

            let success = false;

            if (contentType.includes('application/json')) {
                const data = await response.json();
                if (data.code === 16 && data.message === 'User authentication required') {
                    throw new Error('Not authenticated');
                }
                success = true;
            } else {
                const finalUrl = page.url();
                if (finalUrl.includes('grok.com') && !finalUrl.includes('sign-in') && !finalUrl.includes('login')) {
                    success = true;
                } else {
                    throw new Error('Verification failed - not logged in');
                }
            }

            if (success) {
                this.log(`🎉 SUCCESS: ${email}`, 'success');
                this.saveResult(account, 'success');
            }

        } catch (error) {
            this.log(`❌ FAILED: ${error.message}`, 'error');
            this.saveResult(account, 'failed', { error: error.message });
        } finally {
            if (!this.keepBrowserOpen && browser) {
                await browser.close();
                this.browsers = this.browsers.filter(b => b.browser !== browser);
                this.updateBrowserCount();
            }
        }
    }

    async stop() {
        this.isRunning = false;
        this.log('⏸️ Stopping...', 'warning');
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

module.exports = { GrokLoginWorker };
