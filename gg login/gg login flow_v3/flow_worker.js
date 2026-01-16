/**
 * Flow Worker - Puppeteer logic for Electron
 * Refactored from V2 flow_login.js
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');

puppeteer.use(StealthPlugin());

class FlowWorker {
    constructor(mainWindow) {
        this.mainWindow = mainWindow;
        this.isRunning = false;
        this.browsers = [];
        this.basePath = __dirname;

        // File paths
        this.RESULTS_FILE = path.join(this.basePath, 'flow_results.json');
        this.HAS_FLOW_FILE = path.join(this.basePath, 'has_flow.txt');
        this.NO_FLOW_FILE = path.join(this.basePath, 'no_flow.txt');
        this.LOGIN_FAILED_FILE = path.join(this.basePath, 'login_failed.txt');
    }

    // Send log to renderer
    log(message, type = 'info') {
        if (this.mainWindow) {
            this.mainWindow.webContents.send('log', { message, type });
        }
        console.log(message);
    }

    // Send progress update
    sendProgress(current, total, text) {
        if (this.mainWindow) {
            this.mainWindow.webContents.send('progress', { current, total, text });
        }
    }

    // Send result update
    sendResult(result) {
        if (this.mainWindow) {
            this.mainWindow.webContents.send('result', result);
        }
    }

    // Send complete
    sendComplete(data) {
        if (this.mainWindow) {
            this.mainWindow.webContents.send('complete', data);
        }
    }

    // Delay
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Reset result files
    resetResultsFile() {
        if (fs.existsSync(this.RESULTS_FILE)) fs.unlinkSync(this.RESULTS_FILE);
        if (fs.existsSync(this.HAS_FLOW_FILE)) fs.unlinkSync(this.HAS_FLOW_FILE);
        if (fs.existsSync(this.NO_FLOW_FILE)) fs.unlinkSync(this.NO_FLOW_FILE);
        if (fs.existsSync(this.LOGIN_FAILED_FILE)) fs.unlinkSync(this.LOGIN_FAILED_FILE);

        fs.writeFileSync(this.RESULTS_FILE, '[]');
        fs.writeFileSync(this.HAS_FLOW_FILE, '');
        fs.writeFileSync(this.NO_FLOW_FILE, '');
        fs.writeFileSync(this.LOGIN_FAILED_FILE, '');

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

        const line = `${result.email}|${result.password}\n`;

        if (result.status === 'HAS_FLOW') {
            fs.appendFileSync(this.HAS_FLOW_FILE, line);
        } else if (result.status === 'NO_FLOW') {
            fs.appendFileSync(this.NO_FLOW_FILE, line);
        } else {
            fs.appendFileSync(this.LOGIN_FAILED_FILE, line);
        }

        this.log(`💾 Đã lưu: ${result.email} → ${result.status}`, 'success');
        this.sendResult(result);
    }

    // Fast type
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

    // Check Flow availability via API
    async checkFlowAvailability(page) {
        try {
            await this.delay(2000);
            this.log('   🔍 Kiểm tra Flow availability...', 'info');

            const response = await page.evaluate(async () => {
                try {
                    const res = await fetch('https://labs.google/fx/api/trpc/general.fetchToolAvailability?input=%7B%22json%22%3A%7B%22tool%22%3A%22PINHOLE%22%7D%7D');
                    return await res.json();
                } catch (e) {
                    return { error: e.message };
                }
            });

            if (response.error) {
                return { available: false, state: 'API_ERROR', raw: response.error };
            }

            const availabilityState = response?.result?.data?.json?.result?.availabilityState;

            if (availabilityState === 'AVAILABLE') {
                return { available: true, state: 'AVAILABLE', raw: availabilityState };
            } else {
                return { available: false, state: availabilityState || 'UNKNOWN', raw: availabilityState };
            }

        } catch (error) {
            return { available: false, state: 'CHECK_ERROR', raw: error.message };
        }
    }

    // ========== VALIDATION HELPERS ==========

    // Kiểm tra đang ở trang nào
    async detectCurrentPage(page) {
        const url = page.url();
        const content = await page.content();

        if (url.includes('accounts.google.com')) {
            if (content.includes('input type="email"') || content.includes('identifierId')) {
                return 'EMAIL_PAGE';
            }
            if (content.includes('input type="password"') || content.includes('Nhập mật khẩu')) {
                return 'PASSWORD_PAGE';
            }
            if (content.includes('Couldn\'t find') || content.includes('Không tìm thấy')) {
                return 'EMAIL_NOT_FOUND';
            }
            if (content.includes('Wrong password') || content.includes('Sai mật khẩu')) {
                return 'WRONG_PASSWORD';
            }
            if (content.includes('verify') || content.includes('Verify') || content.includes('xác minh')) {
                return 'VERIFY_REQUIRED';
            }
            return 'GOOGLE_LOGIN_OTHER';
        }

        if (url.includes('labs.google') && url.includes('flow')) {
            return 'FLOW_PAGE';
        }

        return 'UNKNOWN';
    }

    // Kiểm tra Flow API với retry
    async checkFlowWithRetry(page, maxRetries = 3) {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            this.log(`   🔍 Kiểm tra Flow (lần ${attempt}/${maxRetries})...`, 'info');

            await this.delay(1500); // Chờ 1.5s trước mỗi lần check

            const result = await this.checkFlowAvailability(page);

            // Nếu có kết quả rõ ràng, return
            if (result.state === 'AVAILABLE' || result.state === 'UNAVAILABLE_LOW_REPUTATION') {
                return result;
            }

            // Nếu lỗi API, thử lại
            if (result.state === 'API_ERROR' || result.state === 'CHECK_ERROR') {
                if (attempt < maxRetries) {
                    this.log(`   ⚠️ API lỗi, thử lại...`, 'warning');
                    await this.delay(2000);
                    continue;
                }
            }

            return result;
        }

        return { available: false, state: 'RETRY_EXHAUSTED' };
    }

    // Chờ URL thay đổi
    async waitForUrlChange(page, currentUrl, timeout = 10000) {
        const startTime = Date.now();
        while (Date.now() - startTime < timeout) {
            const newUrl = page.url();
            if (newUrl !== currentUrl) {
                return newUrl;
            }
            await this.delay(500);
        }
        return page.url();
    }

    // Login single account
    async loginAccount(email, password, index, total) {
        if (!this.isRunning) return null;

        const startTime = Date.now();
        this.log(`[${index + 1}/${total}] 🚀 ${email}`, 'info');
        this.sendProgress(index, total, `${index + 1}/${total}: ${email}`);

        const browser = await puppeteer.launch({
            headless: false,
            slowMo: 0,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--start-maximized'
            ],
            defaultViewport: null
        });

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
            status: 'UNKNOWN',
            flowState: 'N/A',
            time: 0
        };

        try {
            // Step 1: Go to Flow
            this.log(`   📍 Vào Flow...`, 'info');
            await page.goto('https://labs.google/fx/tools/flow', {
                waitUntil: 'domcontentloaded',
                timeout: 30000
            });

            await this.delay(2000);

            // Step 2: Click "Create with Flow"
            this.log(`   🖱️ Click Create with Flow...`, 'info');
            await page.evaluate(() => {
                const buttons = document.querySelectorAll('button, a, [role="button"]');
                for (const btn of buttons) {
                    if (btn.textContent.includes('Create with Flow') ||
                        btn.textContent.includes('Start creating')) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            });

            await this.delay(3000);

            const currentUrl = page.url();

            // Step 3: Login if needed
            if (currentUrl.includes('accounts.google.com')) {
                let loginSuccess = false;
                let retryCount = 0;
                const maxRetries = 3;

                while (!loginSuccess && retryCount < maxRetries && this.isRunning) {
                    retryCount++;

                    if (retryCount > 1) {
                        this.log(`   🔄 Thử lại lần ${retryCount}/${maxRetries}...`, 'warning');
                        await page.goto('https://labs.google/fx/tools/flow', {
                            waitUntil: 'domcontentloaded',
                            timeout: 30000
                        });
                        await this.delay(2000);

                        await page.evaluate(() => {
                            const buttons = document.querySelectorAll('button, a, [role="button"]');
                            for (const btn of buttons) {
                                if (btn.textContent.includes('Create with Flow') || btn.textContent.includes('Start creating')) {
                                    btn.click();
                                    return true;
                                }
                            }
                            return false;
                        });
                        await this.delay(3000);
                    }

                    try {
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

                        await this.delay(2500);

                        const pageContent = await page.content();
                        if (pageContent.includes('Couldn\'t find') || pageContent.includes('Không tìm thấy')) {
                            result.status = 'LOGIN_FAILED';
                            result.flowState = 'EMAIL_NOT_FOUND';
                            this.log(`   ❌ Email không tồn tại!`, 'error');
                            loginSuccess = true;
                        } else {
                            try {
                                this.log(`   🔐 Chờ trang password...`, 'info');
                                await page.waitForSelector('input[type="password"]', { visible: true, timeout: 8000 });

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

                                await this.delay(4000);

                                const finalContent = await page.content();

                                if (finalContent.includes('Wrong password') || finalContent.includes('Sai mật khẩu')) {
                                    result.status = 'LOGIN_FAILED';
                                    result.flowState = 'WRONG_PASSWORD';
                                    this.log(`   ❌ Sai mật khẩu!`, 'error');
                                } else if (finalContent.includes('verify') || finalContent.includes('Verify')) {
                                    result.status = 'LOGIN_FAILED';
                                    result.flowState = 'NEED_VERIFY';
                                    this.log(`   ⚠️ Cần xác minh!`, 'warning');
                                } else {
                                    // ===== CHECKPOINT: Sau khi nhập password thành công =====
                                    this.log(`   ✅ Đã qua bước password!`, 'success');

                                    // Chờ cho page ổn định
                                    await this.delay(2000);

                                    // Kiểm tra vị trí hiện tại
                                    const currentPage = await this.detectCurrentPage(page);
                                    this.log(`   📍 Trang hiện tại: ${currentPage}`, 'info');

                                    if (currentPage === 'FLOW_PAGE') {
                                        // Đã ở trang Flow, check API với retry
                                        const flowCheck = await this.checkFlowWithRetry(page, 3);
                                        result.flowState = flowCheck.state;

                                        if (flowCheck.available) {
                                            result.status = 'HAS_FLOW';
                                            this.log(`   🎬 CÓ FLOW! (${flowCheck.state})`, 'success');
                                        } else {
                                            result.status = 'NO_FLOW';
                                            this.log(`   ⚠️ KHÔNG CÓ FLOW (${flowCheck.state})`, 'warning');
                                        }
                                    } else {
                                        // Navigate về Flow page
                                        this.log(`   🔄 Chuyển về Flow page...`, 'info');

                                        try {
                                            await page.goto('https://labs.google/fx/tools/flow', {
                                                waitUntil: 'domcontentloaded',
                                                timeout: 15000
                                            });
                                            await this.delay(2000);

                                            // Double check trang hiện tại
                                            const newPage = await this.detectCurrentPage(page);

                                            if (newPage === 'FLOW_PAGE') {
                                                // Check API với retry
                                                const flowCheck = await this.checkFlowWithRetry(page, 3);
                                                result.flowState = flowCheck.state;

                                                if (flowCheck.available) {
                                                    result.status = 'HAS_FLOW';
                                                    this.log(`   🎬 CÓ FLOW! (${flowCheck.state})`, 'success');
                                                } else {
                                                    result.status = 'NO_FLOW';
                                                    this.log(`   ⚠️ KHÔNG CÓ FLOW (${flowCheck.state})`, 'warning');
                                                }
                                            } else if (newPage.includes('GOOGLE')) {
                                                // Vẫn ở trang Google login
                                                result.status = 'CHECK_MANUALLY';
                                                result.flowState = 'STUCK_AT_LOGIN';
                                                this.log(`   ⚠️ Còn kẹt ở trang login`, 'warning');
                                            } else {
                                                result.status = 'CHECK_MANUALLY';
                                                result.flowState = newPage;
                                                this.log(`   ⚠️ Trang không xác định: ${newPage}`, 'warning');
                                            }
                                        } catch (navError) {
                                            result.status = 'CHECK_MANUALLY';
                                            result.flowState = 'NAV_ERROR';
                                            this.log(`   ⚠️ Không navigate được`, 'warning');
                                        }
                                    }
                                }

                                loginSuccess = true;

                            } catch (passError) {
                                this.log(`   ⚠️ Không thấy trang password (CAPTCHA?)`, 'warning');
                                if (retryCount >= maxRetries) {
                                    result.status = 'LOGIN_FAILED';
                                    result.flowState = 'CAPTCHA_OR_ERROR';
                                }
                            }
                        }
                    } catch (err) {
                        this.log(`   ⚠️ Lỗi: ${err.message}`, 'error');
                        if (retryCount >= maxRetries) {
                            result.status = 'LOGIN_FAILED';
                            result.flowState = 'ERROR';
                        }
                    }
                }
            } else {
                result.status = 'LOGIN_FAILED';
                result.flowState = 'NO_LOGIN_PAGE';
                this.log(`   ⚠️ Không chuyển đến login page`, 'warning');
            }

        } catch (error) {
            result.status = 'LOGIN_FAILED';
            result.flowState = `ERROR`;
            this.log(`   ❌ Lỗi: ${error.message}`, 'error');
        }

        result.time = ((Date.now() - startTime) / 1000).toFixed(1);
        this.saveResultRealtime(result);
        this.log(`   ⏱️ Hoàn thành trong ${result.time}s`, 'info');

        return result;
    }

    // Start login process - PARALLEL với delay 1s giữa mỗi account
    async start(accounts) {
        this.isRunning = true;
        this.browsers = [];
        this.completedCount = 0;

        this.resetResultsFile();

        const startTime = Date.now();
        const promises = [];

        this.log(`🚀 Mở ${accounts.length} browsers song song (delay 1s mỗi cái)...`, 'info');

        // Mở tất cả browsers với delay 1s giữa mỗi cái
        for (let i = 0; i < accounts.length && this.isRunning; i++) {
            const acc = accounts[i];

            // Delay 1s trước khi mở browser tiếp (trừ cái đầu tiên)
            if (i > 0) {
                await this.delay(1000);
            }

            // Bắt đầu login (KHÔNG await - chạy song song)
            const promise = this.loginAccount(acc.email, acc.password, i, accounts.length)
                .then(result => {
                    this.completedCount++;
                    this.sendProgress(this.completedCount, accounts.length,
                        `Hoàn thành: ${this.completedCount}/${accounts.length}`);
                    return result;
                });
            promises.push(promise);
        }

        // Chờ TẤT CẢ hoàn thành
        const results = await Promise.all(promises);

        let hasFlow = 0, noFlow = 0, failed = 0;
        results.forEach(result => {
            if (result) {
                if (result.status === 'HAS_FLOW') hasFlow++;
                else if (result.status === 'NO_FLOW') noFlow++;
                else failed++;
            }
        });

        const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);

        this.sendComplete({
            total: accounts.length,
            hasFlow,
            noFlow,
            failed,
            totalTime
        });

        this.isRunning = false;
        return { hasFlow, noFlow, failed, totalTime };
    }

    // Stop all
    async stop() {
        this.isRunning = false;

        for (const browser of this.browsers) {
            try {
                await browser.close();
            } catch (e) {
                // Ignore
            }
        }

        this.browsers = [];
        this.log('Đã dừng tất cả', 'warning');
    }
}

module.exports = FlowWorker;
