/**
 * TDC Login Worker - Đăng nhập Google, xử lý speedbump, lưu kết quả
 */
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');

puppeteer.use(StealthPlugin());

const BROWSER_LIST = [
    {
        name: 'Google Chrome', id: 'chrome',
        paths: [
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
            (process.env.LOCALAPPDATA || '') + '\\Google\\Chrome\\Application\\chrome.exe',
        ]
    },
    {
        name: 'Microsoft Edge', id: 'edge',
        paths: [
            'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
            'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
        ]
    },
    {
        name: 'Brave', id: 'brave',
        paths: [
            'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
            (process.env.LOCALAPPDATA || '') + '\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
        ]
    }
];

function detectAllBrowsers() {
    const detected = [];
    detected.push({ id: 'puppeteer', name: 'Puppeteer Chromium (Mặc định)', detected: true, path: null });
    for (const browser of BROWSER_LIST) {
        let foundPath = null;
        for (const p of browser.paths) {
            if (fs.existsSync(p)) { foundPath = p; break; }
        }
        detected.push({ id: browser.id, name: browser.name, detected: !!foundPath, path: foundPath });
    }
    return detected;
}

function getBrowserPath(browserId) {
    const browsers = detectAllBrowsers();
    const browser = browsers.find(b => b.id === browserId && b.detected);
    return browser ? browser.path : null;
}

class LoginWorker {
    constructor(mainWindow, selectedBrowserId = null, options = {}) {
        this.mainWindow = mainWindow;
        this.isRunning = false;
        this.browsers = [];
        this.selectedBrowserId = selectedBrowserId;
        this.headless = options.headless || false;

        if (process.env.PORTABLE_EXECUTABLE_DIR) {
            this.basePath = process.env.PORTABLE_EXECUTABLE_DIR;
        } else if (process.resourcesPath && !process.resourcesPath.includes('node_modules')) {
            this.basePath = path.dirname(process.resourcesPath);
        } else {
            this.basePath = __dirname;
        }

        this.PASSED_FILE = path.join(this.basePath, 'passed.txt');
        this.HAS_PHONE_FILE = path.join(this.basePath, 'has_phone.txt');
        this.NEED_PHONE_FILE = path.join(this.basePath, 'need_phone.txt');
        this.FAILED_FILE = path.join(this.basePath, 'login_failed.txt');
    }

    log(message, type = 'info') {
        if (this.mainWindow) this.mainWindow.webContents.send('log', { message, type });
        console.log(message);
    }

    sendProgress(current, total, text) {
        if (this.mainWindow) this.mainWindow.webContents.send('progress', { current, total, text });
    }

    sendResult(result) {
        if (this.mainWindow) this.mainWindow.webContents.send('result', result);
    }

    sendComplete(data) {
        if (this.mainWindow) this.mainWindow.webContents.send('complete', data);
    }

    delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

    resetResultsFile() {
        fs.writeFileSync(this.PASSED_FILE, '');
        fs.writeFileSync(this.HAS_PHONE_FILE, '');
        fs.writeFileSync(this.NEED_PHONE_FILE, '');
        fs.writeFileSync(this.FAILED_FILE, '');
        this.log('🗑️ Đã xóa kết quả cũ', 'info');
    }

    saveResult(result) {
        const line = `${result.email}|${result.password}\n`;
        if (result.status === 'PASSED') {
            fs.appendFileSync(this.PASSED_FILE, line);
        } else if (result.status === 'HAS_PHONE') {
            fs.appendFileSync(this.HAS_PHONE_FILE, line);
        } else if (result.status === 'NEED_PHONE') {
            fs.appendFileSync(this.NEED_PHONE_FILE, line);
        } else {
            fs.appendFileSync(this.FAILED_FILE, line);
        }
        this.sendResult(result);
    }

    async fastType(page, selector, text) {
        await page.waitForSelector(selector, { visible: true, timeout: 15000 });
        await page.click(selector);
        await this.delay(100);
        await page.evaluate((sel, txt) => {
            const el = document.querySelector(sel);
            if (el) {
                el.value = txt;
                el.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }, selector, text);
        await this.delay(100);
    }

    async loginAccount(email, password, index, total) {
        if (!this.isRunning) return null;

        const startTime = Date.now();
        this.log(`[${index + 1}/${total}] 🚀 ${email}`, 'info');
        this.sendProgress(index, total, `${index + 1}/${total}: ${email}`);

        let browserPath = null;
        if (this.selectedBrowserId && this.selectedBrowserId !== 'puppeteer') {
            browserPath = getBrowserPath(this.selectedBrowserId);
        }

        const launchArgs = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--start-maximized'
        ];

        const launchOptions = {
            headless: this.headless ? 'new' : false,
            args: launchArgs,
            defaultViewport: this.headless ? { width: 1280, height: 720 } : null
        };

        if (browserPath) launchOptions.executablePath = browserPath;

        let browser;
        try {
            browser = await puppeteer.launch(launchOptions);
        } catch (err) {
            this.log(`   ❌ Không mở được browser: ${err.message}`, 'error');
            const result = { email, password, status: 'FAILED', reason: 'BROWSER_ERROR', time: 0 };
            this.saveResult(result);
            return result;
        }

        this.browsers.push(browser);
        const page = await browser.newPage();

        await page.setUserAgent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        );
        await page.evaluateOnNewDocument(() => {
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        });

        let result = { email, password, status: 'FAILED', reason: 'UNKNOWN', time: 0 };

        try {
            // Step 1: Vào Google login
            this.log(`   📍 Vào trang đăng nhập Google...`, 'info');
            await page.goto('https://accounts.google.com/signin', {
                waitUntil: 'domcontentloaded',
                timeout: 30000
            });
            await this.delay(2000);

            // Step 2: Nhập email
            this.log(`   📧 Nhập email...`, 'info');
            await this.fastType(page, 'input[type="email"]', email);
            await this.delay(300);

            await page.evaluate(() => {
                const btns = document.querySelectorAll('#identifierNext, button');
                for (const btn of btns) {
                    if (btn.id === 'identifierNext' || btn.textContent.includes('Next') || btn.textContent.includes('Tiếp')) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            });

            await this.delay(4000);

            // Check email errors
            const afterEmailContent = await page.content();
            const afterEmailUrl = page.url();

            if (afterEmailUrl.includes('deletedaccount') ||
                afterEmailContent.includes('Account deleted') ||
                afterEmailContent.includes('Tài khoản đã bị xóa')) {
                result.reason = 'ACCOUNT_DELETED';
                this.log(`   🗑️ Account đã bị xóa!`, 'error');
                this.saveResult(result);
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                return result;
            }

            if (afterEmailContent.includes("Couldn't find") || afterEmailContent.includes('Không tìm thấy')) {
                result.reason = 'EMAIL_NOT_FOUND';
                this.log(`   ❌ Email không tồn tại!`, 'error');
                this.saveResult(result);
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                return result;
            }

            // Step 3: Nhập password
            try {
                this.log(`   🔐 Chờ trang password...`, 'info');
                await page.waitForSelector('input[type="password"]', { visible: true, timeout: 10000 });

                this.log(`   🔑 Nhập password...`, 'info');
                await this.fastType(page, 'input[type="password"]', password);
                await this.delay(300);

                await page.evaluate(() => {
                    const btns = document.querySelectorAll('#passwordNext, button');
                    for (const btn of btns) {
                        if (btn.id === 'passwordNext' || btn.textContent.includes('Next') || btn.textContent.includes('Tiếp')) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                });

                await this.delay(5000);
            } catch (passError) {
                result.reason = 'NO_PASSWORD_PAGE';
                this.log(`   ⚠️ Không thấy trang password (CAPTCHA?)`, 'warning');
                this.saveResult(result);
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                return result;
            }

            // Step 4: Check kết quả sau login
            const finalContent = await page.content();
            const finalUrl = page.url();

            // Check sai mật khẩu hoặc password đã đổi
            if (finalContent.includes('Wrong password') || finalContent.includes('Sai mật khẩu') ||
                finalContent.includes('password was changed') || finalContent.includes('mật khẩu đã được thay đổi') ||
                finalUrl.includes('challenge/pwd')) {
                result.reason = finalUrl.includes('challenge/pwd') || finalContent.includes('password was changed') || finalContent.includes('mật khẩu đã được thay đổi')
                    ? 'PASSWORD_CHANGED' : 'WRONG_PASSWORD';
                this.log(`   ❌ ${result.reason === 'PASSWORD_CHANGED' ? 'Password đã đổi!' : 'Sai mật khẩu!'}`, 'error');
                this.saveResult(result);
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                return result;
            }

            // Check challenge/dp - đã có SĐT (Google gửi notification qua điện thoại)
            if (finalUrl.includes('challenge/dp') ||
                finalContent.includes('Open the Gmail app') ||
                finalContent.includes('Google sent a notification') ||
                finalContent.includes('Mở ứng dụng Gmail') ||
                finalContent.includes('Google đã gửi thông báo')) {
                result.status = 'HAS_PHONE';
                result.reason = 'HAS_PHONE_VERIFY';
                this.log(`   📱 Đã có SĐT - cần xác minh qua điện thoại`, 'warning');
                this.saveResult(result);
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                return result;
            }

            // Check challenge/iap - chưa có SĐT (cần nhập số điện thoại)
            if (finalUrl.includes('challenge/iap') ||
                finalContent.includes('Enter a phone number') ||
                finalContent.includes('Nhập số điện thoại') ||
                finalContent.includes('get a text message') ||
                finalContent.includes('nhận tin nhắn')) {
                result.status = 'NEED_PHONE';
                result.reason = 'NEED_PHONE_VERIFY';
                this.log(`   📵 Chưa có SĐT - cần nhập số điện thoại`, 'warning');
                this.saveResult(result);
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                return result;
            }

            // Check các challenge khác
            if (finalUrl.includes('challenge') ||
                finalContent.includes('Verify it') || finalContent.includes('Verify your identity') ||
                finalContent.includes('verification code') ||
                finalContent.includes('mã xác minh') ||
                finalContent.includes('Xác minh danh tính')) {
                // Kiểm tra nội dung để phân loại chính xác
                const pageText = await page.evaluate(() => document.body.innerText).catch(() => '');
                if (pageText.includes('Open the Gmail app') || pageText.includes('notification') ||
                    pageText.includes('Mở ứng dụng Gmail')) {
                    result.status = 'HAS_PHONE';
                    result.reason = 'HAS_PHONE_VERIFY';
                    this.log(`   📱 Đã có SĐT - xác minh qua thiết bị`, 'warning');
                } else if (pageText.includes('phone number') || pageText.includes('số điện thoại')) {
                    result.status = 'NEED_PHONE';
                    result.reason = 'NEED_PHONE_VERIFY';
                    this.log(`   📵 Chưa có SĐT - cần nhập SĐT`, 'warning');
                } else {
                    result.status = 'HAS_PHONE';
                    result.reason = 'UNKNOWN_CHALLENGE';
                    this.log(`   📱 Challenge không xác định - lưu HAS_PHONE`, 'warning');
                }
                this.saveResult(result);
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                return result;
            }

            // Step 5: Check speedbump
            if (finalUrl.includes('speedbump')) {
                this.log(`   ⚡ Phát hiện trang Speedbump!`, 'success');
                await this.delay(1500);

                // Click "Tôi hiểu" / "I understand"
                const clicked = await page.evaluate(() => {
                    // Cách 1: input[name="confirm"]
                    const confirmBtn = document.querySelector('input[name="confirm"]');
                    if (confirmBtn) { confirmBtn.click(); return true; }

                    // Cách 2: Buttons chứa text
                    const buttons = document.querySelectorAll('button, input[type="submit"]');
                    for (const btn of buttons) {
                        const text = btn.value || btn.textContent || '';
                        if (text.includes('Tôi hiểu') || text.includes('I understand') ||
                            text.includes('Confirm') || text.includes('Continue')) {
                            btn.click();
                            return true;
                        }
                    }

                    // Cách 3: ID hoặc class
                    const el = document.querySelector('#confirm, .MK9CEd');
                    if (el) { el.click(); return true; }

                    return false;
                });

                if (clicked) {
                    this.log(`   ✅ Đã bấm "Tôi hiểu" - LOGIN THÀNH CÔNG!`, 'success');
                    await this.delay(2000);
                    result.status = 'PASSED';
                    result.reason = 'SPEEDBUMP_ACCEPTED';
                } else {
                    this.log(`   ⚠️ Không tìm thấy nút xác nhận`, 'warning');
                    result.status = 'PASSED';
                    result.reason = 'SPEEDBUMP_NO_BUTTON';
                }
            } else if (finalUrl.includes('myaccount.google.com') ||
                       finalUrl.includes('google.com/search') ||
                       finalUrl.includes('accounts.google.com/signin/oauth') ||
                       !finalUrl.includes('accounts.google.com')) {
                // Đã login thành công (không có speedbump)
                result.status = 'PASSED';
                result.reason = 'LOGIN_OK';
                this.log(`   ✅ Login thành công (không có speedbump)`, 'success');
            } else {
                // Vẫn ở trang google accounts - có thể cần thêm xử lý
                // Chờ thêm rồi check lại
                await this.delay(3000);
                const retryUrl = page.url();

                if (retryUrl.includes('speedbump')) {
                    this.log(`   ⚡ Speedbump xuất hiện sau delay!`, 'success');

                    const clicked = await page.evaluate(() => {
                        const confirmBtn = document.querySelector('input[name="confirm"], #confirm, .MK9CEd');
                        if (confirmBtn) { confirmBtn.click(); return true; }
                        const buttons = document.querySelectorAll('button, input[type="submit"]');
                        for (const btn of buttons) {
                            const text = btn.value || btn.textContent || '';
                            if (text.includes('Tôi hiểu') || text.includes('I understand')) {
                                btn.click(); return true;
                            }
                        }
                        return false;
                    });

                    if (clicked) {
                        this.log(`   ✅ Đã bấm "Tôi hiểu"!`, 'success');
                        result.status = 'PASSED';
                        result.reason = 'SPEEDBUMP_ACCEPTED';
                    } else {
                        result.status = 'PASSED';
                        result.reason = 'SPEEDBUMP_NO_BUTTON';
                    }
                } else if (!retryUrl.includes('accounts.google.com')) {
                    result.status = 'PASSED';
                    result.reason = 'LOGIN_OK';
                    this.log(`   ✅ Login thành công!`, 'success');
                } else {
                    result.reason = 'STUCK_AT_LOGIN';
                    this.log(`   ⚠️ Kẹt ở trang login`, 'warning');
                }
            }

        } catch (error) {
            result.reason = 'ERROR';
            this.log(`   ❌ Lỗi: ${error.message}`, 'error');
        }

        result.time = ((Date.now() - startTime) / 1000).toFixed(1);
        this.saveResult(result);
        this.log(`   ⏱️ ${result.status} - ${result.reason} (${result.time}s)`, result.status === 'PASSED' ? 'success' : 'warning');

        return result;
    }

    async start(accounts) {
        this.isRunning = true;
        this.browsers = [];
        this.completedCount = 0;
        this.resetResultsFile();

        const startTime = Date.now();
        const promises = [];

        this.log(`🚀 Mở ${accounts.length} browsers (delay 1.5s giữa mỗi cái)...`, 'info');

        for (let i = 0; i < accounts.length && this.isRunning; i++) {
            const acc = accounts[i];
            if (i > 0) await this.delay(1500);

            const promise = this.loginAccount(acc.email, acc.password, i, accounts.length)
                .then(result => {
                    this.completedCount++;
                    this.sendProgress(this.completedCount, accounts.length,
                        `Hoàn thành: ${this.completedCount}/${accounts.length}`);
                    return result;
                });
            promises.push(promise);
        }

        const results = await Promise.all(promises);

        let passed = 0, hasPhone = 0, needPhone = 0, failed = 0;
        results.forEach(r => {
            if (r && r.status === 'PASSED') passed++;
            else if (r && r.status === 'HAS_PHONE') hasPhone++;
            else if (r && r.status === 'NEED_PHONE') needPhone++;
            else failed++;
        });

        const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
        this.sendComplete({ total: accounts.length, passed, hasPhone, needPhone, failed, totalTime });
        this.isRunning = false;
        return { passed, hasPhone, needPhone, failed, totalTime };
    }

    async stop() {
        this.isRunning = false;
        this.log('⏸ Đã dừng! Browsers vẫn mở để kiểm tra.', 'warning');
    }

    async closeAllBrowsers() {
        const count = this.browsers.length;
        for (const browser of this.browsers) {
            try { await browser.close(); } catch (e) { }
        }
        this.browsers = [];
        this.log(`✖ Đã đóng ${count} browsers`, 'warning');
    }
}

module.exports = { LoginWorker, detectAllBrowsers };
