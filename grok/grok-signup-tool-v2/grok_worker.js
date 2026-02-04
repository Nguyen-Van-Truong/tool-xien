/**
 * Grok Worker - Puppeteer Automation Module
 * Supports parallel browser execution
 */

const puppeteer = require('puppeteer-core');
const { generateEmail, checkEmailForCode } = require('./email_service');
const fs = require('fs');

class GrokWorker {
    constructor(mainWindow, browserId, options = {}) {
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
            // Simple format: email|password
            const line = `${account.email}|${account.password}\n`;
            fs.appendFileSync('success.txt', line);
            this.results.success++;
        } else {
            // Failed format: email|password|error|timestamp (for debugging)
            const line = `${account.email}|${account.password}|${extraData.error}|${timestamp}\n`;
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

        this.log(`🚀 Starting signup for ${accounts.length} accounts (max ${this.maxConcurrent} concurrent)...`, 'info');

        // Process in batches
        for (let i = 0; i < accounts.length && this.isRunning; i += this.maxConcurrent) {
            const batch = accounts.slice(i, i + this.maxConcurrent);
            const batchNum = Math.floor(i / this.maxConcurrent) + 1;
            const totalBatches = Math.ceil(accounts.length / this.maxConcurrent);

            this.log(`\n📦 Batch ${batchNum}/${totalBatches}: ${batch.length} account(s) in parallel...`, 'info');

            const promises = batch.map((account, idx) => {
                const accountNum = i + idx + 1;
                return this.signupAccount(account, accountNum, accounts.length);
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

    async signupAccount(account, accountNum, total) {
        const { email, password, firstname, lastname } = account;
        let browser = null;

        try {
            this.log(`\n━━ [${accountNum}/${total}] ${email} ━━`, 'info');
            this.updateProgress(accountNum, total, `Processing ${accountNum}/${total}...`);

            // Generate temp email
            this.log('📧 1/12: Generating temp email...', 'info');
            const tempEmailData = await generateEmail();
            this.log(`✅ Temp: ${tempEmailData.email}`, 'success');

            // Launch browser
            this.log('🌐 2/12: Launching browser...', 'info');
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

            // Navigate
            this.log('🔗 3/12: Navigating...', 'info');
            await page.goto('https://accounts.x.ai/sign-up', { waitUntil: 'networkidle2', timeout: 30000 });

            // Click "Sign up with email"
            this.log('🖱️ 4/12: Clicking email button...', 'info');
            await page.waitForSelector('button svg.lucide-mail', { timeout: 10000 });
            await page.evaluate(() => document.querySelector('button svg.lucide-mail').closest('button').click());
            await page.waitForTimeout(2000);

            // Fill email
            this.log('📝 5/12: Filling email...', 'info');
            await page.waitForSelector('[data-testid="email"]', { timeout: 10000 });
            await page.type('[data-testid="email"]', tempEmailData.email, { delay: 50 });
            await page.keyboard.press('Enter');

            // Get OTP
            this.log('⏳ 6/12: Waiting for OTP...', 'info');
            await page.waitForSelector('[name="code"]', { timeout: 15000 });
            const otp = await checkEmailForCode(tempEmailData.domain, tempEmailData.user);
            if (!otp) throw new Error('Failed to get OTP');
            this.log(`✅ OTP: ${otp}`, 'success');

            // Fill OTP
            this.log('🔑 7/12: Entering OTP...', 'info');
            await page.type('[name="code"]', otp, { delay: 100 });
            await page.waitForTimeout(1000);

            // Confirm email
            this.log('✔️ 8/12: Confirming email...', 'info');
            await page.evaluate(() => {
                const btn = Array.from(document.querySelectorAll('button[type="submit"]'))
                    .find(b => b.textContent.includes('Confirm email'));
                if (btn) btn.click();
            });
            await page.waitForTimeout(3000);

            // Fill signup form
            this.log('📝 9/12: Filling form...', 'info');
            await page.waitForSelector('[data-testid="givenName"]', { timeout: 10000 });
            await page.type('[data-testid="givenName"]', firstname, { delay: 50 });
            await page.type('[data-testid="familyName"]', lastname, { delay: 50 });
            await page.type('[data-testid="password"]', password, { delay: 50 });
            await page.waitForTimeout(1000);

            // Complete signup
            this.log('✔️ 10/12: Submitting signup...', 'info');
            await page.evaluate(() => {
                const btn = Array.from(document.querySelectorAll('button[type="submit"]'))
                    .find(b => b.textContent.includes('Complete sign up'));
                if (btn) btn.click();
            });
            await page.waitForTimeout(5000);

            // Check if we landed on ToS page
            const currentUrl = page.url();
            this.log(`📍 Current URL: ${currentUrl}`, 'info');

            if (currentUrl.includes('accept-tos')) {
                // Step 11: Accept Terms of Service
                this.log('📜 11/12: Accepting Terms of Service...', 'info');

                // Wait for ToS page to load
                await page.waitForSelector('input[name="readTerms"]', { timeout: 10000 });

                // Click both checkboxes (using the button role elements)
                await page.evaluate(() => {
                    // Click "I have read and accept" checkbox
                    const readTermsBtn = document.querySelector('button[role="checkbox"][aria-checked="false"]');
                    if (readTermsBtn) readTermsBtn.click();

                    // Click "I am above 18" checkbox  
                    const buttons = document.querySelectorAll('button[role="checkbox"]');
                    if (buttons[1]) buttons[1].click();
                });

                await page.waitForTimeout(1000);
                this.log('✅ ToS checkboxes checked', 'success');

                // Click Continue button
                await page.evaluate(() => {
                    const continueBtn = document.querySelector('button[type="submit"]');
                    if (continueBtn) continueBtn.click();
                });

                await page.waitForTimeout(3000);
                this.log('✅ ToS accepted', 'success');
            }

            // Verify success
            this.log('✅ 12/12: Verifying account...', 'info');
            await page.waitForTimeout(2000);

            // Try to navigate to profile endpoint
            const response = await page.goto('https://grok.com/rest/suggestions/profile');
            const contentType = response.headers()['content-type'] || '';

            let success = false;

            // Check if JSON response
            if (contentType.includes('application/json')) {
                const data = await response.json();
                // If auth required, signup failed
                if (data.code === 16 && data.message === "User authentication required") {
                    throw new Error('Not authenticated');
                }
                success = true;
            } else {
                // HTML response - check current URL to confirm we're logged in
                const finalUrl = page.url();
                if (finalUrl.includes('grok.com') && !finalUrl.includes('sign-up') && !finalUrl.includes('login')) {
                    // Logged in to Grok
                    success = true;
                } else {
                    throw new Error('Verification failed - not logged in');
                }
            }

            if (success) {
                this.log(`🎉 SUCCESS: ${email}`, 'success');
                this.saveResult(account, 'success', { temp_email: tempEmailData.email, otp });
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
    }
}

module.exports = { GrokWorker };
