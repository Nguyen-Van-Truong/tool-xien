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
            // Format: grok_email|password (temp email used for Grok)
            const grokEmail = extraData.grokEmail;
            const line = `${grokEmail}|${account.password}\n`;
            fs.appendFileSync('success.txt', line);
            this.results.success++;
        } else {
            // Failed format: email|error|timestamp (for debugging)
            const failedEmail = extraData.grokEmail || 'unknown';
            const line = `${failedEmail}|${extraData.error}|${timestamp}\n`;
            fs.appendFileSync('failed.txt', line);
            this.results.failed++;
        }
        if (this.mainWindow) {
            this.mainWindow.webContents.send('result', this.results);
        }
    }

    // Generate random password
    generateRandomPassword(length = 12) {
        const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%';
        let password = '';
        for (let i = 0; i < length; i++) {
            password += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return password;
    }

    // Generate accounts based on config
    generateAccounts(config) {
        const { count, passwordMode, customPassword } = config;
        const firstNames = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emma', 'James', 'Emily', 'Robert', 'Olivia', 'William', 'Sophia', 'Benjamin', 'Isabella', 'Daniel', 'Mia', 'Alexander', 'Charlotte', 'Henry', 'Amelia'];
        const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Martinez', 'Lopez', 'Wilson', 'Anderson', 'Taylor', 'Thomas', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White'];

        const accounts = [];
        for (let i = 0; i < count; i++) {
            accounts.push({
                password: passwordMode === 'custom' ? customPassword : this.generateRandomPassword(),
                firstname: firstNames[Math.floor(Math.random() * firstNames.length)],
                lastname: lastNames[Math.floor(Math.random() * lastNames.length)]
            });
        }
        return accounts;
    }

    async start(config) {
        this.isRunning = true;
        
        // Generate accounts from config
        const accounts = this.generateAccounts(config);
        this.results = { success: 0, failed: 0, total: accounts.length };
        const startTime = Date.now();

        this.log(`🚀 Starting signup for ${accounts.length} accounts (max ${this.maxConcurrent} concurrent)...`, 'info');

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
                    const result = await this.signupAccount(account, accountNum, accounts.length);
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

    async signupAccount(account, accountNum, total) {
        const { password, firstname, lastname } = account;
        let browser = null;
        let tempEmailData = null;

        try {
            this.log(`\n━━ [${accountNum}/${total}] Creating account... ━━`, 'info');
            this.updateProgress(accountNum, total, `Processing ${accountNum}/${total}...`);

            // Generate temp email
            this.log('📧 1/12: Generating temp email...', 'info');
            tempEmailData = await generateEmail();
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
                headless: this.headless ? 'new' : false,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled'
                ],
                defaultViewport: { width: 1280, height: 720 }
            });
            this.browsers.push({ browser, email: tempEmailData.email });
            this.updateBrowserCount();
            const page = await browser.newPage();

            // Stealth: Only hide webdriver flag (keep everything else real)
            // DO NOT override window.chrome - we use real Chrome, fake object makes it worse
            await page.evaluateOnNewDocument(() => {
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            });

            // Navigate
            this.log('🔗 3/12: Navigating...', 'info');
            await page.goto('https://accounts.x.ai/sign-up', { waitUntil: 'networkidle2', timeout: 30000 });

            // Click "Sign up with email" - with multiple selector fallbacks
            this.log('🖱️ 4/12: Clicking email button...', 'info');
            let emailBtnClicked = false;
            
            // Strategy 1: Try lucide-mail SVG icon
            try {
                await page.waitForSelector('button svg.lucide-mail', { timeout: 8000, visible: true });
                await page.evaluate(() => document.querySelector('button svg.lucide-mail').closest('button').click());
                emailBtnClicked = true;
            } catch (e) {
                this.log('⚠️ SVG selector failed, trying fallback...', 'warning');
            }

            // Strategy 2: Find button containing "email" text
            if (!emailBtnClicked) {
                try {
                    await page.waitForTimeout(2000);
                    emailBtnClicked = await page.evaluate(() => {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const emailBtn = buttons.find(b => {
                            const text = b.textContent.toLowerCase();
                            return text.includes('email') || text.includes('mail');
                        });
                        if (emailBtn) { emailBtn.click(); return true; }
                        return false;
                    });
                } catch (e) {
                    this.log('⚠️ Text fallback failed...', 'warning');
                }
            }

            // Strategy 3: Try any mail-related SVG or icon
            if (!emailBtnClicked) {
                try {
                    emailBtnClicked = await page.evaluate(() => {
                        // Look for any button with an SVG that has a mail-like path
                        const svgs = document.querySelectorAll('button svg');
                        for (const svg of svgs) {
                            const paths = svg.querySelectorAll('path');
                            const classList = Array.from(svg.classList);
                            if (classList.some(c => c.includes('mail') || c.includes('email')) || paths.length > 0) {
                                const btn = svg.closest('button');
                                if (btn && btn.offsetParent !== null) {
                                    btn.click();
                                    return true;
                                }
                            }
                        }
                        // Last resort: 3rd button on page (often the email option)
                        const allBtns = document.querySelectorAll('button');
                        if (allBtns.length >= 3) {
                            allBtns[allBtns.length - 1].click();
                            return true;
                        }
                        return false;
                    });
                } catch (e) {
                    this.log('⚠️ SVG path fallback failed...', 'warning');
                }
            }

            if (!emailBtnClicked) {
                throw new Error('Could not find email signup button');
            }
            
            this.log('✅ Email button clicked!', 'success');
            await page.waitForTimeout(2000);

            // Fill email
            this.log('📝 5/12: Filling email...', 'info');
            await page.waitForSelector('[data-testid="email"]', { timeout: 10000 });
            await page.type('[data-testid="email"]', tempEmailData.email, { delay: 80 });
            
            // Wait for Cloudflare Turnstile to pass BEFORE submitting email
            this.log('🔄 5.5/12: Waiting for Cloudflare Turnstile...', 'info');
            let turnstilePassed = false;
            for (let i = 0; i < 30 && !turnstilePassed; i++) {
                turnstilePassed = await page.evaluate(() => {
                    // Check if Turnstile response token exists (means challenge solved)
                    const cfInput = document.querySelector('input[name="cf-turnstile-response"]');
                    if (cfInput && cfInput.value && cfInput.value.length > 10) return true;
                    
                    // Also check for Turnstile solved state
                    const wrapper = document.querySelector('[data-status="solved"]');
                    if (wrapper) return true;
                    
                    // Check if NO Turnstile at all (page doesn't use it)
                    const cfIframe = document.querySelector('iframe[src*="challenges.cloudflare.com"]');
                    const cfWidget = document.querySelector('.cf-turnstile');
                    if (!cfIframe && !cfWidget) return true;
                    
                    return false;
                });
                
                if (!turnstilePassed) {
                    if (i === 0) this.log('⏳ Cloudflare Turnstile detected, waiting for it to solve...', 'info');
                    if (i > 0 && i % 10 === 0) this.log(`⏳ Still waiting for Turnstile... (${i}s)`, 'info');
                    await page.waitForTimeout(1000);
                }
            }
            
            if (turnstilePassed) {
                this.log('✅ Cloudflare Turnstile passed!', 'success');
            } else {
                this.log('⚠️ Turnstile may not have passed, trying submit anyway...', 'warning');
            }
            
            // Now submit email
            await page.keyboard.press('Enter');

            // Get OTP
            this.log('⏳ 6/12: Waiting for OTP page...', 'info');
            
            // Check if we got past the email step (no 403 error)
            await page.waitForTimeout(3000);
            
            // Check for error on page 
            const hasError = await page.evaluate(() => {
                const text = document.body.innerText || '';
                return text.includes('403') || text.includes('permission_denied') || text.includes('Error');
            });
            
            if (hasError) {
                // Check if it's actually a Cloudflare error vs Turnstile widget showing "Error"
                const isReal403 = await page.evaluate(() => {
                    const text = document.body.innerText || '';
                    return text.includes('403') || text.includes('permission_denied');
                });
                if (isReal403) {
                    throw new Error('403 Permission Denied - Cloudflare blocked the request');
                }
            }
            
            await page.waitForSelector('[name="code"]', { timeout: 20000 });
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

            // Complete signup - wait for Cloudflare Turnstile to pass first
            this.log('✔️ 10/12: Waiting for Cloudflare verification...', 'info');
            
            // Wait for Cloudflare Turnstile to complete (check for success state)
            let cfPassed = false;
            for (let i = 0; i < 30 && !cfPassed; i++) {
                cfPassed = await page.evaluate(() => {
                    // Check if Turnstile iframe exists and has resolved
                    const cfIframe = document.querySelector('iframe[src*="challenges.cloudflare.com"]');
                    if (!cfIframe) return true; // No Cloudflare = proceed
                    
                    // Check for success response token
                    const cfInput = document.querySelector('input[name="cf-turnstile-response"]');
                    if (cfInput && cfInput.value && cfInput.value.length > 0) return true;
                    
                    // Check checkbox state inside iframe (can't access cross-origin, check wrapper)
                    const wrapper = document.querySelector('.cf-turnstile');
                    if (wrapper && wrapper.getAttribute('data-status') === 'solved') return true;
                    
                    return false;
                });
                
                if (!cfPassed) {
                    if (i === 0) this.log('🔄 Cloudflare Turnstile detected, waiting...', 'info');
                    if (i > 0 && i % 5 === 0) this.log(`⏳ Still waiting for Cloudflare... (${i}s)`, 'info');
                    await page.waitForTimeout(1000);
                }
            }
            
            if (cfPassed) {
                this.log('✅ Cloudflare verification passed!', 'success');
            } else {
                this.log('⚠️ Cloudflare might not have passed, attempting submit anyway...', 'warning');
            }
            
            // Now click Complete sign up
            this.log('🚀 Submitting signup...', 'info');
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
                this.log(`🎉 SUCCESS: ${tempEmailData.email}`, 'success');
                this.saveResult(account, 'success', { grokEmail: tempEmailData.email });
            }

        } catch (error) {
            this.log(`❌ FAILED: ${error.message}`, 'error');
            this.saveResult(account, 'failed', { 
                error: error.message, 
                grokEmail: tempEmailData ? tempEmailData.email : null 
            });
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
