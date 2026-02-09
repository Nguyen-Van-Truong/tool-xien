/**
 * GitHub Signup Worker - Puppeteer Automation
 * Fills signup form and waits for manual captcha/verify
 *
 * GitHub signup is a SINGLE-PAGE form (as of 2025+):
 *   - "Continue with Google" button (DO NOT CLICK!)
 *   - "Continue with Apple" button (DO NOT CLICK!)
 *   - Email input
 *   - Password input
 *   - Username input
 *   - Country/Region select
 *   - Email preferences checkbox
 *   - "Create account" button
 *   - Then Captcha/Verify step
 *
 * Flow: Fill all fields → STOP → user solves captcha → Done/Failed
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

class GitHubWorker {
    constructor(mainWindow, options = {}) {
        this.mainWindow = mainWindow;
        this.browsers = [];
        this.isRunning = false;
        this.headless = options.headless || false;
        this.keepBrowserOpen = (options.keepBrowser !== undefined) ? options.keepBrowser : true;
        this.autofillDelay = (options.autofillDelay || 1) * 1000; // convert to ms
        this.typingDelay = options.typingDelay || 50; // ms per keystroke
        this.autoClickCreate = options.autoClickCreate !== false; // auto click "Create account"
        this.results = { success: 0, failed: 0, total: 0 };
        this.currentAccountIndex = -1;

        // Manual wait signal mechanism
        this._manualResolve = null;
    }

    log(msg) {
        console.log(msg);
        if (this.mainWindow && this.mainWindow.webContents) {
            this.mainWindow.webContents.send('log', msg);
        }
    }

    sendEvent(channel, data) {
        if (this.mainWindow && this.mainWindow.webContents) {
            this.mainWindow.webContents.send(channel, data);
        }
    }

    updateProgress(current, total, text) {
        this.sendEvent('progress', { current, total, text });
    }

    updateBrowserCount() {
        this.sendEvent('browser-count', { active: this.browsers.length });
    }

    saveResult(account, status, extraData = {}) {
        const timestamp = new Date().toISOString();
        const resultDir = __dirname;

        if (status === 'success') {
            const line = `${account.email}|${account.password}|${account.username}\n`;
            fs.appendFileSync(path.join(resultDir, 'success.txt'), line);
            this.results.success++;
        } else {
            const line = `${account.email}|${account.password}|${extraData.error || 'unknown'}|${timestamp}\n`;
            fs.appendFileSync(path.join(resultDir, 'failed.txt'), line);
            this.results.failed++;
        }

        this.sendEvent('result', {
            email: account.email,
            password: account.password,
            username: account.username,
            status,
            error: extraData.error || '',
            timestamp
        });
    }

    // Called from main process when user clicks "Done" or "Failed"
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

        this.log(`🚀 Bắt đầu đăng ký ${accounts.length} GitHub account(s)...`);

        for (let i = 0; i < accounts.length; i++) {
            if (!this.isRunning) {
                this.log('⏸️ Đã dừng bởi người dùng.');
                break;
            }

            const account = accounts[i];
            this.currentAccountIndex = i;
            const num = i + 1;

            this.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
            this.log(`📌 [${num}/${accounts.length}] ${account.email}`);
            this.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
            this.updateProgress(num, accounts.length, `[${num}/${accounts.length}] ${account.email}`);

            await this.processAccount(account, num, accounts.length);
        }

        const totalTime = Math.round((Date.now() - startTime) / 1000);
        this.log(`\n🎉 Hoàn thành! ✅ ${this.results.success} | ❌ ${this.results.failed} | ⏱ ${totalTime}s`);

        this.sendEvent('complete', {
            total: this.results.total,
            success: this.results.success,
            failed: this.results.failed,
            totalTime
        });
    }

    async processAccount(account, accountNum, total) {
        const { email, password, username } = account;
        let browser = null;
        let page = null;

        try {
            // ===== Step 1: Launch browser =====
            this.log('🌐 Đang mở trình duyệt...');
            const chromePaths = [
                'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
                (process.env.LOCALAPPDATA || '') + '\\Google\\Chrome\\Application\\chrome.exe'
            ];
            const executablePath = chromePaths.find(p => {
                try { return fs.existsSync(p); } catch { return false; }
            });
            if (!executablePath) throw new Error('Không tìm thấy Chrome! Cài Chrome trước.');

            browser = await puppeteer.launch({
                executablePath,
                headless: this.headless ? 'new' : false,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--window-size=1280,850'
                ],
                defaultViewport: { width: 1280, height: 850 }
            });
            this.browsers.push({ browser, email, page: null });
            this.updateBrowserCount();

            page = await browser.newPage();
            this.browsers[this.browsers.length - 1].page = page;

            // Stealth: hide automation flag
            await page.evaluateOnNewDocument(() => {
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            });

            // ===== Step 2: Navigate to GitHub signup =====
            this.log('🔗 Đang truy cập github.com/signup...');
            await page.goto('https://github.com/signup', {
                waitUntil: 'networkidle2',
                timeout: 30000
            });

            // Wait for page to fully load
            await this.sleep(this.autofillDelay);

            // ===== Step 3: Detect page layout - multi-step or single-page =====
            this.log('🔍 Đang phân tích form signup...');
            const formType = await this.detectFormType(page);
            this.log(`   📋 Form type: ${formType}`);

            if (formType === 'multi-step') {
                await this.fillMultiStepForm(page, email, password, username);
            } else {
                await this.fillSinglePageForm(page, email, password, username);
            }

            // ===== FORM FILLED - Notify user =====
            this.log('');
            this.log('✅ ═════════════════════════════════════════');
            this.log('✅ ĐÃ ĐIỀN XONG TẤT CẢ CÁC FIELD!');

            if (this.autoClickCreate) {
                this.log('🖱️ Đang tìm nút "Create account"...');
                const clicked = await this.clickCreateAccount(page);
                if (clicked) {
                    this.log('✅ Đã bấm "Create account"!');
                } else {
                    this.log('⚠️ Không thấy nút, bạn tự bấm nhé');
                }
            } else {
                this.log('ℹ️ Auto-click Create Account: TẮT');
                this.log('   Bạn hãy tự bấm "Create account"');
            }

            this.log('');
            this.log('⏸️ Hãy hoàn thành CAPTCHA + VERIFY thủ công');
            this.log('⏸️ Rồi bấm "✅ Done" hoặc "❌ Failed" trên UI');
            this.log('═════════════════════════════════════════');

            // Send waiting signal to UI
            this.sendEvent('waiting-manual', { email, username, accountNum, total });

            // ===== WAIT FOR USER =====
            const userStatus = await this.waitForManualCompletion();

            if (userStatus === 'done' || userStatus === 'success') {
                this.log(`🎉 THÀNH CÔNG: ${email} | ${username}`);
                this.saveResult(account, 'success');
            } else if (userStatus === 'stopped') {
                this.log(`⏸️ Đã dừng: ${email}`);
            } else {
                this.log(`❌ THẤT BẠI (user): ${email}`);
                this.saveResult(account, 'failed', { error: 'User marked as failed' });
            }

            // Close browser if not keeping it
            if (!this.keepBrowserOpen) {
                try { await browser.close(); } catch (e) { }
                this.browsers = this.browsers.filter(b => b.browser !== browser);
                this.updateBrowserCount();
            }

        } catch (error) {
            this.log(`❌ LỖI: ${email} - ${error.message}`);
            this.saveResult(account, 'failed', { error: error.message });

            // If browser is open, still wait for user input
            if (browser && !this.headless) {
                this.log('⏸️ Browser vẫn mở, bạn có thể sửa thủ công');
                this.log('   Bấm "Done" hoặc "Failed" để tiếp tục...');

                this.sendEvent('waiting-manual', {
                    email, username, accountNum, total, hasError: true
                });

                const userStatus = await this.waitForManualCompletion();
                if (userStatus === 'done' || userStatus === 'success') {
                    this.log(`🎉 Đã sửa thành công: ${email}`);
                    this.results.failed--;
                    this.saveResult(account, 'success');
                }

                if (!this.keepBrowserOpen) {
                    try { await browser.close(); } catch (e) { }
                    this.browsers = this.browsers.filter(b => b.browser !== browser);
                    this.updateBrowserCount();
                }
            }
        }
    }

    /**
     * Detect if the signup form is multi-step (old) or single-page (new)
     */
    async detectFormType(page) {
        return await page.evaluate(() => {
            const emailInput = document.querySelector('#email, input[name="user[email]"]');
            const passInput = document.querySelector('#password, input[name="user[password]"]');
            const loginInput = document.querySelector('#login, input[name="user[login]"]');

            // If all 3 fields are visible at once → single page
            const isVisible = (el) => {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && style.visibility !== 'hidden'
                    && el.offsetWidth > 0 && el.offsetHeight > 0;
            };

            const emailVis = isVisible(emailInput);
            const passVis = isVisible(passInput);
            const loginVis = isVisible(loginInput);

            if (emailVis && passVis && loginVis) return 'single-page';
            if (emailVis && !passVis && !loginVis) return 'multi-step';
            return 'single-page'; // default to single-page (current GitHub)
        });
    }

    /**
     * Fill single-page form (current GitHub layout)
     * ALL fields visible at once, just fill them and click Create
     */
    async fillSinglePageForm(page, email, password, username) {
        // Fill Email
        this.log(`📧 Nhập email: ${email}`);
        await this.fillField(page, '#email', email)
            || await this.fillField(page, 'input[name="user[email]"]', email)
            || await this.fillField(page, 'input[type="email"]', email);
        await this.sleep(600);

        // Fill Password
        this.log('🔑 Nhập password...');
        await this.fillField(page, '#password', password)
            || await this.fillField(page, 'input[name="user[password]"]', password)
            || await this.fillField(page, 'input[type="password"]', password);
        await this.sleep(600);

        // Fill Username
        this.log(`👤 Nhập username: ${username}`);
        await this.fillField(page, '#login', username)
            || await this.fillField(page, 'input[name="user[login]"]', username)
            || await this.fillField(page, 'input[name="login"]', username);
        await this.sleep(600);

        // Handle Email Preferences
        await this.handleEmailPreferences(page);
        await this.sleep(500);
    }

    /**
     * Fill multi-step form (old GitHub layout, just in case they revert)
     * Only email visible first → Continue → password → Continue → etc.
     */
    async fillMultiStepForm(page, email, password, username) {
        // Step: Email
        this.log(`📧 Nhập email: ${email}`);
        await this.fillField(page, '#email', email)
            || await this.fillField(page, 'input[type="email"]', email);
        await this.sleep(800);
        await this.clickStepContinue(page);
        await this.sleep(2000);

        // Step: Password
        this.log('🔑 Nhập password...');
        await page.waitForSelector('#password', { visible: true, timeout: 10000 }).catch(() => {});
        await this.fillField(page, '#password', password)
            || await this.fillField(page, 'input[type="password"]', password);
        await this.sleep(800);
        await this.clickStepContinue(page);
        await this.sleep(2000);

        // Step: Username
        this.log(`👤 Nhập username: ${username}`);
        await page.waitForSelector('#login', { visible: true, timeout: 10000 }).catch(() => {});
        await this.fillField(page, '#login', username)
            || await this.fillField(page, 'input[name="login"]', username);
        await this.sleep(800);
        await this.clickStepContinue(page);
        await this.sleep(2000);

        // Step: Email preferences
        await this.handleEmailPreferences(page);
        await this.sleep(500);
        await this.clickStepContinue(page);
        await this.sleep(2000);
    }

    /**
     * Click Continue in multi-step form
     * CAREFULLY avoids "Continue with Google" / "Continue with Apple"
     */
    async clickStepContinue(page) {
        this.log('   ➡️ Clicking Continue...');
        try {
            const clicked = await page.evaluate(() => {
                // Find buttons with data-continue-to attribute (GitHub's step buttons)
                const stepBtns = document.querySelectorAll('button[data-continue-to]');
                for (const btn of stepBtns) {
                    if (btn.offsetParent !== null && btn.offsetWidth > 0) {
                        btn.click();
                        return 'data-continue-to';
                    }
                }

                // Find submit buttons, but SKIP social login ones
                const buttons = Array.from(document.querySelectorAll('button'));
                for (const btn of buttons) {
                    const text = btn.textContent.trim().toLowerCase();
                    // SKIP: "Continue with Google", "Continue with Apple"
                    if (text.includes('google') || text.includes('apple')) continue;
                    // SKIP: "Create account" (that's the final button)
                    if (text.includes('create')) continue;

                    // Match: "Continue" standalone
                    if (text === 'continue' || text === 'next') {
                        if (btn.offsetParent !== null && btn.offsetWidth > 0) {
                            btn.click();
                            return 'text-continue';
                        }
                    }
                }

                return false;
            });

            if (clicked) {
                this.log(`   ✅ Continue clicked (${clicked})`);
            } else {
                this.log('   ⚠️ Continue button not found');
            }
        } catch (e) {
            this.log('   ⚠️ Error clicking Continue: ' + e.message);
        }
    }

    /**
     * Handle email preferences checkbox/input
     */
    async handleEmailPreferences(page) {
        this.log('📩 Xử lý email preferences...');
        try {
            const pref = await page.$('#opt_in');
            if (pref) {
                const inputType = await page.evaluate(el => (el.type || '').toLowerCase(), pref);
                if (inputType === 'checkbox') {
                    const isChecked = await page.evaluate(el => el.checked, pref);
                    if (isChecked) {
                        await pref.click();
                        this.log('   ☑️ Đã bỏ chọn email preferences');
                    }
                } else {
                    await pref.click();
                    await pref.type('n', { delay: 30 });
                }
            } else {
                this.log('   ℹ️ Không thấy email preferences, bỏ qua');
            }
        } catch (e) {
            this.log('   ⚠️ Lỗi email preferences, bỏ qua');
        }
    }

    /**
     * Fill a form field safely - click, clear, then type
     */
    async fillField(page, selector, value) {
        try {
            const el = await page.$(selector);
            if (!el) return false;

            const isVisible = await page.evaluate(el => {
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && style.visibility !== 'hidden'
                    && el.offsetWidth > 0 && el.offsetHeight > 0;
            }, el);
            if (!isVisible) return false;

            // Scroll into view
            await page.evaluate(el => el.scrollIntoView({ block: 'center' }), el);
            await this.sleep(200);

            // Click to focus
            await el.click();
            await this.sleep(150);

            // Clear existing value
            await page.evaluate(el => { el.value = ''; }, el);
            await el.click({ clickCount: 3 });
            await page.keyboard.press('Backspace');
            await this.sleep(100);

            // Type with human-like delay
            await el.type(value, { delay: this.typingDelay });

            // Trigger events for form validation
            await page.evaluate(el => {
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('blur', { bubbles: true }));
            }, el);

            return true;
        } catch (e) {
            return false;
        }
    }

    /**
     * Click "Create account" button
     * CAREFULLY avoids "Continue with Google/Apple" buttons
     */
    async clickCreateAccount(page) {
        try {
            // Strategy 1: Find button with exact text "Create account"
            const clicked = await page.evaluate(() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                for (const btn of buttons) {
                    const text = btn.textContent.trim().toLowerCase();
                    if (text === 'create account' || text === 'create your account') {
                        if (btn.offsetParent !== null && btn.offsetWidth > 0) {
                            btn.click();
                            return true;
                        }
                    }
                }
                return false;
            });
            if (clicked) return true;

            // Strategy 2: Submit button that is NOT social login
            const clicked2 = await page.evaluate(() => {
                const buttons = Array.from(document.querySelectorAll('button[type="submit"]'));
                for (const btn of buttons) {
                    const text = btn.textContent.trim().toLowerCase();
                    if (text.includes('google') || text.includes('apple') || text.includes('continue with'))
                        continue;
                    if (btn.offsetParent !== null && btn.offsetWidth > 0) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            });
            if (clicked2) return true;

            // Strategy 3: data-attribute based
            const selectors = [
                'button.js-octocaptcha-form-submit',
                'button[data-target="signup-form.SignupButton"]',
                'input[type="submit"][value*="Create"]',
            ];
            for (const sel of selectors) {
                try {
                    const btn = await page.$(sel);
                    if (btn) { await btn.click(); return true; }
                } catch (e) { }
            }

            return false;
        } catch (e) {
            return false;
        }
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Stop processing - but DO NOT close browsers
     */
    async stop() {
        this.isRunning = false;
        this.log('⏸️ Đã dừng xử lý. Browsers vẫn mở.');
        if (this._manualResolve) {
            this._manualResolve('stopped');
        }
    }

    /**
     * Close ALL open browsers
     */
    async closeAllBrowsers() {
        const count = this.browsers.length;
        if (count === 0) {
            this.log('ℹ️ Không có browser nào đang mở.');
            return;
        }
        this.log(`🗑️ Đang đóng ${count} browser(s)...`);
        for (const b of this.browsers) {
            try { await b.browser.close(); } catch (e) { }
        }
        this.browsers = [];
        this.updateBrowserCount();
        this.log(`✅ Đã đóng tất cả ${count} browser(s).`);
    }
}

module.exports = { GitHubWorker };
