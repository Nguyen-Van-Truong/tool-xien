/**
 * Flow Worker - Puppeteer logic for Electron
 * Refactored from V2 flow_login.js
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

puppeteer.use(StealthPlugin());

// Danh sách tất cả browsers Chromium-based có thể hỗ trợ
const BROWSER_LIST = [
    {
        name: 'Google Chrome',
        id: 'chrome',
        paths: [
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
            process.env.LOCALAPPDATA + '\\Google\\Chrome\\Application\\chrome.exe',
        ]
    },
    {
        name: 'Microsoft Edge',
        id: 'edge',
        paths: [
            'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
            'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
        ]
    },
    {
        name: 'Brave',
        id: 'brave',
        paths: [
            'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
            'C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
            process.env.LOCALAPPDATA + '\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
        ]
    },
    {
        name: 'Vivaldi',
        id: 'vivaldi',
        paths: [
            'C:\\Program Files\\Vivaldi\\Application\\vivaldi.exe',
            process.env.LOCALAPPDATA + '\\Vivaldi\\Application\\vivaldi.exe',
        ]
    },
    {
        name: 'Opera',
        id: 'opera',
        paths: [
            'C:\\Program Files\\Opera\\launcher.exe',
            process.env.LOCALAPPDATA + '\\Programs\\Opera\\launcher.exe',
        ]
    },
    {
        name: 'Opera GX',
        id: 'operagx',
        paths: [
            process.env.LOCALAPPDATA + '\\Programs\\Opera GX\\launcher.exe',
        ]
    }
];

// Tìm đường dẫn Puppeteer Chromium (bundled)
function findPuppeteerChromiumPath() {
    // 1. Thử tìm trong resources/chromium khi chạy từ EXE (production)
    if (process.resourcesPath) {
        const chromiumDir = path.join(process.resourcesPath, 'chromium');

        // Thử trực tiếp trong chromium folder
        const directPath = path.join(chromiumDir, 'chrome.exe');
        if (fs.existsSync(directPath)) {
            console.log('Found Chrome at:', directPath);
            return directPath;
        }

        // Thử tìm trong các subfolder
        if (fs.existsSync(chromiumDir)) {
            try {
                const items = fs.readdirSync(chromiumDir);
                for (const item of items) {
                    const itemPath = path.join(chromiumDir, item);
                    if (fs.statSync(itemPath).isDirectory()) {
                        const chromePath = path.join(itemPath, 'chrome.exe');
                        if (fs.existsSync(chromePath)) {
                            console.log('Found Chrome at:', chromePath);
                            return chromePath;
                        }
                    }
                }
            } catch (e) {
                console.log('Error searching for Chrome:', e.message);
            }
        }
    }

    // 2. Dev mode: dùng puppeteer default (null = auto detect)
    return null;
}

// Detect tất cả browsers có sẵn trên máy
function detectAllBrowsers() {
    const detected = [];

    // Tìm Puppeteer Chromium path
    const puppeteerPath = findPuppeteerChromiumPath();

    // Thêm Puppeteer bundled Chromium làm mặc định (luôn có sẵn)
    detected.push({
        id: 'puppeteer',
        name: 'Puppeteer Chromium (Mặc định)',
        detected: true,
        path: puppeteerPath // null = dùng Puppeteer default, hoặc path cụ thể khi production
    });

    // Detect các browsers cài sẵn
    for (const browser of BROWSER_LIST) {
        let foundPath = null;

        for (const browserPath of browser.paths) {
            if (fs.existsSync(browserPath)) {
                foundPath = browserPath;
                break;
            }
        }

        detected.push({
            id: browser.id,
            name: browser.name,
            detected: !!foundPath,
            path: foundPath
        });
    }

    return detected;
}

// Tìm path của browser theo ID
function getBrowserPath(browserId) {
    const browsers = detectAllBrowsers();
    const browser = browsers.find(b => b.id === browserId && b.detected);
    return browser ? browser.path : null;
}

// Tìm browser đầu tiên khả dụng
function findFirstAvailableBrowser() {
    const browsers = detectAllBrowsers();
    const available = browsers.find(b => b.detected);
    return available ? available.path : null;
}

class FlowWorker {
    constructor(mainWindow, selectedBrowserId = null, options = {}) {
        this.mainWindow = mainWindow;
        this.isRunning = false;
        this.browsers = [];
        this.selectedBrowserId = selectedBrowserId;
        this.headless = options.headless || false;
        this.ramFlags = options.ramFlags || false;

        // Xác định basePath - dùng folder chứa EXE khi chạy production
        if (process.env.PORTABLE_EXECUTABLE_DIR) {
            // Chạy từ portable EXE
            this.basePath = process.env.PORTABLE_EXECUTABLE_DIR;
        } else if (process.resourcesPath && !process.resourcesPath.includes('node_modules')) {
            // Chạy từ built app (unpacked)
            this.basePath = path.dirname(process.resourcesPath);
        } else {
            // Chạy từ source (dev mode)
            this.basePath = __dirname;
        }

        // File paths
        this.RESULTS_FILE = path.join(this.basePath, 'flow_results.json');
        this.HAS_FLOW_FILE = path.join(this.basePath, 'has_flow.txt');
        this.NO_FLOW_FILE = path.join(this.basePath, 'no_flow.txt');
        this.LOGIN_FAILED_FILE = path.join(this.basePath, 'login_failed.txt');

        console.log('📁 Base path:', this.basePath);
        console.log('🌐 Selected browser:', this.selectedBrowserId || 'auto');
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
            await this.delay(4000); // Tăng từ 2000 để đợi load đủ
            this.log('   🔍 Kiểm tra Flow availability...', 'info');

            const response = await page.evaluate(async () => {
                try {
                    const res = await fetch('https://labs.google/fx/api/trpc/general.fetchToolAvailability?input=%7B%22json%22%3A%7B%22tool%22%3A%22PINHOLE%22%7D%7D');
                    return await res.json();
                } catch (e) {
                    return { error: e.message };
                }
            });

            // Check UNAUTHORIZED - chưa login
            if (response?.error?.json?.code === -32001 ||
                response?.error?.json?.message === 'UNAUTHORIZED' ||
                response?.error?.json?.data?.httpStatus === 401) {
                return { available: false, state: 'UNAUTHORIZED', raw: 'Chưa đăng nhập' };
            }

            if (response.error && !response.result) {
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
        await this.delay(2000); // Thêm delay 2s để đợi page load
        const url = page.url();
        const content = await page.content();

        if (url.includes('accounts.google.com')) {
            // Kiểm tra trang speedbump (cần bấm "Tôi hiểu" / "I understand")
            if (url.includes('speedbump')) {
                return 'SPEEDBUMP_PAGE';
            }
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

    // Xử lý trang speedbump - bấm nút "Tôi hiểu" / "I understand"
    async handleSpeedbumpPage(page) {
        this.log(`   ⚠️ Phát hiện trang speedbump, đang xử lý...`, 'warning');

        try {
            // Chờ 1s để trang load
            await this.delay(1000);

            // Thử click nút confirm bằng nhiều cách
            const clicked = await page.evaluate(() => {
                // Cách 1: Tìm input[name="confirm"]
                const confirmBtn = document.querySelector('input[name="confirm"]');
                if (confirmBtn) {
                    confirmBtn.click();
                    return true;
                }

                // Cách 2: Tìm button có text "Tôi hiểu" hoặc "I understand"
                const buttons = document.querySelectorAll('button, input[type="submit"]');
                for (const btn of buttons) {
                    const text = btn.value || btn.textContent || '';
                    if (text.includes('Tôi hiểu') || text.includes('I understand') ||
                        text.includes('Confirm') || text.includes('Continue')) {
                        btn.click();
                        return true;
                    }
                }

                // Cách 3: Tìm theo class
                const confirmByClass = document.querySelector('.MK9CEd, .MVpUfe, #confirm');
                if (confirmByClass) {
                    confirmByClass.click();
                    return true;
                }

                return false;
            });

            if (clicked) {
                this.log(`   ✅ Đã bấm nút xác nhận speedbump`, 'success');
                await this.delay(2000); // Chờ chuyển trang
                return true;
            } else {
                this.log(`   ❌ Không tìm thấy nút xác nhận speedbump`, 'error');
                return false;
            }
        } catch (error) {
            this.log(`   ❌ Lỗi xử lý speedbump: ${error.message}`, 'error');
            return false;
        }
    }

    // Kiểm tra Flow API với retry
    async checkFlowWithRetry(page, maxRetries = 6) {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            this.log(`   🔍 Kiểm tra Flow (lần ${attempt}/${maxRetries})...`, 'info');

            await this.delay(5000); // Tăng từ 3000 - Chờ 5s trước mỗi lần check

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

        // Tìm browser để dùng
        let browserPath = null;
        let usePuppeteerChromium = false;

        if (this.selectedBrowserId === 'puppeteer' || !this.selectedBrowserId) {
            // Dùng Puppeteer bundled Chromium (như V2 - ít CAPTCHA hơn)
            usePuppeteerChromium = true;

            // Lấy path của Puppeteer Chromium (nếu có - production mode)
            const puppeteerBrowser = detectAllBrowsers().find(b => b.id === 'puppeteer');
            if (puppeteerBrowser && puppeteerBrowser.path) {
                browserPath = puppeteerBrowser.path;
                this.log(`   🌐 Dùng Puppeteer Chromium (từ bundle)`, 'info');
            } else {
                this.log(`   🌐 Dùng Puppeteer Chromium (mặc định)`, 'info');
            }
        } else {
            browserPath = getBrowserPath(this.selectedBrowserId);
            if (!browserPath) {
                this.log(`   ❌ Không tìm thấy trình duyệt trên máy!`, 'error');
                return {
                    email,
                    password,
                    status: 'LOGIN_FAILED',
                    flowState: 'NO_BROWSER',
                    time: 0
                };
            }
            this.log(`   🌐 Dùng browser: ${this.selectedBrowserId}`, 'info');
        }

        // Config cho Puppeteer Chromium (như V2 - ít CAPTCHA)
        // Tìm Dark Reader extension path
        let extensionPath = path.join(__dirname, 'extensions', 'eimadpbcbfnmbkopoojfekhnkhdbieeh', '4.9.118_0');
        // Nếu chạy từ EXE, tìm trong resources
        if (process.resourcesPath) {
            const prodExtPath = path.join(process.resourcesPath, 'app', 'extensions', 'eimadpbcbfnmbkopoojfekhnkhdbieeh', '4.9.118_0');
            if (fs.existsSync(prodExtPath)) {
                extensionPath = prodExtPath;
            }
        }

        const launchArgs = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars'
        ];

        // RAM saving flags
        if (this.ramFlags) {
            this.log('⚡ Áp dụng RAM flags tiết kiệm bộ nhớ', 'info');
            launchArgs.push(
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-software-rasterizer',
                '--renderer-process-limit=1',
                '--single-process'
            );
        } else {
            launchArgs.push('--start-maximized');
        }

        // Load Dark Reader extension (only when not headless)
        if (!this.headless) {
            launchArgs.push(
                `--disable-extensions-except=${extensionPath}`,
                `--load-extension=${extensionPath}`
            );
        }

        // Log headless mode
        if (this.headless) {
            this.log('👻 Chạy ở chế độ Headless (ẩn browser)', 'info');
        }

        const launchOptions = {
            headless: this.headless ? 'new' : false,
            slowMo: 0,
            args: launchArgs,
            defaultViewport: this.headless ? { width: 1280, height: 720 } : null
        };

        // Nếu có browserPath (production hoặc browser cài sẵn)
        if (browserPath) {
            launchOptions.executablePath = browserPath;
        }

        // Nếu dùng browser cài sẵn (không phải Puppeteer), thêm các config anti-detection
        if (!usePuppeteerChromium && browserPath) {
            const userDataDir = path.join(this.basePath, 'browser_profiles', `profile_${index}_${Date.now()}`);
            launchOptions.userDataDir = userDataDir;
            launchOptions.ignoreDefaultArgs = ['--enable-automation'];
            launchOptions.args.push(
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-extensions',
                '--disable-sync',
                '--no-first-run'
            );
        }

        const browser = await puppeteer.launch(launchOptions);

        this.browsers.push(browser);

        // Đợi 2s để extension load và trang intro hiện
        await this.delay(2000);

        // Đóng tất cả các tab intro của extension (nếu có)
        const pages = await browser.pages();
        for (const p of pages) {
            const url = p.url();
            // Đóng các tab intro của extension
            if (url.includes('darkreader') || url.includes('extension') || url.includes('chrome-extension')) {
                try {
                    await p.close();
                } catch (e) {
                    // Ignore
                }
            }
        }

        // Tạo page mới sau khi đóng tab intro
        const page = await browser.newPage();

        // Thiết lập User Agent
        await page.setUserAgent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        );

        // Anti-detection scripts
        // Anti-detection scripts
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
                const maxRetries = 6;

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

                        await this.delay(4500); // Tăng từ 2500 để đợi load đủ

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

                                await this.delay(6000); // Tăng từ 4000 để đợi load đủ

                                const finalContent = await page.content();
                                const currentUrl = page.url();

                                if (finalContent.includes('Wrong password') || finalContent.includes('Sai mật khẩu')) {
                                    result.status = 'LOGIN_FAILED';
                                    result.flowState = 'WRONG_PASSWORD';
                                    this.log(`   ❌ Sai mật khẩu!`, 'error');
                                    loginSuccess = true; // Dừng retry
                                } else if (currentUrl.includes('challenge') ||
                                    finalContent.includes('Enter a phone number') ||
                                    finalContent.includes('Nhập số điện thoại') ||
                                    finalContent.includes('Verify it') ||
                                    finalContent.includes('verification code') ||
                                    finalContent.includes('mã xác minh')) {
                                    // Gặp trang xác minh số điện thoại - DỪNG NGAY
                                    result.status = 'LOGIN_FAILED';
                                    result.flowState = 'NEED_PHONE_VERIFY';
                                    this.log(`   📱 Cần xác minh số điện thoại - DỪNG`, 'warning');
                                    loginSuccess = true; // Dừng retry, để user tự xác minh
                                } else {
                                    // Dùng API check thay vì check text
                                    this.log(`   🔍 Kiểm tra trạng thái login qua API...`, 'info');
                                    const apiCheck = await this.checkFlowAvailability(page);

                                    if (apiCheck.state === 'UNAUTHORIZED') {
                                        // Chưa login thành công - check thêm lý do
                                        if (page.url().includes('accounts.google.com')) {
                                            result.status = 'LOGIN_FAILED';
                                            result.flowState = 'NEED_VERIFY';
                                            this.log(`   ⚠️ Cần xác minh hoặc có vấn đề khác!`, 'warning');
                                        } else {
                                            result.status = 'LOGIN_FAILED';
                                            result.flowState = 'UNAUTHORIZED';
                                            this.log(`   ❌ Không thể xác thực!`, 'error');
                                        }
                                    } else if (apiCheck.state === 'AVAILABLE') {
                                        result.status = 'HAS_FLOW';
                                        result.flowState = 'AVAILABLE';
                                        this.log(`   🎬 CÓ FLOW!`, 'success');
                                    } else if (apiCheck.state === 'UNAVAILABLE_LOW_REPUTATION') {
                                        result.status = 'NO_FLOW';
                                        result.flowState = 'UNAVAILABLE_LOW_REPUTATION';
                                        this.log(`   ⚠️ KHÔNG CÓ FLOW (Low reputation)`, 'warning');
                                    } else {
                                        // ===== CHECKPOINT: Có kết quả khác, tiếp tục flow cũ =====
                                        this.log(`   ✅ Đã qua bước password! (${apiCheck.state})`, 'success');

                                        // Chờ cho page ổn định
                                        await this.delay(4000); // Tăng từ 2000

                                        // Kiểm tra vị trí hiện tại
                                        let currentPage = await this.detectCurrentPage(page);
                                        this.log(`   📍 Trang hiện tại: ${currentPage}`, 'info');

                                        // Xử lý speedbump nếu cần
                                        if (currentPage === 'SPEEDBUMP_PAGE') {
                                            await this.handleSpeedbumpPage(page);
                                            await this.delay(2000);
                                            currentPage = await this.detectCurrentPage(page);
                                            this.log(`   📍 Sau speedbump: ${currentPage}`, 'info');
                                        }

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

    // Stop (chỉ dừng process, KHÔNG đóng browsers để kiểm tra thủ công)
    async stop() {
        this.isRunning = false;
        this.log('⏸ Đã dừng! Browsers vẫn mở để kiểm tra.', 'warning');
    }

    // Chỉ đóng tất cả browsers (không ảnh hưởng isRunning)
    async closeAllBrowsers() {
        const count = this.browsers.length;

        for (const browser of this.browsers) {
            try {
                await browser.close();
            } catch (e) {
                // Ignore
            }
        }

        this.browsers = [];
        this.log(`✖ Đã đóng ${count} browsers`, 'warning');
    }
}

module.exports = { FlowWorker, detectAllBrowsers };
