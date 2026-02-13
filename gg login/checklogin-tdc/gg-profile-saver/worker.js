/**
 * GG Profile Saver - Worker (backend logic)
 * Login Google accounts & lưu mỗi acc vào 1 profile riêng
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Set Puppeteer cache riêng trong folder này (tách biệt, không bị tool khác xóa)
const LOCAL_BROWSER_DIR = path.join(__dirname, 'browser');
process.env.PUPPETEER_CACHE_DIR = LOCAL_BROWSER_DIR;

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

// ======================== CONFIG ========================
const CONFIG = {
    PROFILES_DIR: path.join(__dirname, 'saved_profiles'),
    DB_FILE: path.join(__dirname, 'profiles_db.json'),
    ACCOUNTS_FILE: path.join(__dirname, 'accounts.txt'),
    GITHUB_ACCOUNTS_FILE: path.join(__dirname, 'github_accounts.txt'),
    BACKUP_DIR: path.join(__dirname, 'backups'),
    LOGIN_URL: 'https://accounts.google.com/signin',
    CHECK_URL: 'https://myaccount.google.com/?utm_source=sign_in_no_continue&pli=1',
    VERIFY_WAIT: 120000,
    DELAY_BETWEEN: 2000,
};

// ======================== BROWSER DETECT ========================
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

    // Check local Puppeteer Chromium
    let localChromiumExists = false;
    try {
        const chromeDirs = path.join(LOCAL_BROWSER_DIR, 'chrome');
        if (fs.existsSync(chromeDirs)) {
            const versions = fs.readdirSync(chromeDirs);
            for (const ver of versions) {
                const exePath = path.join(chromeDirs, ver, 'chrome-win64', 'chrome.exe');
                if (fs.existsSync(exePath)) {
                    localChromiumExists = true;
                    break;
                }
            }
        }
    } catch (e) {}
    detected.push({
        id: 'puppeteer',
        name: localChromiumExists ? 'Puppeteer Chromium (Local)' : 'Puppeteer Chromium (Chưa tải)',
        detected: localChromiumExists,
        path: null
    });

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

// ======================== ProfileWorker CLASS ========================
class ProfileWorker {
    constructor(mainWindow, selectedBrowserId = null, options = {}) {
        this.mainWindow = mainWindow;
        this.isRunning = false;
        this.openBrowsers = new Map();
        this.selectedBrowserId = selectedBrowserId;
        this.headless = options.headless || false;
    }

    // ---- Logging ----
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

    sendProfilesUpdate() {
        if (this.mainWindow) this.mainWindow.webContents.send('profiles-updated');
    }

    delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

    // ---- Database ----
    loadDB() {
        if (fs.existsSync(CONFIG.DB_FILE)) {
            return JSON.parse(fs.readFileSync(CONFIG.DB_FILE, 'utf8'));
        }
        return {};
    }

    saveDB(db) {
        fs.writeFileSync(CONFIG.DB_FILE, JSON.stringify(db, null, 2), 'utf8');
    }

    getNextProfileNum(db) {
        let max = 0;
        for (const key of Object.keys(db)) {
            const num = parseInt(db[key].profileDir.replace('Profile_', ''));
            if (num > max) max = num;
        }
        return max + 1;
    }

    // ---- Accounts ----
    loadAccounts(filePath) {
        if (!fs.existsSync(filePath)) return [];
        const content = fs.readFileSync(filePath, 'utf8').trim();
        if (!content) return [];
        return content.split('\n')
            .map(line => line.trim())
            .filter(line => line && !line.startsWith('#') && line.includes('|'))
            .map(line => {
                const [email, password] = line.split('|', 2);
                return { email: email.trim(), password: password.trim() };
            })
            .filter(a => a.email && a.password);
    }

    // ---- Browser ----
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

    async launchProfileBrowser(profileDir) {
        const profilePath = path.join(CONFIG.PROFILES_DIR, profileDir);
        if (!fs.existsSync(profilePath)) fs.mkdirSync(profilePath, { recursive: true });

        const launchArgs = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--start-maximized',
        ];

        const launchOptions = {
            headless: this.headless ? 'new' : false,
            args: launchArgs,
            userDataDir: profilePath,
            defaultViewport: null,
        };

        // Chọn browser: ưu tiên user chọn → fallback tự động
        if (this.selectedBrowserId && this.selectedBrowserId !== 'puppeteer') {
            const browserPath = getBrowserPath(this.selectedBrowserId);
            if (browserPath) launchOptions.executablePath = browserPath;
        } else if (this.selectedBrowserId === 'puppeteer') {
            // Dùng local Puppeteer Chromium (đã set PUPPETEER_CACHE_DIR)
            // Nếu không có, tự fallback sang Chrome/Edge trên máy
            const allBrowsers = detectAllBrowsers();
            const puppeteerEntry = allBrowsers.find(b => b.id === 'puppeteer');
            if (!puppeteerEntry || !puppeteerEntry.detected) {
                // Fallback: tìm Chrome hoặc Edge trên máy
                const fallback = allBrowsers.find(b => b.id !== 'puppeteer' && b.detected);
                if (fallback) {
                    launchOptions.executablePath = fallback.path;
                    this.log(`   ⚠️ Puppeteer Chromium chưa tải, dùng ${fallback.name}`, 'warning');
                }
                // Nếu không có gì → puppeteer tự throw error rõ ràng
            }
        }

        return await puppeteer.launch(launchOptions);
    }

    // ---- Login Flow ----
    async loginAccount(email, password, profileDir, index, total) {
        if (!this.isRunning) return null;

        const startTime = Date.now();
        this.log(`[${index + 1}/${total}] 🚀 ${email} → ${profileDir}`, 'info');
        this.sendProgress(index, total, `${index + 1}/${total}: ${email}`);

        let browser;
        try {
            browser = await this.launchProfileBrowser(profileDir);
        } catch (err) {
            this.log(`   ❌ Không mở được browser: ${err.message}`, 'error');
            return { email, password, profileDir, status: 'error', reason: 'BROWSER_ERROR', time: 0 };
        }

        this.openBrowsers.set(profileDir, browser);
        const pages = await browser.pages();
        const page = pages[0] || await browser.newPage();
        await page.setUserAgent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        );
        await page.evaluateOnNewDocument(() => {
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        });

        let result = { email, password, profileDir, status: 'error', reason: 'UNKNOWN', time: 0 };

        try {
            // Step 1: Vào Google login
            this.log(`   📍 Vào trang đăng nhập...`, 'info');
            await page.goto(CONFIG.LOGIN_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
            await this.delay(2000);

            // Step 2: Nhập email
            this.log(`   📧 Nhập email...`, 'info');
            await this.fastType(page, 'input[type="email"]', email);
            await this.delay(300);

            await page.evaluate(() => {
                const btns = document.querySelectorAll('#identifierNext, button');
                for (const btn of btns) {
                    if (btn.id === 'identifierNext' || btn.textContent.includes('Next') || btn.textContent.includes('Tiếp')) {
                        btn.click(); return true;
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
                this.log(`   🗑️ Account đã bị xóa!`, 'error');
                result.status = 'email_error'; result.reason = 'ACCOUNT_DELETED';
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
                return result;
            }

            if (afterEmailContent.includes("Couldn't find") || afterEmailContent.includes('Không tìm thấy')) {
                this.log(`   ❌ Email không tồn tại!`, 'error');
                result.status = 'email_error'; result.reason = 'EMAIL_NOT_FOUND';
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
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
                            btn.click(); return true;
                        }
                    }
                    return false;
                });

                // Chờ navigation sau khi nhấn Next password
                try {
                    await page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 15000 });
                } catch (navErr) {
                    // Navigation timeout OK - trang có thể đã chuyển
                }
                await this.delay(3000);
            } catch (passError) {
                this.log(`   ⚠️ Không thấy trang password (CAPTCHA?)`, 'warning');
                result.status = 'error'; result.reason = 'NO_PASSWORD_PAGE';
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
                return result;
            }

            // Step 4: Check kết quả
            let finalContent = '';
            let finalUrl = '';
            try {
                finalUrl = page.url();
                finalContent = await page.content();
            } catch (ctxError) {
                // Context destroyed = trang đã navigate = login có thể OK
                this.log(`   ⏳ Trang đang chuyển...`, 'info');
                await this.delay(3000);
                try {
                    finalUrl = page.url();
                    finalContent = await page.content();
                } catch (e2) {
                    // Vẫn lỗi → coi như login thành công (trang đã redirect)
                    result.status = 'logged_in'; result.reason = 'LOGIN_OK';
                    this.log(`   ✅ Login thành công! (redirect detected)`, 'success');
                }
            }

            // Sai mật khẩu
            if (finalContent.includes('Wrong password') || finalContent.includes('Sai mật khẩu') ||
                finalContent.includes('password was changed') || finalContent.includes('mật khẩu đã được thay đổi') ||
                finalUrl.includes('challenge/pwd')) {
                this.log(`   ❌ Sai mật khẩu!`, 'error');
                result.status = 'wrong_password'; result.reason = 'WRONG_PASSWORD';
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
                return result;
            }

            // Challenge/dp - đã có SĐT (Google gửi notification qua điện thoại)
            if (finalUrl.includes('challenge/dp') ||
                finalContent.includes('Open the Gmail app') ||
                finalContent.includes('Google sent a notification') ||
                finalContent.includes('Mở ứng dụng Gmail') ||
                finalContent.includes('Google đã gửi thông báo')) {
                result.status = 'has_phone'; result.reason = 'HAS_PHONE_VERIFY';
                this.log(`   📱 Đã có SĐT - cần xác minh qua điện thoại`, 'warning');
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
                return result;
            }

            // Challenge/iap - chưa có SĐT (cần nhập số điện thoại)
            if (finalUrl.includes('challenge/iap') ||
                finalContent.includes('Enter a phone number') ||
                finalContent.includes('Nhập số điện thoại') ||
                finalContent.includes('get a text message') ||
                finalContent.includes('nhận tin nhắn')) {
                result.status = 'need_phone'; result.reason = 'NEED_PHONE_VERIFY';
                this.log(`   📵 Chưa có SĐT - cần nhập số điện thoại`, 'warning');
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
                return result;
            }

            // Các challenge khác - phân loại bằng nội dung trang
            if (finalUrl.includes('challenge/') || finalUrl.includes('signin/rejected') ||
                finalContent.includes('Verify it') || finalContent.includes('Verify your identity') ||
                finalContent.includes('verification code') ||
                finalContent.includes('mã xác minh') || finalContent.includes('Xác minh danh tính')) {
                const pageText = await page.evaluate(() => document.body.innerText).catch(() => '');
                if (pageText.includes('Open the Gmail app') || pageText.includes('notification') ||
                    pageText.includes('Mở ứng dụng Gmail')) {
                    result.status = 'has_phone'; result.reason = 'HAS_PHONE_VERIFY';
                    this.log(`   📱 Đã có SĐT - xác minh qua thiết bị`, 'warning');
                } else if (pageText.includes('phone number') || pageText.includes('số điện thoại')) {
                    result.status = 'need_phone'; result.reason = 'NEED_PHONE_VERIFY';
                    this.log(`   📵 Chưa có SĐT - cần nhập SĐT`, 'warning');
                } else {
                    result.status = 'has_phone'; result.reason = 'UNKNOWN_CHALLENGE';
                    this.log(`   📱 Challenge không xác định`, 'warning');
                }
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
                return result;
            }

            // Step 5: Check speedbump
            if (result.status !== 'logged_in') {
                if (finalUrl.includes('speedbump')) {
                    this.log(`   ⚡ Speedbump!`, 'success');
                    await this.delay(1500);
                    await page.evaluate(() => {
                        const confirmBtn = document.querySelector('input[name="confirm"]');
                        if (confirmBtn) { confirmBtn.click(); return; }
                        const buttons = document.querySelectorAll('button, input[type="submit"]');
                        for (const btn of buttons) {
                            const text = btn.value || btn.textContent || '';
                            if (text.includes('Tôi hiểu') || text.includes('I understand') ||
                                text.includes('Confirm') || text.includes('Continue')) {
                                btn.click(); return;
                            }
                        }
                        const el = document.querySelector('#confirm, .MK9CEd');
                        if (el) el.click();
                    });
                    await this.delay(2000);
                    this.log(`   ✅ Speedbump OK!`, 'success');
                    result.status = 'logged_in'; result.reason = 'SPEEDBUMP_ACCEPTED';
                } else if (finalUrl.includes('myaccount.google.com') ||
                           finalUrl.includes('google.com/search') ||
                           !finalUrl.includes('accounts.google.com')) {
                    result.status = 'logged_in'; result.reason = 'LOGIN_OK';
                    this.log(`   ✅ Login thành công!`, 'success');
                } else {
                    await this.delay(3000);
                    const retryUrl = page.url();
                    if (retryUrl.includes('speedbump')) {
                        await page.evaluate(() => {
                            const el = document.querySelector('input[name="confirm"], #confirm, .MK9CEd');
                            if (el) { el.click(); return; }
                            const buttons = document.querySelectorAll('button, input[type="submit"]');
                            for (const btn of buttons) {
                                const text = btn.value || btn.textContent || '';
                                if (text.includes('Tôi hiểu') || text.includes('I understand')) {
                                    btn.click(); return;
                                }
                            }
                        });
                        await this.delay(2000);
                        result.status = 'logged_in'; result.reason = 'SPEEDBUMP_ACCEPTED';
                        this.log(`   ✅ Speedbump OK!`, 'success');
                    } else if (!retryUrl.includes('accounts.google.com')) {
                        result.status = 'logged_in'; result.reason = 'LOGIN_OK';
                        this.log(`   ✅ Login thành công!`, 'success');
                    } else {
                        this.log(`   ⚠️ Kẹt ở trang login`, 'warning');
                        result.status = 'error'; result.reason = 'STUCK_AT_LOGIN';
                        result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                        this.sendResult(result);
                        return result;
                    }
                }
            }

            // Step 6: Verify session bằng email trên myaccount
            if (result.status === 'logged_in') {
                this.log(`   🔍 Kiểm tra session...`, 'info');
                try {
                    await page.goto(CONFIG.CHECK_URL, { waitUntil: 'domcontentloaded', timeout: 15000 });
                    await this.delay(3000);
                    const emailOnPage = await page.evaluate(() => {
                        const el = document.querySelector('.fwyMNe');
                        return el ? el.textContent.trim() : '';
                    });
                    if (emailOnPage && emailOnPage.toLowerCase() === email.toLowerCase()) {
                        this.log(`   ✅ Session OK! Email: ${emailOnPage}`, 'success');
                    } else if (emailOnPage) {
                        this.log(`   ✅ Session OK! (${emailOnPage})`, 'success');
                    } else {
                        const checkUrl = page.url();
                        if (checkUrl.includes('myaccount.google.com')) {
                            this.log(`   ✅ Session OK! Profile đã lưu.`, 'success');
                        } else {
                            this.log(`   ⚠️ Session redirect, profile vẫn lưu.`, 'warning');
                        }
                    }
                } catch (e) {
                    this.log(`   ⚠️ Không check session, profile vẫn lưu.`, 'warning');
                }
            }

        } catch (error) {
            this.log(`   ❌ Lỗi: ${error.message}`, 'error');
            result.status = 'error'; result.reason = 'ERROR';
        }

        result.time = ((Date.now() - startTime) / 1000).toFixed(1);

        // Giữ browser mở nếu login OK, đóng nếu thất bại
        if (result.status !== 'logged_in') {
            try { await browser.close(); } catch (e) {}
            this.openBrowsers.delete(profileDir);
        }

        this.sendResult(result);
        this.log(`   ⏱️ ${result.status} - ${result.reason} (${result.time}s)`, result.status === 'logged_in' ? 'success' : 'warning');
        return result;
    }

    // ---- Check session cho account đã login ----
    async checkSession(email, profileDir, index, total) {
        if (!this.isRunning) return null;

        const startTime = Date.now();
        this.log(`[${index + 1}/${total}] 🔍 Kiểm tra session ${email} → ${profileDir}`, 'info');
        this.sendProgress(index, total, `${index + 1}/${total}: ${email} (check session)`);

        let browser;
        try {
            browser = await this.launchProfileBrowser(profileDir);
        } catch (err) {
            this.log(`   ❌ Không mở được browser: ${err.message}`, 'error');
            return { email, profileDir, status: 'error', reason: 'BROWSER_ERROR', time: 0 };
        }

        this.openBrowsers.set(profileDir, browser);
        const pages = await browser.pages();
        const page = pages[0] || await browser.newPage();

        let result = { email, profileDir, status: 'error', reason: 'SESSION_EXPIRED', time: 0 };

        try {
            await page.goto(CONFIG.CHECK_URL, { waitUntil: 'domcontentloaded', timeout: 20000 });
            await this.delay(3000);

            const emailOnPage = await page.evaluate(() => {
                const el = document.querySelector('.fwyMNe');
                return el ? el.textContent.trim() : '';
            });

            if (emailOnPage && emailOnPage.toLowerCase() === email.toLowerCase()) {
                this.log(`   ✅ Session còn sống! Email: ${emailOnPage}`, 'success');
                result.status = 'logged_in';
                result.reason = 'SESSION_OK';
            } else if (emailOnPage) {
                this.log(`   ✅ Session OK! (${emailOnPage})`, 'success');
                result.status = 'logged_in';
                result.reason = 'SESSION_OK';
            } else {
                const checkUrl = page.url();
                if (checkUrl.includes('myaccount.google.com')) {
                    this.log(`   ✅ Session OK!`, 'success');
                    result.status = 'logged_in';
                    result.reason = 'SESSION_OK';
                } else {
                    this.log(`   ⚠️ Session hết hạn, cần login lại`, 'warning');
                }
            }
        } catch (e) {
            this.log(`   ⚠️ Không check được session: ${e.message}`, 'warning');
        }

        result.time = ((Date.now() - startTime) / 1000).toFixed(1);

        if (result.status !== 'logged_in') {
            try { await browser.close(); } catch (e) {}
            this.openBrowsers.delete(profileDir);
        }

        this.sendResult(result);
        this.log(`   ⏱️ ${result.status} - ${result.reason} (${result.time}s)`, result.status === 'logged_in' ? 'success' : 'warning');
        return result;
    }

    // ---- Login All ----
    async startLoginAll(accounts) {
        this.isRunning = true;
        let db = this.loadDB();
        const startTime = Date.now();

        // Deduplicate accounts (giữ entry đầu tiên)
        const seen = new Set();
        const uniqueAccounts = accounts.filter(a => {
            const key = a.email.toLowerCase();
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });
        if (uniqueAccounts.length < accounts.length) {
            this.log(`⚠️ Bỏ qua ${accounts.length - uniqueAccounts.length} accounts trùng lặp`, 'warning');
        }

        // Chia thành 2 nhóm: đã login OK và chưa login
        const alreadyOK = [];
        const needLogin = [];
        for (const acc of uniqueAccounts) {
            const entry = db[acc.email];
            if (entry && entry.status === 'logged_in') {
                alreadyOK.push({ ...acc, profileDir: entry.profileDir });
            } else {
                // Gán profileDir
                if (db[acc.email]) {
                    acc.profileDir = db[acc.email].profileDir;
                } else {
                    const num = this.getNextProfileNum(db);
                    acc.profileDir = `Profile_${num}`;
                    db[acc.email] = { profileDir: acc.profileDir, status: 'pending', reason: '', lastLogin: '' };
                    this.saveDB(db);
                    db = this.loadDB();
                }
                needLogin.push(acc);
            }
        }

        const totalWork = uniqueAccounts.length;
        this.log(`🚀 Tổng: ${totalWork} accounts (${alreadyOK.length} check session + ${needLogin.length} cần login)`, 'info');

        // Phase 1: Check session song song (mỗi profile userDataDir riêng)
        if (alreadyOK.length > 0) {
            this.log(`🔍 Check session ${alreadyOK.length} accounts...`, 'info');
            const sessionPromises = [];
            for (let i = 0; i < alreadyOK.length && this.isRunning; i++) {
                if (i > 0) await this.delay(1500);
                const acc = alreadyOK[i];
                sessionPromises.push(
                    this.checkSession(acc.email, acc.profileDir, i, totalWork)
                        .then(result => {
                            if (!result) return null;
                            const curDb = this.loadDB();
                            curDb[acc.email] = {
                                profileDir: acc.profileDir,
                                status: result.status,
                                reason: result.reason,
                                lastLogin: new Date().toISOString(),
                            };
                            this.saveDB(curDb);
                            this.sendProfilesUpdate();
                            if (result.status !== 'logged_in') {
                                needLogin.push({ email: acc.email, password: acc.password, profileDir: acc.profileDir });
                            }
                            return result;
                        })
                );
            }
            await Promise.all(sessionPromises);
        }

        // Phase 2: Login song song
        if (needLogin.length > 0 && this.isRunning) {
            this.log(`🚀 Mở ${needLogin.length} browsers song song...`, 'info');
            const loginPromises = [];
            const offset = alreadyOK.length;
            for (let i = 0; i < needLogin.length && this.isRunning; i++) {
                if (i > 0) await this.delay(1500);
                const acc = needLogin[i];
                if (!acc.password) continue;
                loginPromises.push(
                    this.loginAccount(acc.email, acc.password, acc.profileDir, offset + i, totalWork)
                        .then(result => {
                            if (!result) return null;
                            const curDb = this.loadDB();
                            curDb[acc.email] = {
                                profileDir: acc.profileDir,
                                status: result.status,
                                reason: result.reason,
                                lastLogin: new Date().toISOString(),
                            };
                            this.saveDB(curDb);
                            this.sendProfilesUpdate();
                            return result;
                        })
                );
            }
            await Promise.all(loginPromises);
        }

        // Đếm kết quả
        db = this.loadDB();
        let loggedIn = 0, failed = 0;
        for (const acc of uniqueAccounts) {
            if (db[acc.email]?.status === 'logged_in') loggedIn++;
            else failed++;
        }

        const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
        this.sendComplete({ total: totalWork, loggedIn, failed, skipped: 0, totalTime });
        this.isRunning = false;
    }

    // ---- Import ----
    importAccounts() {
        const importSources = [
            { name: 'tdc-login-tool/passed.txt', path: path.join(__dirname, '..', 'tdc-login-tool', 'passed.txt') },
            { name: 'tdc-login-tool/has_phone.txt', path: path.join(__dirname, '..', 'tdc-login-tool', 'has_phone.txt') },
            { name: 'gg login flow_v3/has_flow.txt', path: path.join(__dirname, '..', '..', '..', 'gg login flow_v3', 'has_flow.txt') },
            { name: 'gg login flow_v3/no_flow.txt', path: path.join(__dirname, '..', '..', '..', 'gg login flow_v3', 'no_flow.txt') },
        ];

        const existing = new Set(this.loadAccounts(CONFIG.ACCOUNTS_FILE).map(a => a.email));
        let totalImported = 0;
        const results = [];

        for (const source of importSources) {
            if (!fs.existsSync(source.path)) {
                results.push({ name: source.name, status: 'not_found', imported: 0, skipped: 0 });
                continue;
            }
            const accounts = this.loadAccounts(source.path);
            const newAccounts = accounts.filter(a => !existing.has(a.email));

            if (newAccounts.length > 0) {
                const lines = newAccounts.map(a => `${a.email}|${a.password}`).join('\n') + '\n';
                fs.appendFileSync(CONFIG.ACCOUNTS_FILE, lines);
                newAccounts.forEach(a => existing.add(a.email));
            }

            totalImported += newAccounts.length;
            results.push({ name: source.name, status: 'ok', imported: newAccounts.length, skipped: accounts.length - newAccounts.length });
        }

        return { totalImported, totalAccounts: existing.size, sources: results };
    }

    // ---- Profile Management ----
    getProfiles() {
        const db = this.loadDB();
        const profiles = Object.entries(db).map(([email, entry], i) => ({
            email,
            ...entry,
            sortOrder: entry.sortOrder !== undefined ? entry.sortOrder : i
        }));
        profiles.sort((a, b) => a.sortOrder - b.sortOrder);
        return profiles;
    }

    async openProfile(email) {
        const db = this.loadDB();
        if (!db[email]) return { success: false, reason: 'NOT_FOUND' };

        const entry = db[email];

        // Nếu browser cho profile này đã mở
        if (this.openBrowsers.has(entry.profileDir)) {
            const existing = this.openBrowsers.get(entry.profileDir);
            if (existing.isConnected()) {
                this.log(`📂 Browser cho ${email} đã mở sẵn`, 'info');
                return { success: true };
            }
            this.openBrowsers.delete(entry.profileDir);
        }

        this.log(`📂 Mở profile: ${entry.profileDir} (${email})`, 'info');

        try {
            const browser = await this.launchProfileBrowser(entry.profileDir);
            this.openBrowsers.set(entry.profileDir, browser);
            const pages = await browser.pages();
            const page = pages[0] || await browser.newPage();
            await page.goto('https://myaccount.google.com', { waitUntil: 'domcontentloaded', timeout: 30000 });

            this.log(`✅ Browser đã mở cho ${email}`, 'success');
            return { success: true };
        } catch (e) {
            this.log(`❌ Không mở được: ${e.message}`, 'error');
            return { success: false, reason: 'BROWSER_ERROR' };
        }
    }

    async openAllProfiles() {
        const db = this.loadDB();
        const loggedIn = Object.entries(db).filter(([_, v]) => v.status === 'logged_in');

        if (loggedIn.length === 0) return { success: false, reason: 'NO_PROFILES', count: 0 };

        this.log(`🚀 Mở ${loggedIn.length} profiles...`, 'info');
        let opened = 0;

        for (const [email, entry] of loggedIn) {
            if (this.openBrowsers.has(entry.profileDir)) {
                const existing = this.openBrowsers.get(entry.profileDir);
                if (existing.isConnected()) {
                    this.log(`   📂 ${email} đã mở sẵn`, 'info');
                    opened++;
                    continue;
                }
                this.openBrowsers.delete(entry.profileDir);
            }

            try {
                const browser = await this.launchProfileBrowser(entry.profileDir);
                this.openBrowsers.set(entry.profileDir, browser);
                const pages = await browser.pages();
                const page = pages[0] || await browser.newPage();
                await page.goto('https://myaccount.google.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
                this.log(`   ✅ Đã mở ${email}`, 'success');
                opened++;
                await this.delay(1000);
            } catch (e) {
                this.log(`   ❌ Lỗi mở ${email}: ${e.message}`, 'error');
            }
        }

        this.log(`✅ Đã mở ${opened}/${loggedIn.length} profiles`, 'success');
        return { success: true, count: opened };
    }

    cleanProfiles() {
        const db = this.loadDB();
        const entries = Object.entries(db);
        const toDelete = entries.filter(([_, v]) => v.status !== 'logged_in');

        if (toDelete.length === 0) return { deleted: 0, kept: entries.length };

        for (const [email, entry] of toDelete) {
            const profilePath = path.join(CONFIG.PROFILES_DIR, entry.profileDir);
            if (fs.existsSync(profilePath)) {
                try {
                    fs.rmSync(profilePath, { recursive: true, force: true });
                } catch (e) {}
            }
            delete db[email];
            this.log(`🗑️ Xóa ${email} (${entry.profileDir}) - ${entry.status}`, 'warning');
        }

        this.saveDB(db);
        return { deleted: toDelete.length, kept: entries.length - toDelete.length };
    }

    deleteProfile(email) {
        const db = this.loadDB();
        if (!db[email]) return false;

        const entry = db[email];
        const profilePath = path.join(CONFIG.PROFILES_DIR, entry.profileDir);
        if (fs.existsSync(profilePath)) {
            try { fs.rmSync(profilePath, { recursive: true, force: true }); } catch (e) {}
        }
        delete db[email];
        this.saveDB(db);
        this.log(`🗑️ Đã xóa profile ${entry.profileDir} (${email})`, 'warning');
        return true;
    }

    // ---- Backup / Restore ----
    backup() {
        if (!fs.existsSync(CONFIG.BACKUP_DIR)) fs.mkdirSync(CONFIG.BACKUP_DIR, { recursive: true });

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const backupName = `backup_${timestamp}`;
        const backupPath = path.join(CONFIG.BACKUP_DIR, backupName);
        fs.mkdirSync(backupPath, { recursive: true });

        let files = [];

        if (fs.existsSync(CONFIG.DB_FILE)) {
            fs.copyFileSync(CONFIG.DB_FILE, path.join(backupPath, 'profiles_db.json'));
            files.push('profiles_db.json');
        }

        if (fs.existsSync(CONFIG.PROFILES_DIR)) {
            try {
                execSync(`xcopy "${CONFIG.PROFILES_DIR}" "${path.join(backupPath, 'saved_profiles')}\\" /E /I /Q /Y`, { stdio: 'pipe' });
                files.push('saved_profiles/');
            } catch (e) {}
        }

        if (fs.existsSync(CONFIG.ACCOUNTS_FILE)) {
            fs.copyFileSync(CONFIG.ACCOUNTS_FILE, path.join(backupPath, 'accounts.txt'));
            files.push('accounts.txt');
        }

        this.log(`💾 Backup hoàn thành: ${backupName}`, 'success');
        return { name: backupName, path: backupPath, files };
    }

    listBackups() {
        if (!fs.existsSync(CONFIG.BACKUP_DIR)) return [];
        return fs.readdirSync(CONFIG.BACKUP_DIR)
            .filter(f => fs.statSync(path.join(CONFIG.BACKUP_DIR, f)).isDirectory())
            .sort().reverse();
    }

    restore(backupName) {
        const backupPath = path.join(CONFIG.BACKUP_DIR, backupName);
        if (!fs.existsSync(backupPath)) return { success: false, reason: 'NOT_FOUND' };

        let files = [];

        const dbBackup = path.join(backupPath, 'profiles_db.json');
        if (fs.existsSync(dbBackup)) {
            fs.copyFileSync(dbBackup, CONFIG.DB_FILE);
            files.push('profiles_db.json');
        }

        const profilesBackup = path.join(backupPath, 'saved_profiles');
        if (fs.existsSync(profilesBackup)) {
            try {
                execSync(`xcopy "${profilesBackup}" "${CONFIG.PROFILES_DIR}\\" /E /I /Q /Y`, { stdio: 'pipe' });
                files.push('saved_profiles/');
            } catch (e) {}
        }

        const accBackup = path.join(backupPath, 'accounts.txt');
        if (fs.existsSync(accBackup)) {
            fs.copyFileSync(accBackup, CONFIG.ACCOUNTS_FILE);
            files.push('accounts.txt');
        }

        this.log(`♻️ Restore hoàn thành từ ${backupName}`, 'success');
        return { success: true, files };
    }

    // ---- Stop / Close ----
    stop() {
        this.isRunning = false;
        this.log('⏸ Đã dừng!', 'warning');
    }

    async closeAllBrowsers() {
        const count = this.openBrowsers.size;
        for (const [_, browser] of this.openBrowsers) {
            try { await browser.close(); } catch (e) {}
        }
        this.openBrowsers = new Map();
        this.log(`✖ Đã đóng ${count} browsers`, 'warning');
        return count;
    }

    // ---- Read accounts file ----
    readAccountsFile() {
        if (!fs.existsSync(CONFIG.ACCOUNTS_FILE)) return '';
        return fs.readFileSync(CONFIG.ACCOUNTS_FILE, 'utf8');
    }

    saveAccountsFile(content) {
        fs.writeFileSync(CONFIG.ACCOUNTS_FILE, content, 'utf8');
    }

    // ---- Rename Profile (display name) ----
    renameProfile(email, newDisplayName) {
        const db = this.loadDB();
        if (!db[email]) return { success: false, reason: 'NOT_FOUND' };
        const entry = db[email];
        const oldName = entry.displayName || entry.profileDir;
        entry.displayName = newDisplayName;
        this.saveDB(db);
        this.log(`✏️ Đổi tên: ${oldName} → ${newDisplayName}`, 'success');
        return { success: true, oldName, newName: newDisplayName };
    }

    // ---- Reorder Profiles ----
    reorderProfile(email, direction) {
        const db = this.loadDB();
        if (!db[email]) return false;
        const entries = Object.entries(db);
        // Assign sortOrder if missing
        entries.forEach(([_, v], i) => { if (v.sortOrder === undefined) v.sortOrder = i; });
        entries.sort((a, b) => (a[1].sortOrder || 0) - (b[1].sortOrder || 0));

        const idx = entries.findIndex(([e]) => e === email);
        if (idx < 0) return false;

        const swapIdx = direction === 'up' ? idx - 1 : idx + 1;
        if (swapIdx < 0 || swapIdx >= entries.length) return false;

        // Swap sortOrder
        const tmp = entries[idx][1].sortOrder;
        entries[idx][1].sortOrder = entries[swapIdx][1].sortOrder;
        entries[swapIdx][1].sortOrder = tmp;

        this.saveDB(db);
        return true;
    }

    // ---- GitHub Signup ----
    async githubSignupMultiple(emails) {
        this.isRunning = true;
        const db = this.loadDB();
        const startTime = Date.now();
        const total = emails.length;
        let successCount = 0, failedCount = 0;

        this.log(`🐙 GitHub Signup: ${total} accounts...`, 'info');

        for (let i = 0; i < total; i++) {
            if (!this.isRunning) break;
            const email = emails[i];
            const entry = db[email];
            if (!entry || entry.status !== 'logged_in') {
                this.log(`⚠️ Bỏ qua ${email} (chưa login Google)`, 'warning');
                failedCount++;
                continue;
            }

            const username = generateRandomUsername(email);
            const ghPassword = generateRandomPassword();

            this.log(`[${i + 1}/${total}] 🐙 ${email} → ${username}`, 'info');
            this.sendProgress(i, total, `${i + 1}/${total}: ${email}`);

            let browser;
            let reusingBrowser = false;

            // Check if browser is already open for this profile
            if (this.openBrowsers.has(entry.profileDir)) {
                const existing = this.openBrowsers.get(entry.profileDir);
                if (existing.isConnected()) {
                    browser = existing;
                    reusingBrowser = true;
                    this.log(`   📂 Tái sử dụng browser đang mở`, 'info');
                } else {
                    this.openBrowsers.delete(entry.profileDir);
                }
            }

            if (!browser) {
                try {
                    browser = await this.launchProfileBrowser(entry.profileDir);
                } catch (err) {
                    this.log(`   ❌ Không mở được browser: ${err.message}`, 'error');
                    failedCount++;
                    continue;
                }
                this.openBrowsers.set(entry.profileDir, browser);
            }

            // Open new tab for GitHub signup
            const page = await browser.newPage();

            if (!reusingBrowser) {
                await page.setUserAgent(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                );
                await page.evaluateOnNewDocument(() => {
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                });
            }

            try {
                this.log(`   🔗 Vào github.com/signup...`, 'info');
                await page.goto('https://github.com/signup', { waitUntil: 'networkidle2', timeout: 30000 });
                await this.delay(2000);

                // Detect form type
                const formType = await page.evaluate(() => {
                    const emailInput = document.querySelector('#email, input[name="user[email]"]');
                    const passInput = document.querySelector('#password, input[name="user[password]"]');
                    const loginInput = document.querySelector('#login, input[name="user[login]"]');
                    const isVisible = (el) => {
                        if (!el) return false;
                        const style = window.getComputedStyle(el);
                        return style.display !== 'none' && style.visibility !== 'hidden' && el.offsetWidth > 0;
                    };
                    if (isVisible(emailInput) && isVisible(passInput) && isVisible(loginInput)) return 'single';
                    return 'multi';
                });

                if (formType === 'single') {
                    await this._ghFillField(page, '#email, input[name="user[email]"], input[type="email"]', email);
                    await this.delay(600);
                    await this._ghFillField(page, '#password, input[name="user[password]"], input[type="password"]', ghPassword);
                    await this.delay(600);
                    await this._ghFillField(page, '#login, input[name="user[login]"], input[name="login"]', username);
                    await this.delay(600);
                    await this._ghHandleEmailPref(page);
                } else {
                    // Multi-step
                    await this._ghFillField(page, '#email, input[type="email"]', email);
                    await this.delay(800);
                    await this._ghClickContinue(page);
                    await this.delay(2000);

                    await page.waitForSelector('#password', { visible: true, timeout: 10000 }).catch(() => {});
                    await this._ghFillField(page, '#password, input[type="password"]', ghPassword);
                    await this.delay(800);
                    await this._ghClickContinue(page);
                    await this.delay(2000);

                    await page.waitForSelector('#login', { visible: true, timeout: 10000 }).catch(() => {});
                    await this._ghFillField(page, '#login, input[name="login"]', username);
                    await this.delay(800);
                    await this._ghClickContinue(page);
                    await this.delay(2000);

                    await this._ghHandleEmailPref(page);
                    await this._ghClickContinue(page);
                    await this.delay(1000);
                }

                // Click Create account
                this.log(`   🖱️ Bấm Create account...`, 'info');
                await this._ghClickCreate(page);
                await this.delay(1000);

                this.log(`   ✅ Đã điền form! Chờ giải captcha...`, 'success');

                // Emit event to UI - waiting for manual captcha
                if (this.mainWindow) {
                    this.mainWindow.webContents.send('github-waiting', {
                        email, username, ghPassword, index: i, total
                    });
                }

                // Wait for manual resolution
                const status = await new Promise((resolve) => {
                    this._ghResolves = this._ghResolves || new Map();
                    this._ghResolves.set(email, resolve);
                });

                const curDb = this.loadDB();
                if (status === 'done') {
                    curDb[email].github = {
                        username,
                        password: ghPassword,
                        status: 'registered',
                        registeredAt: new Date().toISOString()
                    };
                    this.saveDB(curDb);
                    // Save to github_accounts.txt
                    const line = `${email}|${ghPassword}|${username}\n`;
                    fs.appendFileSync(CONFIG.GITHUB_ACCOUNTS_FILE, line);
                    this.log(`   🎉 GitHub OK: ${email} | ${username} | ${ghPassword}`, 'success');
                    this.log(`   💾 Đã lưu vào github_accounts.txt`, 'info');
                    successCount++;
                } else {
                    this.log(`   ❌ GitHub thất bại: ${email}`, 'error');
                    failedCount++;
                }

            } catch (error) {
                this.log(`   ❌ Lỗi: ${error.message}`, 'error');
                failedCount++;
            }

            this.sendResult({ email, status: 'github_signup' });
        }

        const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
        this.sendComplete({ total, loggedIn: successCount, failed: failedCount, skipped: 0, totalTime });
        this.isRunning = false;
    }

    // Resolve manual wait for github signup
    githubSignupDone(email, status) {
        if (this._ghResolves && this._ghResolves.has(email)) {
            this._ghResolves.get(email)(status);
            this._ghResolves.delete(email);
        }
    }

    // GitHub helper: fill a field
    async _ghFillField(page, selectors, value) {
        const sels = selectors.split(',').map(s => s.trim());
        for (const sel of sels) {
            try {
                const el = await page.$(sel);
                if (!el) continue;
                const isVisible = await page.evaluate(e => {
                    const s = window.getComputedStyle(e);
                    return s.display !== 'none' && s.visibility !== 'hidden' && e.offsetWidth > 0;
                }, el);
                if (!isVisible) continue;

                await page.evaluate(e => e.scrollIntoView({ block: 'center' }), el);
                await this.delay(200);
                await el.click();
                await this.delay(150);
                await page.evaluate(e => { e.value = ''; }, el);
                await el.click({ clickCount: 3 });
                await page.keyboard.press('Backspace');
                await this.delay(100);
                await el.type(value, { delay: 50 });
                await page.evaluate(e => {
                    e.dispatchEvent(new Event('input', { bubbles: true }));
                    e.dispatchEvent(new Event('change', { bubbles: true }));
                    e.dispatchEvent(new Event('blur', { bubbles: true }));
                }, el);
                this.log(`   ✅ Filled: ${sel.split(',')[0]}`, 'info');
                return true;
            } catch (e) { continue; }
        }
        return false;
    }

    // GitHub helper: click Continue (not Google/Apple)
    async _ghClickContinue(page) {
        await page.evaluate(() => {
            const stepBtns = document.querySelectorAll('button[data-continue-to]');
            for (const btn of stepBtns) {
                if (btn.offsetParent !== null && btn.offsetWidth > 0) { btn.click(); return; }
            }
            const buttons = Array.from(document.querySelectorAll('button'));
            for (const btn of buttons) {
                const text = btn.textContent.trim().toLowerCase();
                if (text.includes('google') || text.includes('apple') || text.includes('create')) continue;
                if (text === 'continue' || text === 'next') {
                    if (btn.offsetParent !== null && btn.offsetWidth > 0) { btn.click(); return; }
                }
            }
        });
    }

    // GitHub helper: handle email preferences
    async _ghHandleEmailPref(page) {
        try {
            const pref = await page.$('#opt_in');
            if (pref) {
                const isChecked = await page.evaluate(el => el.checked, pref);
                if (isChecked) await pref.click();
            }
        } catch (e) {}
    }

    // GitHub helper: click Create account
    async _ghClickCreate(page) {
        await page.evaluate(() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            for (const btn of buttons) {
                const text = btn.textContent.trim().toLowerCase();
                if (text === 'create account' || text === 'create your account') {
                    if (btn.offsetParent !== null && btn.offsetWidth > 0) { btn.click(); return true; }
                }
            }
            const submits = Array.from(document.querySelectorAll('button[type="submit"]'));
            for (const btn of submits) {
                const text = btn.textContent.trim().toLowerCase();
                if (text.includes('google') || text.includes('apple')) continue;
                if (btn.offsetParent !== null && btn.offsetWidth > 0) { btn.click(); return true; }
            }
            return false;
        });
    }
}

// ======================== RANDOM GENERATORS ========================
function generateRandomUsername(email) {
    const base = email.split('@')[0].replace(/[^a-zA-Z0-9]/g, '');
    const suffix = Math.random().toString(36).substring(2, 8);
    return (base.substring(0, 12) + '-' + suffix).substring(0, 39);
}

function generateRandomPassword(length = 14) {
    const upper = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
    const lower = 'abcdefghjkmnpqrstuvwxyz';
    const digits = '23456789';
    const symbols = '!@#$%&*?';
    const all = upper + lower + digits + symbols;
    // Ensure at least one of each type
    let pass = '';
    pass += upper[Math.floor(Math.random() * upper.length)];
    pass += lower[Math.floor(Math.random() * lower.length)];
    pass += digits[Math.floor(Math.random() * digits.length)];
    pass += symbols[Math.floor(Math.random() * symbols.length)];
    for (let i = pass.length; i < length; i++) {
        pass += all[Math.floor(Math.random() * all.length)];
    }
    // Shuffle
    return pass.split('').sort(() => Math.random() - 0.5).join('');
}

module.exports = { ProfileWorker, detectAllBrowsers, CONFIG, LOCAL_BROWSER_DIR, generateRandomUsername, generateRandomPassword };
