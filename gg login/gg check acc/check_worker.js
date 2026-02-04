/**
 * Check Worker - Simple Google account checker with 2FA support
 * Based on turbo_mass_checker.py logic
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const speakeasy = require('speakeasy');
const fs = require('fs');
const path = require('path');

puppeteer.use(StealthPlugin());

// Browser detection (keep existing detection logic)
function findPuppeteerChromiumPath() {
    if (process.resourcesPath) {
        const chromiumDir = path.join(process.resourcesPath, 'chromium');
        const directPath = path.join(chromiumDir, 'chrome.exe');
        if (fs.existsSync(directPath)) {
            return directPath;
        }

        if (fs.existsSync(chromiumDir)) {
            try {
                const items = fs.readdirSync(chromiumDir);
                for (const item of items) {
                    const itemPath = path.join(chromiumDir, item);
                    if (fs.statSync(itemPath).isDirectory()) {
                        const chromePath = path.join(itemPath, 'chrome.exe');
                        if (fs.existsSync(chromePath)) {
                            return chromePath;
                        }
                    }
                }
            } catch (e) {
                console.log('Error searching Chrome:', e.message);
            }
        }
    }
    return null;
}

function detectAllBrowsers() {
    const detected = [];
    const puppeteerPath = findPuppeteerChromiumPath();

    detected.push({
        id: 'puppeteer',
        name: 'Puppeteer Chromium (Mặc định)',
        detected: true,
        path: puppeteerPath
    });

    return detected;
}

function getBrowserPath(browserId) {
    const browsers = detectAllBrowsers();
    const browser = browsers.find(b => b.id === browserId && b.detected);
    return browser ? browser.path : null;
}

class CheckWorker {
    constructor(mainWindow, selectedBrowserId = null, options = {}) {
        this.mainWindow = mainWindow;
        this.isRunning = false;
        this.browsers = [];
        this.selectedBrowserId = selectedBrowserId;
        this.headless = options.headless || false;
        this.ramFlags = options.ramFlags || false;

        // Determine base path
        if (process.env.PORTABLE_EXECUTABLE_DIR) {
            this.basePath = process.env.PORTABLE_EXECUTABLE_DIR;
        } else if (process.resourcesPath && !process.resourcesPath.includes('node_modules')) {
            this.basePath = path.dirname(process.resourcesPath);
        } else {
            this.basePath = __dirname;
        }

        // File paths - NEW names
        this.RESULTS_FILE = path.join(this.basePath, 'check_results.json');
        this.LOGIN_OK_FILE = path.join(this.basePath, 'login_ok.txt');
        this.LOGIN_FAILED_FILE = path.join(this.basePath, 'login_failed.txt');
        this.NEED_2FA_FILE = path.join(this.basePath, 'need_2fa.txt');

        console.log('📁 Base path:', this.basePath);
    }

    log(message, type = 'info') {
        if (this.mainWindow) {
            this.mainWindow.webContents.send('log', { message, type });
        }
        console.log(message);
    }

    sendProgress(current, total, text) {
        if (this.mainWindow) {
            this.mainWindow.webContents.send('progress', { current, total, text });
        }
    }

    sendResult(result) {
        if (this.mainWindow) {
            this.mainWindow.webContents.send('result', result);
        }
    }

    sendComplete(data) {
        if (this.mainWindow) {
            this.mainWindow.webContents.send('complete', data);
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Generate OTP from 2FA secret
    generateOTP(secret) {
        try {
            const token = speakeasy.totp({
                secret: secret.replace(/\s/g, ''), // Remove spaces
                encoding: 'base32'
            });
            return token;
        } catch (error) {
            this.log(`   ❌ Lỗi tạo OTP: ${error.message}`, 'error');
            return null;
        }
    }

    // Reset result files
    resetResultsFile() {
        if (fs.existsSync(this.RESULTS_FILE)) fs.unlinkSync(this.RESULTS_FILE);
        if (fs.existsSync(this.LOGIN_OK_FILE)) fs.unlinkSync(this.LOGIN_OK_FILE);
        if (fs.existsSync(this.LOGIN_FAILED_FILE)) fs.unlinkSync(this.LOGIN_FAILED_FILE);
        if (fs.existsSync(this.NEED_2FA_FILE)) fs.unlinkSync(this.NEED_2FA_FILE);

        fs.writeFileSync(this.RESULTS_FILE, '[]');
        fs.writeFileSync(this.LOGIN_OK_FILE, '');
        fs.writeFileSync(this.LOGIN_FAILED_FILE, '');
        fs.writeFileSync(this.NEED_2FA_FILE, '');

        this.log('🗑️ Đã xóa kết quả cũ', 'info');
    }

    // Save result realtime
    saveResultRealtime(result) {
        let results = [];

        if (fs.existsSync(this.RESULTS_FILE)) {
            try {
                results = JSON.parse(fs.readFileSync(this.RESULTS_FILE, 'utf8'));
            } catch (e) {
                results = [];
            }
        }

        results.push(result);
        fs.writeFileSync(this.RESULTS_FILE, JSON.stringify(results, null, 2));

        const line = `${result.email}|${result.password}${result.twoFASecret ? '|' + result.twoFASecret : ''}\n`;

        if (result.status === 'LOGIN_OK') {
            fs.appendFileSync(this.LOGIN_OK_FILE, line);
        } else if (result.status === 'NEED_2FA') {
            fs.appendFileSync(this.NEED_2FA_FILE, line);
        } else {
            fs.appendFileSync(this.LOGIN_FAILED_FILE, line);
        }

        this.log(`💾 Đã lưu: ${result.email} → ${result.status}`, 'success');
        this.sendResult(result);
    }

    // Fast type (like turbo_input)
    async fastType(page, selector, text) {
        await page.waitForSelector(selector, { visible: true, timeout: 10000 });

        // JS injection for speed (turbo_input method)
        await page.evaluate((sel, txt) => {
            const el = document.querySelector(sel);
            if (el) {
                el.value = txt;
                el.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }, selector, text);

        await this.delay(200);
    }

    // Check for wrong password (lightning_check_wrong_password)
    async checkWrongPassword(page) {
        try {
            const pageSource = await page.content();
            const errorPatterns = [
                'wrong password',
                'incorrect password',
                'sai mật khẩu',
                'couldn\'t sign you in',
                'sign-in failed'
            ];

            return errorPatterns.some(pattern => pageSource.toLowerCase().includes(pattern));
        } catch {
            return false;
        }
    }

    // Check account deleted
    async checkAccountDeleted(page) {
        try {
            const url = page.url();
            const content = await page.content();

            return url.includes('deletedaccount') ||
                content.includes('Account deleted') ||
                content.includes('Tài khoản đã bị xóa') ||
                content.includes('recently deleted');
        } catch {
            return false;
        }
    }

    // Check 2FA challenge page
    async check2FAChallenge(page) {
        try {
            const url = page.url();
            return url.includes('/challenge/totp');
        } catch {
            return false;
        }
    }

    // Input OTP code
    async inputOTP(page, otpCode) {
        try {
            this.log(`   🔑 Nhập mã OTP: ${otpCode}`, 'info');

            // Wait for OTP input field
            await page.waitForSelector('input[type="tel"]', { visible: true, timeout: 5000 });

            // Input OTP
            await this.fastType(page, 'input[type="tel"]', otpCode);
            await this.delay(500);

            // Click Next/Verify button
            await page.evaluate(() => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    const text = btn.textContent || '';
                    if (text.includes('Next') || text.includes('Tiếp') || text.includes('Verify')) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            });

            await this.delay(3000);
            return true;
        } catch (error) {
            this.log(`   ❌ Lỗi nhập OTP: ${error.message}`, 'error');
            return false;
        }
    }

    // Login single account (simplified from turbo_test_single_account)
    async loginAccount(email, password, twoFASecret, index, total) {
        if (!this.isRunning) return null;

        const startTime = Date.now();
        this.log(`[${index + 1}/${total}] 🚀 ${email}`, 'info');
        this.sendProgress(index, total, `${index + 1}/${total}: ${email}`);

        // Get browser path
        let browserPath = null;
        if (this.selectedBrowserId === 'puppeteer' || !this.selectedBrowserId) {
            const puppeteerBrowser = detectAllBrowsers().find(b => b.id === 'puppeteer');
            if (puppeteerBrowser && puppeteerBrowser.path) {
                browserPath = puppeteerBrowser.path;
            }
            this.log(`   🌐 Dùng Puppeteer Chromium`, 'info');
        }

        // Launch options
        const launchArgs = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-blink-features=AutomationControlled'
        ];

        if (this.ramFlags) {
            launchArgs.push(
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--renderer-process-limit=1',
                '--single-process'
            );
        }

        const launchOptions = {
            headless: this.headless ? 'new' : false,
            args: launchArgs,
            defaultViewport: this.headless ? { width: 1280, height: 720 } : null
        };

        if (browserPath) {
            launchOptions.executablePath = browserPath;
        }

        const browser = await puppeteer.launch(launchOptions);
        this.browsers.push(browser);

        const page = await browser.newPage();

        await page.setUserAgent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        );

        await page.evaluateOnNewDocument(() => {
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        });

        let result = {
            email,
            password,
            twoFASecret: twoFASecret || null,
            status: 'UNKNOWN',
            time: 0,
            description: ''
        };

        try {
            // Step 1: Navigate to Google login
            this.log(`   📍 Mở trang đăng nhập Google...`, 'info');
            await page.goto('https://accounts.google.com/signin', {
                waitUntil: 'domcontentloaded',
                timeout: 30000
            });
            await this.delay(2000);

            // Step 2: Input email
            this.log(`   📧 Nhập email...`, 'info');
            await this.fastType(page, 'input[type="email"]', email);
            await this.delay(300);

            // Click Next
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

            await this.delay(3000);

            // Check if account deleted
            if (await this.checkAccountDeleted(page)) {
                result.status = 'LOGIN_FAILED';
                result.description = 'Account đã bị xóa';
                this.log(`   🗑️ Account đã bị xóa!`, 'error');
                return result;
            }

            // Step 3: Input password
            this.log(`   🔐 Chờ trang password...`, 'info');
            await page.waitForSelector('input[type="password"]', { visible: true, timeout: 8000 });

            this.log(`   🔑 Nhập password...`, 'info');
            await this.fastType(page, 'input[type="password"]', password);
            await this.delay(300);

            // Click Next
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

            await this.delay(4000);

            // Step 4: Check result

            // Check wrong password first
            if (await this.checkWrongPassword(page)) {
                result.status = 'LOGIN_FAILED';
                result.description = 'Sai mật khẩu';
                this.log(`   ❌ Sai mật khẩu!`, 'error');
                return result;
            }

            // Check 2FA challenge
            if (await this.check2FAChallenge(page)) {
                this.log(`   📱 Phát hiện trang 2FA!`, 'warning');

                if (twoFASecret) {
                    // Generate and input OTP
                    const otpCode = this.generateOTP(twoFASecret);
                    if (!otpCode) {
                        result.status = 'LOGIN_FAILED';
                        result.description = 'Lỗi tạo OTP';
                        return result;
                    }

                    const otpSuccess = await this.inputOTP(page, otpCode);
                    if (!otpSuccess) {
                        result.status = 'LOGIN_FAILED';
                        result.description = 'Lỗi nhập OTP';
                        return result;
                    }

                    // Check again after OTP
                    await this.delay(2000);

                    if (await this.checkWrongPassword(page)) {
                        result.status = 'LOGIN_FAILED';
                        result.description = 'OTP không đúng';
                        this.log(`   ❌ OTP không đúng!`, 'error');
                        return result;
                    }

                    // Login successful with 2FA
                    result.status = 'LOGIN_OK';
                    result.description = 'Đăng nhập thành công (2FA)';
                    this.log(`   ✅ Đăng nhập thành công với 2FA!`, 'success');
                } else {
                    // Need 2FA but no secret provided
                    result.status = 'NEED_2FA';
                    result.description = 'Cần mã 2FA';
                    this.log(`   ⚠️ Cần mã 2FA nhưng không có secret!`, 'warning');
                }
                return result;
            }

            // No errors detected → login successful
            result.status = 'LOGIN_OK';
            result.description = 'Đăng nhập thành công';
            this.log(`   ✅ Đăng nhập thành công!`, 'success');

        } catch (error) {
            result.status = 'LOGIN_FAILED';
            result.description = `Lỗi: ${error.message}`;
            this.log(`   ❌ Lỗi: ${error.message}`, 'error');
        } finally {
            result.time = Date.now() - startTime;

            // Don't close browser immediately, keep it open for manual intervention if needed
            // await browser.close();
        }

        return result;
    }

    // Start checking accounts
    async startCheck(accounts) {
        this.isRunning = true;
        this.resetResultsFile();

        this.log(`🚀 Bắt đầu với ${accounts.length} accounts...`, 'info');

        for (let i = 0; i < accounts.length && this.isRunning; i++) {
            const account = accounts[i];
            const result = await this.loginAccount(
                account.email,
                account.password,
                account.twoFASecret,
                i,
                accounts.length
            );

            if (result) {
                this.saveResultRealtime(result);
                this.log(`   ⏱️ Hoàn thành trong ${(result.time / 1000).toFixed(1)}s`, 'info');
            }

            if (!this.isRunning) break;
        }

        this.log(`✅ Hoàn thành kiểm tra!`, 'success');
        this.sendComplete({
            total: accounts.length,
            completed: accounts.length
        });

        this.isRunning = false;
    }

    // Stop checking
    async stop() {
        this.isRunning = false;
        this.log('⏸ Đang dừng...', 'warning');
    }

    // Close all browsers
    async closeAllBrowsers() {
        for (const browser of this.browsers) {
            try {
                await browser.close();
            } catch (e) {
                console.log('Error closing browser:', e.message);
            }
        }
        this.browsers = [];
        this.log('✖ Đã đóng tất cả browsers', 'info');
    }
}

module.exports = { CheckWorker, detectAllBrowsers, getBrowserPath };
