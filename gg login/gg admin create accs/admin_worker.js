/**
 * Admin Worker - Puppeteer logic for Google Admin Console
 * Tự động tạo accounts hàng loạt qua admin.google.com
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');
const EmailAPI = require('./email_api');

puppeteer.use(StealthPlugin());

// Danh sách names để random
const FIRST_NAMES = [
    'James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Charles',
    'Christopher', 'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven', 'Paul', 'Andrew', 'Joshua',
    'Emma', 'Olivia', 'Ava', 'Isabella', 'Sophia', 'Mia', 'Charlotte', 'Amelia', 'Harper', 'Evelyn'
];

const LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
    'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'
];

// Tìm đường dẫn Puppeteer Chromium (bundled)
function findPuppeteerChromiumPath() {
    // Khi chạy từ EXE, tìm trong resources/chromium
    if (process.resourcesPath) {
        const possiblePaths = [
            path.join(process.resourcesPath, 'chromium', 'chrome.exe'),
            path.join(process.resourcesPath, 'chromium', 'chrome-win64', 'chrome.exe'),
        ];

        for (const chromePath of possiblePaths) {
            if (fs.existsSync(chromePath)) {
                return chromePath;
            }
        }
    }

    // Dev mode - Puppeteer tự tìm
    return null;
}

class AdminWorker {
    constructor(mainWindow) {
        this.mainWindow = mainWindow;
        this.isRunning = false;
        this.browser = null;
        this.page = null;
        this.manualLoginResolve = null; // Promise resolve cho manual login

        // Xác định basePath
        if (process.env.PORTABLE_EXECUTABLE_DIR) {
            this.basePath = process.env.PORTABLE_EXECUTABLE_DIR;
        } else if (process.resourcesPath && !process.resourcesPath.includes('node_modules')) {
            this.basePath = path.dirname(process.resourcesPath);
        } else {
            this.basePath = __dirname;
        }

        // Result files
        this.CREATED_FILE = path.join(this.basePath, 'created_accounts.txt');
        this.FAILED_FILE = path.join(this.basePath, 'failed_accounts.txt');
        this.RESULTS_FILE = path.join(this.basePath, 'admin_results.json');
    }

    // Resolve manual login Promise (called from main.js IPC handler)
    resolveManualLogin() {
        if (this.manualLoginResolve) {
            this.manualLoginResolve();
            this.manualLoginResolve = null;
        }
    }

    // Log to renderer
    log(message, type = 'info') {
        console.log(message);
        if (this.mainWindow) {
            this.mainWindow.webContents.send('log', { message, type });
        }
    }

    // Send progress
    sendProgress(current, total, text) {
        if (this.mainWindow) {
            this.mainWindow.webContents.send('progress', { current, total, text });
        }
    }

    // Send result
    sendResult(result) {
        if (this.mainWindow) {
            this.mainWindow.webContents.send('result', result);
        }
    }

    // Delay helper
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Random string generator
    randomString(length) {
        const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    }

    // Random password generator
    randomPassword(length = 12) {
        const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    }

    // Generate random account info
    generateRandomAccount() {
        const firstName = FIRST_NAMES[Math.floor(Math.random() * FIRST_NAMES.length)];
        const lastName = LAST_NAMES[Math.floor(Math.random() * LAST_NAMES.length)];
        const emailPrefix = `${firstName.toLowerCase()}${this.randomString(4)}`;

        return { firstName, lastName, emailPrefix };
    }

    // Reset result files
    resetResultsFile() {
        if (fs.existsSync(this.CREATED_FILE)) fs.unlinkSync(this.CREATED_FILE);
        if (fs.existsSync(this.FAILED_FILE)) fs.unlinkSync(this.FAILED_FILE);
        if (fs.existsSync(this.RESULTS_FILE)) fs.unlinkSync(this.RESULTS_FILE);

        fs.writeFileSync(this.CREATED_FILE, '');
        fs.writeFileSync(this.FAILED_FILE, '');
        fs.writeFileSync(this.RESULTS_FILE, '[]');

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

        if (result.status === 'CREATED') {
            fs.appendFileSync(this.CREATED_FILE, line);
        } else {
            fs.appendFileSync(this.FAILED_FILE, `${result.email}|${result.error}\n`);
        }
    }

    // Fast type - set value directly via evaluate (nhanh hơn page.type)
    async fastType(page, selector, text) {
        try {
            await page.waitForSelector(selector, { visible: true, timeout: 10000 });
            await page.click(selector);
            await this.delay(100);

            await page.evaluate((sel, txt) => {
                const el = document.querySelector(sel);
                if (el) {
                    el.value = txt;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }, selector, text);

            await this.delay(100);
        } catch (error) {
            this.log(`   ⚠️ Lỗi nhập: ${error.message}`, 'warning');
        }
    }

    // Launch browser
    async launchBrowser() {
        const puppeteerPath = findPuppeteerChromiumPath();

        // Tìm Dark Reader extension
        let extensionPath = path.join(__dirname, 'extensions', 'eimadpbcbfnmbkopoojfekhnkhdbieeh', '4.9.118_0');
        if (process.resourcesPath) {
            const prodExtPath = path.join(process.resourcesPath, 'app', 'extensions', 'eimadpbcbfnmbkopoojfekhnkhdbieeh', '4.9.118_0');
            if (fs.existsSync(prodExtPath)) {
                extensionPath = prodExtPath;
            }
        }

        const launchOptions = {
            headless: false,
            defaultViewport: null,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-blink-features=AutomationControlled',
                '--start-maximized'
            ]
        };

        // Load Dark Reader extension if exists
        if (fs.existsSync(extensionPath)) {
            launchOptions.args.push(
                `--disable-extensions-except=${extensionPath}`,
                `--load-extension=${extensionPath}`
            );
        }

        if (puppeteerPath) {
            launchOptions.executablePath = puppeteerPath;
            this.log('🌐 Dùng Puppeteer Chromium bundled', 'info');
        } else {
            this.log('🌐 Dùng Puppeteer Chromium (mặc định)', 'info');
        }

        this.browser = await puppeteer.launch(launchOptions);

        // Đợi extension load
        await this.delay(2000);

        // Đóng tab intro extension
        const pages = await this.browser.pages();
        for (const p of pages) {
            const url = p.url();
            if (url.includes('darkreader') || url.includes('chrome-extension')) {
                try { await p.close(); } catch (e) { }
            }
        }

        this.page = await this.browser.newPage();

        // Set user agent
        await this.page.setUserAgent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        );

        return this.page;
    }

    // Login bằng cookies - import cookies và check đã login chưa
    async loginWithCookies(cookies) {
        this.log('🍪 Đăng nhập bằng cookies...', 'info');

        try {
            // Cần navigate tới domain trước khi set cookies
            await this.page.goto('https://admin.google.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
            await this.delay(1000);

            // Set cookies cho các domain Google
            const googleDomains = ['.google.com', 'google.com', 'accounts.google.com', 'admin.google.com'];

            for (const cookie of cookies) {
                try {
                    // Set cookie cho domain gốc
                    await this.page.setCookie({
                        name: cookie.name,
                        value: cookie.value,
                        domain: cookie.domain || '.google.com',
                        path: cookie.path || '/',
                        httpOnly: cookie.httpOnly || false,
                        secure: cookie.secure !== false,
                        sameSite: cookie.sameSite || 'Lax'
                    });
                } catch (e) {
                    // Ignore errors for individual cookies
                }
            }

            this.log(`   ✅ Đã import ${cookies.length} cookies`, 'success');

            // Reload page để áp dụng cookies
            await this.page.reload({ waitUntil: 'networkidle2', timeout: 30000 });
            await this.delay(3000);

            // Check xem đã login thành công chưa
            const currentPage = await this.detectCurrentPage(this.page);
            this.log(`   📍 Trang hiện tại: ${currentPage}`, 'info');

            if (currentPage === 'ADMIN_DASHBOARD') {
                this.log('✅ Đăng nhập bằng cookies thành công!', 'success');
                return true;
            } else {
                this.log('❌ Cookies không hợp lệ hoặc đã hết hạn', 'error');
                return false;
            }

        } catch (error) {
            this.log(`❌ Lỗi import cookies: ${error.message}`, 'error');
            return false;
        }
    }

    // Login thủ công - mở browser và đợi user đăng nhập tay
    async loginManual() {
        this.log('✋ Chế độ đăng nhập thủ công...', 'info');

        try {
            // Navigate tới admin console
            await this.page.goto('https://admin.google.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
            await this.delay(2000);

            // Gửi event tới UI để enable button
            if (this.mainWindow) {
                this.mainWindow.webContents.send('waiting-manual-login', { waiting: true });
            }

            this.log('👆 Hãy đăng nhập vào Admin Console...', 'info');
            this.log('👆 Sau khi đăng nhập xong, bấm nút "Đã đăng nhập xong" ở giao diện', 'info');

            // Đợi user click button (Promise sẽ được resolve bởi IPC handler)
            await new Promise((resolve) => {
                this.manualLoginResolve = resolve;
            });

            this.log('   ⏳ Đang kiểm tra trạng thái đăng nhập...', 'info');
            await this.delay(2000);

            // Check xem đã login thành công chưa
            const currentPage = await this.detectCurrentPage(this.page);
            this.log(`   📍 Trang hiện tại: ${currentPage}`, 'info');

            if (currentPage === 'ADMIN_DASHBOARD') {
                this.log('✅ Đăng nhập thủ công thành công!', 'success');
                return true;
            } else {
                this.log('❌ Chưa đăng nhập thành công, vui lòng thử lại', 'error');
                return false;
            }

        } catch (error) {
            this.log(`❌ Lỗi: ${error.message}`, 'error');
            return false;
        }
    }

    // Detect current page state - dùng evaluate để check element visible
    async detectCurrentPage(page) {
        const url = page.url();

        // Đã vào admin dashboard (bất kỳ path nào trên admin.google.com, trừ khi đang ở login)
        if (url.includes('admin.google.com') && !url.includes('accounts.google.com')) {
            return 'ADMIN_DASHBOARD';
        }

        if (url.includes('speedbump')) {
            return 'SPEEDBUMP_PAGE';
        }

        if (url.includes('accounts.google.com')) {
            // Dùng evaluate để check element có visible không
            const pageState = await page.evaluate(() => {
                // Check 2FA/OTP page
                const bodyText = document.body.innerText || '';
                if (bodyText.includes('2-Step Verification') || bodyText.includes('Xác minh 2 bước') ||
                    bodyText.includes('Google Authenticator') || bodyText.includes('verification code')) {
                    return 'OTP_PAGE';
                }

                // Check error states
                if (bodyText.includes("Couldn't find") || bodyText.includes('Không tìm thấy')) {
                    return 'EMAIL_NOT_FOUND';
                }
                if (bodyText.includes('Wrong password') || bodyText.includes('Sai mật khẩu')) {
                    return 'WRONG_PASSWORD';
                }

                // Check for visible password input (ưu tiên check trước email)
                const passwordInput = document.querySelector('input[type="password"]:not([aria-hidden="true"])');
                if (passwordInput) {
                    const style = window.getComputedStyle(passwordInput);
                    const rect = passwordInput.getBoundingClientRect();
                    if (style.display !== 'none' && style.visibility !== 'hidden' && rect.height > 0) {
                        return 'PASSWORD_PAGE';
                    }
                }

                // Check for visible email input
                const emailInput = document.querySelector('input[type="email"]:not([aria-hidden="true"])');
                if (emailInput) {
                    const style = window.getComputedStyle(emailInput);
                    const rect = emailInput.getBoundingClientRect();
                    if (style.display !== 'none' && style.visibility !== 'hidden' && rect.height > 0) {
                        return 'EMAIL_PAGE';
                    }
                }

                // Check for verify required
                if (bodyText.includes('verify') || bodyText.includes('Verify') || bodyText.includes('xác minh')) {
                    return 'VERIFY_REQUIRED';
                }

                return 'GOOGLE_LOGIN_OTHER';
            });

            return pageState;
        }

        return 'UNKNOWN';
    }

    // Generate OTP from secret key
    generateOTP(secret) {
        try {
            const { authenticator } = require('otplib');
            // Clean up secret (remove spaces)
            const cleanSecret = secret.replace(/\s+/g, '').toUpperCase();
            const token = authenticator.generate(cleanSecret);
            this.log(`   🔢 Generated OTP: ${token}`, 'info');
            return token;
        } catch (error) {
            this.log(`   ❌ Lỗi generate OTP: ${error.message}`, 'error');
            return null;
        }
    }

    // Handle 2FA OTP page
    async handle2FAOTP(page, otpSecret) {
        this.log('   🔐 Xử lý 2FA OTP...', 'info');

        try {
            const otp = this.generateOTP(otpSecret);
            if (!otp) {
                return false;
            }

            await this.delay(1000);

            // Find OTP input field
            const otpInputSelectors = [
                'input[name="totpPin"]',
                'input[type="tel"]',
                'input[aria-label*="code"]',
                'input[aria-label*="mã"]',
                '#totpPin'
            ];

            for (const selector of otpInputSelectors) {
                try {
                    const exists = await page.$(selector);
                    if (exists) {
                        await this.fastType(page, selector, otp);
                        await this.delay(500);

                        // Click Next/Verify button
                        await page.evaluate(() => {
                            const btns = document.querySelectorAll('button, input[type="submit"]');
                            for (const btn of btns) {
                                const text = (btn.textContent || btn.value || '').toLowerCase();
                                if (text.includes('next') || text.includes('tiếp') ||
                                    text.includes('verify') || text.includes('xác') || text.includes('done')) {
                                    btn.click();
                                    return true;
                                }
                            }
                        });

                        await this.delay(3000);
                        this.log('   ✅ Đã nhập OTP!', 'success');
                        return true;
                    }
                } catch (e) { }
            }

            this.log('   ⚠️ Không tìm thấy input OTP', 'warning');
            return false;

        } catch (error) {
            this.log(`   ❌ Lỗi 2FA: ${error.message}`, 'error');
            return false;
        }
    }

    // Login to Admin Console with state detection, retry and 2FA support
    async loginAdmin(adminEmail, adminPassword, otpSecret = null) {
        this.log('🔐 Đăng nhập Admin Console...', 'info');

        const maxRetries = 3;
        let retryCount = 0;

        while (retryCount < maxRetries) {
            retryCount++;

            try {
                await this.page.goto('https://admin.google.com', { waitUntil: 'networkidle2', timeout: 30000 });
                await this.delay(2000);

                // Check if already logged in
                let currentPage = await this.detectCurrentPage(this.page);
                this.log(`   📍 Trang hiện tại: ${currentPage}`, 'info');

                if (currentPage === 'ADMIN_DASHBOARD') {
                    this.log('✅ Đã đăng nhập sẵn', 'success');
                    return true;
                }

                // Step 1: Enter email
                if (currentPage === 'EMAIL_PAGE' || currentPage === 'GOOGLE_LOGIN_OTHER') {
                    this.log('   📧 Nhập email admin...', 'info');
                    await this.fastType(this.page, 'input[type="email"]', adminEmail);
                    await this.delay(500);

                    // Click Next
                    await this.page.evaluate(() => {
                        const btns = document.querySelectorAll('#identifierNext, button');
                        for (const btn of btns) {
                            if (btn.id === 'identifierNext' || btn.textContent.includes('Next') || btn.textContent.includes('Tiếp')) {
                                btn.click();
                                return true;
                            }
                        }
                    });

                    // Đợi password input xuất hiện hoặc error (tối đa 10s)
                    this.log('   ⏳ Đợi trang password...', 'info');
                    try {
                        await this.page.waitForFunction(() => {
                            // Check password input visible
                            const pwdInput = document.querySelector('input[type="password"]');
                            if (pwdInput) {
                                const rect = pwdInput.getBoundingClientRect();
                                if (rect.height > 0) return true;
                            }
                            // Check error
                            const bodyText = document.body.innerText || '';
                            if (bodyText.includes("Couldn't find") || bodyText.includes('Không tìm thấy')) return true;
                            return false;
                        }, { timeout: 10000 });
                    } catch (e) {
                        this.log('   ⚠️ Timeout đợi trang password', 'warning');
                    }

                    await this.delay(1000);
                    currentPage = await this.detectCurrentPage(this.page);
                    this.log(`   📍 Sau nhập email: ${currentPage}`, 'info');
                }

                // Check for email not found
                if (currentPage === 'EMAIL_NOT_FOUND') {
                    this.log('   ❌ Email không tồn tại!', 'error');
                    return false;
                }

                // Step 2: Enter password
                if (currentPage === 'PASSWORD_PAGE') {
                    this.log('   🔑 Nhập password...', 'info');
                    await this.page.waitForSelector('input[type="password"]', { visible: true, timeout: 10000 });
                    await this.fastType(this.page, 'input[type="password"]', adminPassword);
                    await this.delay(300);

                    await this.page.evaluate(() => {
                        const btns = document.querySelectorAll('#passwordNext, button');
                        for (const btn of btns) {
                            if (btn.id === 'passwordNext' || btn.textContent.includes('Next') || btn.textContent.includes('Tiếp')) {
                                btn.click();
                                return true;
                            }
                        }
                    });
                    await this.delay(4000);

                    currentPage = await this.detectCurrentPage(this.page);
                    this.log(`   📍 Sau nhập password: ${currentPage}`, 'info');
                }

                // Check for wrong password
                if (currentPage === 'WRONG_PASSWORD') {
                    this.log('   ❌ Sai mật khẩu!', 'error');
                    return false;
                }

                // Step 3: Handle 2FA OTP if needed
                if (currentPage === 'OTP_PAGE') {
                    if (otpSecret) {
                        const otpSuccess = await this.handle2FAOTP(this.page, otpSecret);
                        if (otpSuccess) {
                            await this.delay(3000);
                            currentPage = await this.detectCurrentPage(this.page);
                            this.log(`   📍 Sau OTP: ${currentPage}`, 'info');
                        } else {
                            this.log('   ❌ Không thể xử lý 2FA OTP', 'error');
                            return false;
                        }
                    } else {
                        this.log('   ❌ Cần 2FA OTP nhưng không có secret!', 'error');
                        this.log('   💡 Format: email|password|otp_secret', 'info');
                        return false;
                    }
                }

                // Handle speedbump
                if (currentPage === 'SPEEDBUMP_PAGE') {
                    await this.handleSpeedbump(this.page);
                    await this.delay(2000);
                    currentPage = await this.detectCurrentPage(this.page);
                }

                // Check final state
                if (currentPage === 'ADMIN_DASHBOARD') {
                    this.log('✅ Đăng nhập thành công!', 'success');
                    return true;
                }

                // Verify required
                if (currentPage === 'VERIFY_REQUIRED') {
                    this.log('   ⚠️ Cần xác minh bổ sung!', 'warning');
                    return false;
                }

                // Unknown state - retry
                if (retryCount < maxRetries) {
                    this.log(`   🔄 Thử lại lần ${retryCount + 1}/${maxRetries}...`, 'warning');
                }

            } catch (error) {
                this.log(`   ⚠️ Lỗi lần ${retryCount}: ${error.message}`, 'warning');
                if (retryCount < maxRetries) {
                    await this.delay(2000);
                }
            }
        }

        this.log('❌ Đăng nhập thất bại sau nhiều lần thử', 'error');
        return false;
    }

    // Navigate to bulk add page
    async goToBulkAdd() {
        this.log('📍 Vào trang thêm người dùng...', 'info');
        await this.page.goto('https://admin.google.com/ac/user/bulkadd', { waitUntil: 'networkidle2', timeout: 30000 });
        await this.delay(3000);
    }

    // Fill user form for one user
    async fillUserForm(index, firstName, lastName, emailPrefix, secondaryEmail) {
        this.log(`   📝 Điền form user ${index + 1}: ${firstName} ${lastName}`, 'info');

        try {
            // Điền Tên (First Name)
            const firstNameSelector = `#firstName_${index} input`;
            await this.page.waitForSelector(firstNameSelector, { visible: true, timeout: 5000 });
            await this.fastType(this.page, firstNameSelector, firstName);
            await this.delay(500);

            // Điền Họ (Last Name)
            const lastNameSelector = `#lastName_${index} input`;
            await this.fastType(this.page, lastNameSelector, lastName);
            await this.delay(2000); // Đợi 2s trước khi điền email

            // Điền Email prefix
            const emailSelector = `#primaryEmailIdentifier_${index} input`;
            await this.fastType(this.page, emailSelector, emailPrefix);
            await this.delay(2000); // Đợi 2s trước khi điền email phụ

            // Điền Email phụ (Secondary Email)
            const secondaryEmailSelector = `#secondaryEmail_${index} input`;
            await this.fastType(this.page, secondaryEmailSelector, secondaryEmail);
            await this.delay(500);

            return true;
        } catch (error) {
            this.log(`   ❌ Lỗi điền form: ${error.message}`, 'error');
            return false;
        }
    }

    // Click "Thêm người dùng khác" button
    async clickAddMore() {
        this.log('   ➕ Click thêm người dùng...', 'info');
        try {
            await this.page.evaluate(() => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    if (btn.textContent.includes('Thêm một người dùng khác') ||
                        btn.textContent.includes('Add another user')) {
                        btn.click();
                        return true;
                    }
                }
            });
            await this.delay(1000);
            return true;
        } catch (error) {
            this.log(`   ⚠️ Không thể thêm user: ${error.message}`, 'warning');
            return false;
        }
    }

    // Click "Tiếp tục" button
    async clickContinue() {
        this.log('   ▶️ Click Tiếp tục...', 'info');
        try {
            const clicked = await this.page.evaluate(() => {
                // Tìm bằng class button chính xác từ Google Admin
                const btn = document.querySelector('button.UywwFc-LgbsSe');
                if (btn) {
                    // Kiểm tra có chứa text "Tiếp tục" hoặc "Continue"
                    const textSpan = btn.querySelector('span.UywwFc-vQzf8d');
                    if (textSpan && (textSpan.textContent.includes('Tiếp tục') || textSpan.textContent.includes('Continue'))) {
                        btn.click();
                        return 'class-selector';
                    }
                }

                // Fallback: tìm theo jsname
                const jsnameBtn = document.querySelector('button[jsname="EwKiCc"]');
                if (jsnameBtn) {
                    jsnameBtn.click();
                    return 'jsname-selector';
                }

                // Fallback: tìm tất cả buttons
                const buttons = document.querySelectorAll('button');
                for (const b of buttons) {
                    const spans = b.querySelectorAll('span');
                    for (const span of spans) {
                        if (span.textContent.trim() === 'Tiếp tục' || span.textContent.trim() === 'Continue') {
                            b.click();
                            return 'span-text-selector';
                        }
                    }
                }

                return null;
            });

            if (clicked) {
                this.log(`   ✅ Đã click nút Tiếp tục (${clicked})`, 'success');
                await this.delay(3000);
                return true;
            } else {
                this.log('   ⚠️ Không tìm thấy nút Tiếp tục', 'warning');
                return false;
            }
        } catch (error) {
            this.log(`   ❌ Lỗi click Tiếp tục: ${error.message}`, 'error');
            return false;
        }
    }

    // Wait for user creation and send login instructions
    async waitAndSendInstructions() {
        this.log('   ⏳ Đợi tạo user...', 'info');

        // Đợi tối đa 30s cho việc tạo user
        await this.delay(5000);

        // Click "Gửi hướng dẫn đăng nhập" hoặc "Send login instructions"
        try {
            await this.page.evaluate(() => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    if (btn.textContent.includes('Gửi thông tin hướng dẫn') ||
                        btn.textContent.includes('Send login') ||
                        btn.textContent.includes('Send instructions')) {
                        btn.click();
                        return true;
                    }
                }
            });
            this.log('   📧 Đã gửi hướng dẫn đăng nhập', 'success');
            await this.delay(2000);
            return true;
        } catch (error) {
            // Nếu không có nút, có thể bỏ qua
            this.log('   ⚠️ Không tìm thấy nút gửi hướng dẫn', 'warning');
            return false;
        }
    }

    // Handle speedbump page
    async handleSpeedbump(page) {
        const url = page.url();
        if (!url.includes('speedbump')) return false;

        this.log('   ⚠️ Xử lý trang speedbump...', 'warning');

        try {
            await this.delay(1000);

            await page.evaluate(() => {
                const confirmBtn = document.querySelector('input[name="confirm"]');
                if (confirmBtn) {
                    confirmBtn.click();
                    return true;
                }

                const buttons = document.querySelectorAll('button, input[type="submit"]');
                for (const btn of buttons) {
                    const text = btn.value || btn.textContent || '';
                    if (text.includes('Tôi hiểu') || text.includes('I understand') ||
                        text.includes('Confirm') || text.includes('Continue')) {
                        btn.click();
                        return true;
                    }
                }
            });

            await this.delay(2000);
            return true;
        } catch (error) {
            this.log(`   ❌ Lỗi speedbump: ${error.message}`, 'error');
            return false;
        }
    }

    // Handle password change page
    async handlePasswordChange(page, newPassword) {
        this.log('   🔑 Đổi password...', 'info');

        try {
            // Wait for password inputs
            await page.waitForSelector('input[type="password"]', { visible: true, timeout: 10000 });
            await this.delay(500);

            // Set password values directly via evaluate (nhanh hơn type)
            await page.evaluate((pwd) => {
                const inputs = document.querySelectorAll('input[type="password"]');
                inputs.forEach(input => {
                    input.value = pwd;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                });
            }, newPassword);

            await this.delay(500);

            // Click Change password button
            await page.evaluate(() => {
                const btn = document.querySelector('input[type="submit"], #submit');
                if (btn) btn.click();
            });

            await this.delay(3000);
            this.log('   ✅ Đã đổi password!', 'success');
            return true;

        } catch (error) {
            this.log(`   ❌ Lỗi đổi password: ${error.message}`, 'error');
            return false;
        }
    }

    // Process account creation with password change
    async processAccountWithPasswordChange(secondaryEmail, finalEmail, newPassword) {
        // Set log callback cho EmailAPI
        EmailAPI.setLogCallback((msg) => this.log(msg, 'info'));

        // Check email for verification link (8 lần thử, 2s/lần = 16s max)
        this.log(`   📬 Đang check email: ${secondaryEmail}`, 'info');
        const verifyLink = await EmailAPI.checkInboxForLink(secondaryEmail, 8, 2000);

        if (!verifyLink) {
            this.log('   ❌ Không tìm thấy link verification', 'error');
            return { success: false, error: 'NO_VERIFY_LINK' };
        }

        // Open verification link in new tab
        const newPage = await this.browser.newPage();
        await newPage.setUserAgent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        );

        try {
            await newPage.goto(verifyLink, { waitUntil: 'networkidle2', timeout: 30000 });
            await this.delay(2000);

            // Handle speedbump if present
            await this.handleSpeedbump(newPage);
            await this.delay(1000);

            // Handle password change
            const pwdChanged = await this.handlePasswordChange(newPage, newPassword);

            await newPage.close();

            if (pwdChanged) {
                return { success: true, email: finalEmail, password: newPassword };
            } else {
                return { success: false, error: 'PASSWORD_CHANGE_FAILED' };
            }

        } catch (error) {
            await newPage.close();
            return { success: false, error: error.message };
        }
    }

    // Main function: Create accounts
    async start(config) {
        const { loginMode, adminEmail, adminPassword, otpSecret, cookies, accounts, passwordMode, commonPassword } = config;

        this.isRunning = true;
        this.log(`🚀 Bắt đầu tạo ${accounts.length} accounts...`, 'info');
        this.resetResultsFile();

        let created = 0;
        let failed = 0;

        try {
            // Launch browser
            await this.launchBrowser();

            // Login based on mode
            let loginSuccess = false;

            if (loginMode === 'cookies' && cookies && cookies.length > 0) {
                // Login bằng cookies
                loginSuccess = await this.loginWithCookies(cookies);
            } else if (loginMode === 'manual') {
                // Login thủ công - đợi user đăng nhập tay
                loginSuccess = await this.loginManual();
            } else {
                // Login bằng password
                loginSuccess = await this.loginAdmin(adminEmail, adminPassword, otpSecret);
            }

            if (!loginSuccess) {
                this.log('❌ Không thể đăng nhập Admin Console', 'error');
                this.isRunning = false;
                return;
            }

            // Process accounts in batches of 3
            const batchSize = 3;
            for (let batchStart = 0; batchStart < accounts.length && this.isRunning; batchStart += batchSize) {
                const batchEnd = Math.min(batchStart + batchSize, accounts.length);
                const batch = accounts.slice(batchStart, batchEnd);

                this.log(`📦 Batch ${Math.floor(batchStart / batchSize) + 1}: ${batch.length} accounts`, 'info');

                // Go to bulk add page
                await this.goToBulkAdd();
                await this.delay(2000);

                // Prepare secondary emails for this batch
                const batchData = [];
                for (let i = 0; i < batch.length; i++) {
                    const acc = batch[i];
                    const secondaryEmail = await EmailAPI.generateEmail();
                    const password = passwordMode === 'random' ? this.randomPassword() : commonPassword;

                    batchData.push({
                        ...acc,
                        secondaryEmail,
                        password
                    });

                    // Add more user slots if needed
                    if (i > 0) {
                        await this.clickAddMore();
                    }
                }

                // Fill forms
                for (let i = 0; i < batchData.length; i++) {
                    const data = batchData[i];
                    await this.fillUserForm(i, data.firstName, data.lastName, data.emailPrefix, data.secondaryEmail);
                }

                // Submit
                await this.clickContinue();
                await this.delay(5000);

                // Wait and send instructions
                await this.waitAndSendInstructions();
                await this.delay(3000);

                // Process each account's password change
                for (const data of batchData) {
                    if (!this.isRunning) break;

                    // Get the domain from the page or use default
                    const domain = await this.page.evaluate(() => {
                        const domainEl = document.querySelector('[data-value]');
                        return domainEl ? domainEl.getAttribute('data-value') : null;
                    }) || 'example.com';

                    const finalEmail = `${data.emailPrefix}@${domain}`;

                    this.sendProgress(batchStart + batchData.indexOf(data) + 1, accounts.length, `Đang xử lý: ${finalEmail}`);

                    const result = await this.processAccountWithPasswordChange(
                        data.secondaryEmail,
                        finalEmail,
                        data.password
                    );

                    if (result.success) {
                        created++;
                        this.saveResultRealtime({
                            status: 'CREATED',
                            email: finalEmail,
                            password: data.password,
                            timestamp: new Date().toISOString()
                        });
                        this.sendResult({
                            status: 'CREATED',
                            email: finalEmail,
                            password: data.password
                        });
                        this.log(`✅ Tạo thành công: ${finalEmail}`, 'success');
                    } else {
                        failed++;
                        this.saveResultRealtime({
                            status: 'FAILED',
                            email: finalEmail,
                            error: result.error,
                            timestamp: new Date().toISOString()
                        });
                        this.sendResult({
                            status: 'FAILED',
                            email: finalEmail,
                            error: result.error
                        });
                        this.log(`❌ Thất bại: ${finalEmail} - ${result.error}`, 'error');
                    }
                }
            }

        } catch (error) {
            this.log(`❌ Lỗi: ${error.message}`, 'error');
        }

        this.isRunning = false;
        this.log(`🏁 Hoàn thành! Created: ${created}, Failed: ${failed}`, 'info');

        if (this.mainWindow) {
            this.mainWindow.webContents.send('complete', { created, failed });
        }
    }

    // Stop
    async stop() {
        this.isRunning = false;
        this.log('⏹️ Đã dừng', 'warning');
    }

    // Close browser
    async closeBrowser() {
        if (this.browser) {
            await this.browser.close();
            this.browser = null;
            this.page = null;
        }
        this.log('✅ Đã đóng browser', 'info');
    }
}

module.exports = AdminWorker;
