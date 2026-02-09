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
const https = require('https');

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
        this._stopPolling = false;
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
            const hasAPICreds = account.refreshToken && account.clientId;

            if (hasAPICreds) {
                this.log('🔄 AUTO-OTP ENABLED - Sẽ tự lấy OTP từ email');
                this.log('⏸️ Hãy giải CAPTCHA, tool sẽ tự detect verification page...');
                this.log('   (Poll URL mỗi 10 giây)');
            } else {
                this.log('⏸️ Hãy hoàn thành CAPTCHA + VERIFY thủ công');
                this.log('⏸️ Rồi bấm "✅ Done" hoặc "❌ Failed" trên UI');
            }
            this.log('═════════════════════════════════════════');

            // Send waiting signal to UI
            this.sendEvent('waiting-manual', {
                email, username, accountNum, total,
                autoOTP: hasAPICreds
            });

            // Start background OTP polling if API credentials available
            if (hasAPICreds) {
                this.pollOTPInBackground(page, account);
            }

            // ===== WAIT FOR USER (or auto-OTP resolution) =====
            const userStatus = await this.waitForManualCompletion();
            this._stopPolling = true; // Stop any background polling

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

    // ==================== OTP AUTO-FETCH METHODS ====================

    /**
     * POST JSON to a URL and return parsed response
     */
    postJSON(url, data, timeout = 20000) {
        return new Promise((resolve, reject) => {
            const urlObj = new URL(url);
            const postData = JSON.stringify(data);
            const options = {
                hostname: urlObj.hostname,
                port: urlObj.port || 443,
                path: urlObj.pathname + urlObj.search,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(postData)
                }
            };
            const req = https.request(options, (res) => {
                let body = '';
                res.on('data', chunk => body += chunk);
                res.on('end', () => {
                    try { resolve(JSON.parse(body)); }
                    catch (e) { reject(new Error(`Invalid JSON: ${body.substring(0, 200)}`)); }
                });
            });
            req.on('error', reject);
            req.setTimeout(timeout, () => { req.destroy(); reject(new Error('Request timeout')); });
            req.write(postData);
            req.end();
        });
    }

    /**
     * Fetch OTP code from email via dongvanfb API
     * Strategy 1: get_code_oauth2 (type: all)
     * Strategy 2: get_messages_oauth2 + parse GitHub message
     */
    async fetchOTPFromEmail(email, refreshToken, clientId) {
        // Strategy 1: get_code_oauth2 with type "all"
        try {
            this.log('   📧 Gọi API get_code_oauth2 (type: all)...');
            const codeResp = await this.postJSON('https://tools.dongvanfb.net/api/get_code_oauth2', {
                email, refresh_token: refreshToken, client_id: clientId, type: 'all'
            });
            if (codeResp && codeResp.status && codeResp.code && codeResp.code.toString().trim()) {
                const code = codeResp.code.toString().trim();
                this.log(`   ✅ get_code_oauth2 trả về code: ${code}`);
                // Verify it looks like a GitHub code (usually 6-8 digits)
                if (/^\d{5,8}$/.test(code)) return code;
                this.log(`   ⚠️ Code không hợp lệ (${code}), thử cách 2...`);
            } else {
                this.log(`   ⚠️ get_code_oauth2: không có code (status: ${codeResp?.status})`);
            }
        } catch (e) {
            this.log(`   ⚠️ get_code_oauth2 error: ${e.message}`);
        }

        // Strategy 2: get_messages_oauth2 + parse from GitHub email
        try {
            this.log('   📧 Gọi API get_messages_oauth2...');
            const msgResp = await this.postJSON('https://tools.dongvanfb.net/api/get_messages_oauth2', {
                email, refresh_token: refreshToken, client_id: clientId
            });

            if (!msgResp || !msgResp.status) {
                this.log(`   ❌ API trả về status: ${msgResp?.status}`);
                return null;
            }
            if (!msgResp.messages || msgResp.messages.length === 0) {
                this.log('   ⚠️ Không có message nào');
                return null;
            }

            this.log(`   📬 Có ${msgResp.messages.length} message(s)`);

            // Sort by date desc (newest first)
            const sorted = [...msgResp.messages].sort((a, b) =>
                new Date(b.date || 0) - new Date(a.date || 0)
            );

            for (const msg of sorted) {
                const fromAddrs = (msg.from || []).map(f => (f.address || '').toLowerCase());
                const subject = (msg.subject || '').toLowerCase();
                const isGithub = fromAddrs.some(a => a.includes('github')) || subject.includes('github');
                if (!isGithub) continue;

                this.log(`   📨 GitHub email: "${msg.subject}"`);

                // Check API-extracted code first
                if (msg.code && msg.code.toString().trim()) {
                    const code = msg.code.toString().trim();
                    if (/^\d{5,8}$/.test(code)) {
                        this.log(`   🔑 Code from message: ${code}`);
                        return code;
                    }
                }

                // Parse from subject + content
                const fullText = `${msg.subject || ''} ${msg.message || ''}`;
                const patterns = [
                    /code\s*(?:below|is)?[:\s]+?(\d{5,8})/i,
                    /launch\s*code[:\s]*?(\d{5,8})/i,
                    /verification\s*code[:\s]*?(\d{5,8})/i,
                    /\b(\d{7})\b/,   // GitHub uses 7-digit codes
                    /\b(\d{6})\b/,   // fallback 6-digit
                ];
                for (const pattern of patterns) {
                    const match = fullText.match(pattern);
                    if (match) {
                        this.log(`   🔑 Extracted code: ${match[1]}`);
                        return match[1];
                    }
                }
                this.log('   ⚠️ GitHub email found nhưng không extract được code');
            }

            this.log('   ⚠️ Không tìm thấy email từ GitHub');
        } catch (e) {
            this.log(`   ❌ get_messages_oauth2 error: ${e.message}`);
        }

        return null;
    }

    /**
     * Fill OTP code on the GitHub verification page
     */
    async fillOTPCode(page, code) {
        try {
            await this.sleep(1500);

            // Strategy 1: Known selectors for OTP input
            const otpSelectors = [
                'input#otp', 'input[name="otp"]',
                'input[autocomplete="one-time-code"]',
                'input.js-verification-code',
                'input[data-target*="verification"]',
                'input[placeholder*="XXXXXX"]',
                'input[aria-label*="code" i]',
                'input[aria-label*="verification" i]',
                'input[aria-label*="launch" i]',
            ];
            for (const sel of otpSelectors) {
                const filled = await this.fillField(page, sel, code);
                if (filled) {
                    this.log(`   ✅ Nhập OTP qua: ${sel}`);
                    return true;
                }
            }

            // Strategy 2: Any visible text/number/tel input
            const fallback = await page.evaluate((code) => {
                const inputs = document.querySelectorAll(
                    'input[type="text"], input[type="number"], input[type="tel"], input:not([type])'
                );
                for (const inp of inputs) {
                    if (inp.offsetWidth > 0 && inp.offsetHeight > 0
                        && !inp.readOnly && !inp.disabled && inp.type !== 'hidden') {
                        inp.focus();
                        inp.value = '';
                        inp.value = code;
                        inp.dispatchEvent(new Event('input', { bubbles: true }));
                        inp.dispatchEvent(new Event('change', { bubbles: true }));
                        return true;
                    }
                }
                return false;
            }, code);
            if (fallback) {
                this.log('   ✅ Nhập OTP (fallback selector)');
                return true;
            }

            // Strategy 3: Multiple single-digit inputs
            const multiDigit = await page.evaluate((code) => {
                const digitInputs = document.querySelectorAll('input[maxlength="1"]');
                if (digitInputs.length >= 6 && digitInputs.length <= 8) {
                    const digits = code.toString().split('');
                    for (let i = 0; i < Math.min(digits.length, digitInputs.length); i++) {
                        digitInputs[i].focus();
                        digitInputs[i].value = digits[i];
                        digitInputs[i].dispatchEvent(new Event('input', { bubbles: true }));
                    }
                    return true;
                }
                return false;
            }, code);
            if (multiDigit) {
                this.log('   ✅ Nhập OTP (multi-digit inputs)');
                return true;
            }

            this.log('   ⚠️ Không tìm thấy input OTP trên trang');
            return false;
        } catch (e) {
            this.log(`   ❌ Lỗi nhập OTP: ${e.message}`);
            return false;
        }
    }

    /**
     * Try to click Verify/Submit button after OTP entry
     */
    async clickVerifyButton(page) {
        try {
            const clicked = await page.evaluate(() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                for (const btn of buttons) {
                    const text = btn.textContent.trim().toLowerCase();
                    if (text.includes('verify') || text.includes('submit')
                        || text.includes('continue') || text.includes('xác minh')
                        || text.includes('xác nhận')) {
                        if (btn.offsetParent !== null && btn.offsetWidth > 0) {
                            btn.click();
                            return true;
                        }
                    }
                }
                const inputs = Array.from(document.querySelectorAll('input[type="submit"]'));
                for (const inp of inputs) {
                    if (inp.offsetWidth > 0) { inp.click(); return true; }
                }
                return false;
            });
            if (clicked) this.log('   🖱️ Đã bấm nút Verify/Submit');
            return clicked;
        } catch (e) { return false; }
    }

    /**
     * Background polling for verification page + auto-fill OTP
     * Runs concurrently with manual wait - resolves when OTP entered
     */
    async pollOTPInBackground(page, account) {
        this._stopPolling = false;
        const pollInterval = 10000; // 10s
        const maxAttempts = 60;     // 10 minutes max
        const maxOTPRetries = 6;    // retry OTP fetch 6 times (1 min)

        this.log('🔄 Bắt đầu poll URL mỗi 10s...');

        for (let i = 0; i < maxAttempts; i++) {
            await this.sleep(pollInterval);
            if (this._stopPolling || !this.isRunning) {
                this.log('   ⏹️ Dừng polling');
                return;
            }

            try {
                const url = page.url();

                // Log every 3rd poll (every 30s)
                if (i % 3 === 0) {
                    this.log(`   🔍 Poll #${i + 1} (${(i + 1) * 10}s): ${url.substring(0, 60)}...`);
                }

                // Detect verification page
                if (url.includes('account_verifications') || url.includes('account/verifications')) {
                    this.log('🎯 ĐÃ PHÁT HIỆN TRANG VERIFICATION!');
                    this.sendEvent('otp-status', { status: 'fetching', email: account.email });

                    // Retry fetching OTP (email might be delayed)
                    for (let retry = 0; retry < maxOTPRetries; retry++) {
                        if (this._stopPolling) return;

                        if (retry > 0) {
                            this.log(`   🔄 Thử lại lấy OTP (${retry + 1}/${maxOTPRetries})...`);
                            await this.sleep(10000);
                        }

                        const code = await this.fetchOTPFromEmail(
                            account.email, account.refreshToken, account.clientId
                        );

                        if (code) {
                            this.log(`🔑 OTP CODE: ${code}`);
                            this.sendEvent('otp-status', { status: 'filling', code });

                            const filled = await this.fillOTPCode(page, code);
                            if (filled) {
                                this.log('✅ Đã nhập OTP thành công!');

                                // Try clicking verify button
                                await this.sleep(500);
                                await this.clickVerifyButton(page);
                                await this.sleep(3000);

                                // Check if moved past verification
                                const newUrl = page.url();
                                if (!newUrl.includes('account_verifications')) {
                                    this.log('🎉 Verification OK! Đã qua trang verification.');
                                    this.sendEvent('otp-status', { status: 'success' });
                                    this.resolveManualWait('done');
                                } else {
                                    this.log('ℹ️ Vẫn ở trang verification - có thể cần thêm thao tác');
                                    this.sendEvent('otp-status', { status: 'filled', code });
                                    // Don't auto-resolve, let user handle
                                }
                                return;
                            }
                        }
                    }

                    this.log('⚠️ Không lấy được OTP sau nhiều lần thử. Hãy nhập thủ công.');
                    this.sendEvent('otp-status', { status: 'failed' });
                    return;
                }

                // Check if somehow already completed (not on signup/verify pages)
                if (!url.includes('signup') && !url.includes('account_verifications')
                    && !url.includes('captcha') && url.includes('github.com')) {
                    // Could be dashboard - user completed manually
                    if (url === 'https://github.com/' || url.includes('/dashboard')) {
                        this.log('🎯 Phát hiện dashboard - signup đã hoàn thành!');
                        return;
                    }
                }

            } catch (e) {
                // Page might be navigating, ignore
            }
        }

        this.log('⏰ Timeout polling (10 phút). Hãy xử lý thủ công.');
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
