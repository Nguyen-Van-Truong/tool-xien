/**
 * Grok Worker - Puppeteer Automation Module
 * Handles the complete Grok account signup flow
 */

const puppeteer = require('puppeteer-core');
const { generateEmail, checkEmailForCode } = require('./email_service');
const fs = require('fs');
const path = require('path');

class GrokWorker {
    constructor(mainWindow, browserId, options = {}) {
        this.mainWindow = mainWindow;
        this.browserId = browserId;
        this.options = options;
        this.browser = null;
        this.isRunning = false;
        this.results = {
            success: 0,
            failed: 0,
            total: 0
        };
    }

    /**
     * Send log message to GUI
     */
    log(message, type = 'info') {
        console.log(message);
        if (this.mainWindow) {
            this.mainWindow.webContents.send('log', { message, type });
        }
    }

    /**
     * Update progress in GUI
     */
    updateProgress(current, total, text) {
        if (this.mainWindow) {
            this.mainWindow.webContents.send('progress', { current, total, text });
        }
    }

    /**
     * Save result to file
     */
    saveResult(account, status, extraData = {}) {
        const timestamp = new Date().toISOString();

        if (status === 'success') {
            const line = `${account.email}|${account.password}|${extraData.temp_email}|${extraData.otp}|${timestamp}\n`;
            fs.appendFileSync('success.txt', line);
            this.results.success++;
        } else {
            const line = `${account.email}|${extraData.error}|${timestamp}\n`;
            fs.appendFileSync('failed.txt', line);
            this.results.failed++;
        }

        // Notify GUI to refresh results
        if (this.mainWindow) {
            this.mainWindow.webContents.send('result', this.results);
        }
    }

    /**
     * Main entry point - process all accounts
     */
    async start(accounts) {
        this.isRunning = true;
        this.results = { success: 0, failed: 0, total: accounts.length };

        const startTime = Date.now();
        this.log(`🚀 Starting signup for ${accounts.length} accounts...`, 'info');

        for (let i = 0; i < accounts.length && this.isRunning; i++) {
            const account = accounts[i];
            const current = i + 1;

            this.updateProgress(current, accounts.length, `Processing ${current}/${accounts.length}...`);
            this.log(`\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`, 'info');
            this.log(`[${current}/${accounts.length}] Processing: ${account.email}`, 'info');

            try {
                await this.signupAccount(account);
            } catch (error) {
                this.log(`❌ Error: ${error.message}`, 'error');
                this.saveResult(account, 'failed', { error: error.message });
            }
        }

        const totalTime = Math.round((Date.now() - startTime) / 1000);
        this.log(`\n✅ Completed! Success: ${this.results.success}, Failed: ${this.results.failed}`, 'success');

        if (this.mainWindow) {
            this.mainWindow.webContents.send('complete', {
                ...this.results,
                totalTime
            });
        }
    }

    /**
     * Signup single account - Main flow
     */
    async signupAccount(account) {
        const { email, password, firstname, lastname } = account;
        let tempEmail = null;
        let otp = null;

        try {
            // Step 1: Generate temp email
            this.log('📧 Step 1/10: Generating temp email...', 'info');
            tempEmail = await generateEmail();
            this.log(`✅ Temp email: ${tempEmail}`, 'success');

            // Step 2: Launch browser
            this.log('🌐 Step 2/10: Launching browser...', 'info');

            // Find Chrome executable
            const chromePaths = [
                'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
                process.env.LOCALAPPDATA + '\\Google\\Chrome\\Application\\chrome.exe'
            ];

            let executablePath = chromePaths.find(p => require('fs').existsSync(p));
            if (!executablePath) {
                throw new Error('Chrome not found. Please install Google Chrome.');
            }

            this.browser = await puppeteer.launch({
                executablePath,
                headless: this.options.headless || false,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled'
                ],
                defaultViewport: { width: 1280, height: 720 }
            });

            const page = await this.browser.newPage();

            // Step 3: Navigate to signup page
            this.log('🔗 Step 3/10: Navigating to signup page...', 'info');
            await page.goto('https://accounts.x.ai/sign-up', {
                waitUntil: 'networkidle2',
                timeout: 30000
            });
            this.log('✅ Page loaded', 'success');

            // Step 4: Click "Sign up with email" button
            this.log('🖱️ Step 4/10: Clicking "Sign up with email"...', 'info');
            await page.waitForSelector('button svg.lucide-mail', { timeout: 10000 });
            await page.evaluate(() => {
                const button = document.querySelector('button svg.lucide-mail').closest('button');
                button.click();
            });
            await page.waitForTimeout(2000);
            this.log('✅ Button clicked', 'success');

            // Step 5: Fill temp email
            this.log('📝 Step 5/10: Filling email...', 'info');
            await page.waitForSelector('[data-testid="email"]', { timeout: 10000 });
            await page.type('[data-testid="email"]', tempEmail, { delay: 50 });
            await page.keyboard.press('Enter');
            this.log('✅ Email submitted', 'success');

            // Step 6: Wait for OTP screen & get OTP
            this.log('⏳ Step 6/10: Waiting for OTP...', 'info');
            await page.waitForSelector('[name="code"]', { timeout: 15000 });
            this.log('📬 Checking email for OTP code...', 'info');
            otp = await checkEmailForCode(tempEmail);

            if (!otp) {
                throw new Error('Failed to retrieve OTP code');
            }
            this.log(`✅ Got OTP: ${otp}`, 'success');

            // Step 7: Fill OTP
            this.log('🔑 Step 7/10: Entering OTP...', 'info');
            await page.type('[name="code"]', otp, { delay: 100 });
            await page.waitForTimeout(1000);
            this.log('✅ OTP entered', 'success');

            // Step 8: Click "Confirm email"
            this.log('✔️ Step 8/10: Confirming email...', 'info');
            await page.evaluate(() => {
                const button = Array.from(document.querySelectorAll('button[type="submit"]'))
                    .find(btn => btn.textContent.includes('Confirm email'));
                if (button) button.click();
            });
            await page.waitForTimeout(3000);
            this.log('✅ Email confirmed', 'success');

            // Step 9: Complete signup form
            this.log('📝 Step 9/10: Filling signup form...', 'info');
            await page.waitForSelector('[data-testid="givenName"]', { timeout: 10000 });
            await page.type('[data-testid="givenName"]', firstname, { delay: 50 });
            await page.type('[data-testid="familyName"]', lastname, { delay: 50 });
            await page.type('[data-testid="password"]', password, { delay: 50 });
            await page.waitForTimeout(1000);

            // Click "Complete sign up"
            await page.evaluate(() => {
                const button = Array.from(document.querySelectorAll('button[type="submit"]'))
                    .find(btn => btn.textContent.includes('Complete sign up'));
                if (button) button.click();
            });
            await page.waitForTimeout(5000);
            this.log('✅ Signup form submitted', 'success');

            // Step 10: Verify success
            this.log('✅ Step 10/10: Verifying account...', 'info');
            const response = await page.goto('https://grok.com/rest/tasks');
            const data = await response.json();

            if (data.taskUsage && data.taskUsage.limit) {
                this.log(`🎉 SUCCESS! Account created: ${email}`, 'success');
                this.saveResult(account, 'success', { temp_email: tempEmail, otp });
            } else {
                throw new Error('Success verification failed - no taskUsage in response');
            }

        } catch (error) {
            this.log(`❌ Signup failed: ${error.message}`, 'error');
            this.saveResult(account, 'failed', { error: error.message });
            throw error;
        } finally {
            // Close browser
            if (this.browser) {
                await this.browser.close();
                this.browser = null;
            }
        }
    }

    /**
     * Stop processing
     */
    async stop() {
        this.isRunning = false;
        this.log('⏸️ Stopping...', 'warning');
        await this.closeAllBrowsers();
    }

    /**
     * Close all browser instances
     */
    async closeAllBrowsers() {
        if (this.browser) {
            await this.browser.close();
            this.browser = null;
        }
    }
}

module.exports = { GrokWorker };
