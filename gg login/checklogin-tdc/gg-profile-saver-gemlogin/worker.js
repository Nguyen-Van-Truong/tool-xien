/**
 * GG Profile Saver (GemLogin) - Worker
 * Login Google accounts qua GemLogin profile, lưu sub-profile cho mỗi acc
 * 
 * Flow: GemLogin API start profile → CDP endpoint → puppeteer-core connect → login
 */
const fs = require('fs');
const path = require('path');
const http = require('http');
const { execSync } = require('child_process');
const puppeteer = require('puppeteer-core');

// ======================== CONFIG ========================
const CONFIG = {
    GEMLOGIN_API: 'http://localhost:1010',
    DB_FILE: path.join(__dirname, 'profiles_db.json'),
    ACCOUNTS_FILE: path.join(__dirname, 'accounts.txt'),
    BACKUP_DIR: path.join(__dirname, 'backups'),
    LOGIN_URL: 'https://accounts.google.com/signin',
    CHECK_URL: 'https://myaccount.google.com/?utm_source=sign_in_no_continue&pli=1',
    DELAY_BETWEEN: 2000,
};

// ======================== GemLogin API ========================
function gemloginRequest(endpoint) {
    return new Promise((resolve, reject) => {
        const url = new URL(endpoint, CONFIG.GEMLOGIN_API);
        http.get(url.href, { timeout: 30000 }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try { resolve(JSON.parse(data)); }
                catch (e) { reject(new Error('Invalid JSON from GemLogin API')); }
            });
        }).on('error', (err) => reject(err))
          .on('timeout', function() { this.destroy(); reject(new Error('GemLogin API timeout')); });
    });
}

async function checkGemLoginRunning() {
    try {
        const result = await gemloginRequest('/api/profiles');
        return result.success === true;
    } catch {
        return false;
    }
}

async function getGemLoginProfiles() {
    const result = await gemloginRequest('/api/profiles');
    if (!result.success) throw new Error('Failed to get GemLogin profiles');
    return result.data || [];
}

async function startGemLoginProfile(profileId) {
    const result = await gemloginRequest(`/api/profiles/start/${profileId}`);
    if (!result.success || !result.data?.success) {
        throw new Error(result.message || 'Failed to start GemLogin profile');
    }
    return result.data; // { remote_debugging_address, browser_location, ... }
}

async function closeGemLoginProfile(profileId) {
    try {
        await gemloginRequest(`/api/profiles/close/${profileId}`);
    } catch {}
}

// ======================== ProfileWorker CLASS ========================
class ProfileWorker {
    constructor(mainWindow, options = {}) {
        this.mainWindow = mainWindow;
        this.isRunning = false;
        this.openBrowsers = new Map();
        this.gemloginProfileId = options.gemloginProfileId || null;
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
            const match = db[key].profileDir.match(/^tdc(\d+)$/);
            if (match) {
                const num = parseInt(match[1]);
                if (num > max) max = num;
            }
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

    // ---- Browser via GemLogin ----
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

    async connectToGemLogin() {
        // Start GemLogin profile → get CDP address → puppeteer connect
        const data = await startGemLoginProfile(this.gemloginProfileId);
        const debugAddress = data.remote_debugging_address; // "127.0.0.1:PORT"

        // Get WebSocket URL from CDP
        const wsUrl = await this.getWsEndpoint(debugAddress);
        const browser = await puppeteer.connect({
            browserWSEndpoint: wsUrl,
            defaultViewport: null,
        });

        return browser;
    }

    async getWsEndpoint(debugAddress) {
        return new Promise((resolve, reject) => {
            http.get(`http://${debugAddress}/json/version`, { timeout: 10000 }, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    try {
                        const json = JSON.parse(data);
                        resolve(json.webSocketDebuggerUrl);
                    } catch (e) {
                        reject(new Error('Failed to get WebSocket URL'));
                    }
                });
            }).on('error', reject)
              .on('timeout', function() { this.destroy(); reject(new Error('CDP timeout')); });
        });
    }

    // ---- Login Flow ----
    async loginAccount(email, password, profileDir, index, total) {
        if (!this.isRunning) return null;

        const startTime = Date.now();
        this.log(`[${index + 1}/${total}] 🚀 ${email} → ${profileDir}`, 'info');
        this.sendProgress(index, total, `${index + 1}/${total}: ${email}`);

        let browser;
        try {
            browser = await this.connectToGemLogin();
        } catch (err) {
            this.log(`   ❌ Không kết nối được GemLogin: ${err.message}`, 'error');
            return { email, password, profileDir, status: 'error', reason: 'GEMLOGIN_ERROR', time: 0 };
        }

        this.openBrowsers.set(profileDir, browser);

        // Mở tab mới, chuyển đến sub-profile URL
        const page = await browser.newPage();
        await page.setUserAgent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
        );

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
                await page.close();
                return result;
            }

            if (afterEmailContent.includes("Couldn't find") || afterEmailContent.includes('Không tìm thấy')) {
                this.log(`   ❌ Email không tồn tại!`, 'error');
                result.status = 'email_error'; result.reason = 'EMAIL_NOT_FOUND';
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
                await page.close();
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

                try {
                    await page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 15000 });
                } catch (navErr) {}
                await this.delay(3000);
            } catch (passError) {
                this.log(`   ⚠️ Không thấy trang password (CAPTCHA?)`, 'warning');
                result.status = 'error'; result.reason = 'NO_PASSWORD_PAGE';
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
                await page.close();
                return result;
            }

            // Step 4: Check kết quả
            let finalContent = '';
            let finalUrl = '';
            try {
                finalUrl = page.url();
                finalContent = await page.content();
            } catch (ctxError) {
                this.log(`   ⏳ Trang đang chuyển...`, 'info');
                await this.delay(3000);
                try {
                    finalUrl = page.url();
                    finalContent = await page.content();
                } catch (e2) {
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
                await page.close();
                return result;
            }

            // Challenge/dp - đã có SĐT
            if (finalUrl.includes('challenge/dp') ||
                finalContent.includes('Open the Gmail app') ||
                finalContent.includes('Google sent a notification') ||
                finalContent.includes('Mở ứng dụng Gmail') ||
                finalContent.includes('Google đã gửi thông báo')) {
                result.status = 'has_phone'; result.reason = 'HAS_PHONE_VERIFY';
                this.log(`   📱 Đã có SĐT - cần xác minh qua điện thoại`, 'warning');
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
                await page.close();
                return result;
            }

            // Challenge/iap - chưa có SĐT
            if (finalUrl.includes('challenge/iap') ||
                finalContent.includes('Enter a phone number') ||
                finalContent.includes('Nhập số điện thoại') ||
                finalContent.includes('get a text message') ||
                finalContent.includes('nhận tin nhắn')) {
                result.status = 'need_phone'; result.reason = 'NEED_PHONE_VERIFY';
                this.log(`   📵 Chưa có SĐT - cần nhập số điện thoại`, 'warning');
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
                await page.close();
                return result;
            }

            // Các challenge khác
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
                await page.close();
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
                        await page.close();
                        return result;
                    }
                }
            }

            // Step 6: Verify session
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

        // Đóng tab (không đóng browser GemLogin)
        if (result.status !== 'logged_in') {
            try { await page.close(); } catch (e) {}
        }

        this.sendResult(result);
        this.log(`   ⏱️ ${result.status} - ${result.reason} (${result.time}s)`, result.status === 'logged_in' ? 'success' : 'warning');
        return result;
    }

    // ---- Check session ----
    async checkSession(email, profileDir, index, total) {
        if (!this.isRunning) return null;

        const startTime = Date.now();
        this.log(`[${index + 1}/${total}] 🔍 Kiểm tra session ${email}`, 'info');
        this.sendProgress(index, total, `${index + 1}/${total}: ${email} (check session)`);

        let browser;
        try {
            browser = this.openBrowsers.values().next().value;
            if (!browser || !browser.isConnected()) {
                browser = await this.connectToGemLogin();
            }
        } catch (err) {
            this.log(`   ❌ Không kết nối GemLogin: ${err.message}`, 'error');
            return { email, profileDir, status: 'error', reason: 'GEMLOGIN_ERROR', time: 0 };
        }

        const page = await browser.newPage();
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
        try { await page.close(); } catch (e) {}

        this.sendResult(result);
        return result;
    }

    // ---- Login All ----
    async startLoginAll(accounts) {
        this.isRunning = true;

        // Check GemLogin đang chạy
        const running = await checkGemLoginRunning();
        if (!running) {
            this.log('❌ GemLogin chưa mở! Hãy mở GemLogin trước.', 'error');
            this.sendComplete({ total: 0, loggedIn: 0, failed: 0, skipped: 0, totalTime: 0 });
            this.isRunning = false;
            return;
        }

        let db = this.loadDB();
        const startTime = Date.now();

        // Deduplicate
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

        // Chia nhóm
        const needLogin = [];
        for (const acc of uniqueAccounts) {
            db = this.loadDB();
            if (db[acc.email]) {
                acc.profileDir = db[acc.email].profileDir;
            } else {
                const num = this.getNextProfileNum(db);
                acc.profileDir = `tdc${num}`;
                db[acc.email] = { profileDir: acc.profileDir, gemloginProfileId: this.gemloginProfileId, status: 'pending', reason: '', lastLogin: '' };
                this.saveDB(db);
            }
            needLogin.push(acc);
        }

        const totalWork = needLogin.length;
        this.log(`🚀 Bắt đầu login ${totalWork} accounts qua GemLogin (Profile ID: ${this.gemloginProfileId})...`, 'info');

        // Start GemLogin profile 1 lần, dùng chung browser
        let browser;
        try {
            browser = await this.connectToGemLogin();
            this.log('✅ Đã kết nối GemLogin browser', 'success');
        } catch (err) {
            this.log(`❌ Không kết nối GemLogin: ${err.message}`, 'error');
            this.sendComplete({ total: totalWork, loggedIn: 0, failed: totalWork, skipped: 0, totalTime: 0 });
            this.isRunning = false;
            return;
        }

        let loggedIn = 0, failed = 0;

        // Login tuần tự (dùng chung 1 browser GemLogin, mỗi acc = 1 tab)
        for (let i = 0; i < needLogin.length && this.isRunning; i++) {
            const acc = needLogin[i];
            if (!acc.password) { failed++; continue; }

            // Mở tab mới cho mỗi account
            const result = await this.loginAccountInTab(browser, acc.email, acc.password, acc.profileDir, i, totalWork);
            if (!result) continue;

            db = this.loadDB();
            db[acc.email] = {
                profileDir: acc.profileDir,
                gemloginProfileId: this.gemloginProfileId,
                status: result.status,
                reason: result.reason,
                lastLogin: new Date().toISOString(),
            };
            this.saveDB(db);
            this.sendProfilesUpdate();

            if (result.status === 'logged_in') loggedIn++;
            else failed++;

            if (this.isRunning && i < needLogin.length - 1) await this.delay(CONFIG.DELAY_BETWEEN);
        }

        const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
        this.sendComplete({ total: totalWork, loggedIn, failed, skipped: 0, totalTime });
        this.isRunning = false;
    }

    // Login 1 account trong 1 tab mới (dùng chung browser GemLogin)
    async loginAccountInTab(browser, email, password, profileDir, index, total) {
        if (!this.isRunning) return null;

        const startTime = Date.now();
        this.log(`[${index + 1}/${total}] 🚀 ${email} → ${profileDir}`, 'info');
        this.sendProgress(index, total, `${index + 1}/${total}: ${email}`);

        const page = await browser.newPage();

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
                await page.close();
                return result;
            }

            if (afterEmailContent.includes("Couldn't find") || afterEmailContent.includes('Không tìm thấy')) {
                this.log(`   ❌ Email không tồn tại!`, 'error');
                result.status = 'email_error'; result.reason = 'EMAIL_NOT_FOUND';
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
                await page.close();
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

                try {
                    await page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 15000 });
                } catch (navErr) {}
                await this.delay(3000);
            } catch (passError) {
                this.log(`   ⚠️ Không thấy trang password (CAPTCHA?)`, 'warning');
                result.status = 'error'; result.reason = 'NO_PASSWORD_PAGE';
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
                await page.close();
                return result;
            }

            // Step 4: Check kết quả
            let finalContent = '';
            let finalUrl = '';
            try {
                finalUrl = page.url();
                finalContent = await page.content();
            } catch (ctxError) {
                this.log(`   ⏳ Trang đang chuyển...`, 'info');
                await this.delay(3000);
                try {
                    finalUrl = page.url();
                    finalContent = await page.content();
                } catch (e2) {
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
                await page.close();
                return result;
            }

            // Challenge/dp
            if (finalUrl.includes('challenge/dp') ||
                finalContent.includes('Open the Gmail app') ||
                finalContent.includes('Google sent a notification') ||
                finalContent.includes('Mở ứng dụng Gmail') ||
                finalContent.includes('Google đã gửi thông báo')) {
                result.status = 'has_phone'; result.reason = 'HAS_PHONE_VERIFY';
                this.log(`   📱 Đã có SĐT - cần xác minh`, 'warning');
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
                await page.close();
                return result;
            }

            // Challenge/iap
            if (finalUrl.includes('challenge/iap') ||
                finalContent.includes('Enter a phone number') ||
                finalContent.includes('Nhập số điện thoại') ||
                finalContent.includes('get a text message') ||
                finalContent.includes('nhận tin nhắn')) {
                result.status = 'need_phone'; result.reason = 'NEED_PHONE_VERIFY';
                this.log(`   📵 Chưa có SĐT - cần nhập SĐT`, 'warning');
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
                await page.close();
                return result;
            }

            // Các challenge khác
            if (finalUrl.includes('challenge/') || finalUrl.includes('signin/rejected') ||
                finalContent.includes('Verify it') || finalContent.includes('Verify your identity') ||
                finalContent.includes('verification code') ||
                finalContent.includes('mã xác minh') || finalContent.includes('Xác minh danh tính')) {
                const pageText = await page.evaluate(() => document.body.innerText).catch(() => '');
                if (pageText.includes('Open the Gmail app') || pageText.includes('notification') ||
                    pageText.includes('Mở ứng dụng Gmail')) {
                    result.status = 'has_phone'; result.reason = 'HAS_PHONE_VERIFY';
                    this.log(`   📱 Đã có SĐT`, 'warning');
                } else if (pageText.includes('phone number') || pageText.includes('số điện thoại')) {
                    result.status = 'need_phone'; result.reason = 'NEED_PHONE_VERIFY';
                    this.log(`   📵 Chưa có SĐT`, 'warning');
                } else {
                    result.status = 'has_phone'; result.reason = 'UNKNOWN_CHALLENGE';
                    this.log(`   📱 Challenge không xác định`, 'warning');
                }
                result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                this.sendResult(result);
                await page.close();
                return result;
            }

            // Step 5: Speedbump
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
                    result.status = 'logged_in'; result.reason = 'SPEEDBUMP_ACCEPTED';
                    this.log(`   ✅ Speedbump OK!`, 'success');
                } else if (finalUrl.includes('myaccount.google.com') ||
                           finalUrl.includes('google.com/search') ||
                           !finalUrl.includes('accounts.google.com')) {
                    result.status = 'logged_in'; result.reason = 'LOGIN_OK';
                    this.log(`   ✅ Login thành công!`, 'success');
                } else {
                    await this.delay(3000);
                    const retryUrl = page.url();
                    if (!retryUrl.includes('accounts.google.com')) {
                        result.status = 'logged_in'; result.reason = 'LOGIN_OK';
                        this.log(`   ✅ Login thành công!`, 'success');
                    } else {
                        this.log(`   ⚠️ Kẹt ở trang login`, 'warning');
                        result.status = 'error'; result.reason = 'STUCK_AT_LOGIN';
                        result.time = ((Date.now() - startTime) / 1000).toFixed(1);
                        this.sendResult(result);
                        await page.close();
                        return result;
                    }
                }
            }

            // Step 6: Verify session
            if (result.status === 'logged_in') {
                this.log(`   🔍 Kiểm tra session...`, 'info');
                try {
                    await page.goto(CONFIG.CHECK_URL, { waitUntil: 'domcontentloaded', timeout: 15000 });
                    await this.delay(3000);
                    const emailOnPage = await page.evaluate(() => {
                        const el = document.querySelector('.fwyMNe');
                        return el ? el.textContent.trim() : '';
                    });
                    if (emailOnPage) {
                        this.log(`   ✅ Session OK! (${emailOnPage})`, 'success');
                    } else {
                        this.log(`   ✅ Session OK!`, 'success');
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

        // Đóng tab nếu failed
        if (result.status !== 'logged_in') {
            try { await page.close(); } catch (e) {}
        }

        this.sendResult(result);
        this.log(`   ⏱️ ${result.status} - ${result.reason} (${result.time}s)`, result.status === 'logged_in' ? 'success' : 'warning');
        return result;
    }

    // ---- Import ----
    importAccounts() {
        const importSources = [
            { name: 'tdc-login-tool/passed.txt', path: path.join(__dirname, '..', 'tdc-login-tool', 'passed.txt') },
            { name: 'tdc-login-tool/has_phone.txt', path: path.join(__dirname, '..', 'tdc-login-tool', 'has_phone.txt') },
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
        return Object.entries(db).map(([email, entry]) => ({ email, ...entry }));
    }

    async openProfile(email) {
        const db = this.loadDB();
        if (!db[email]) return { success: false, reason: 'NOT_FOUND' };

        this.log(`📂 Mở GemLogin profile (${email})...`, 'info');

        try {
            const browser = await this.connectToGemLogin();
            const page = await browser.newPage();
            await page.goto('https://myaccount.google.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
            this.log(`✅ Browser đã mở cho ${email}`, 'success');
            return { success: true };
        } catch (e) {
            this.log(`❌ Không mở được: ${e.message}`, 'error');
            return { success: false, reason: 'GEMLOGIN_ERROR' };
        }
    }

    async openAllProfiles() {
        const running = await checkGemLoginRunning();
        if (!running) {
            this.log('❌ GemLogin chưa mở!', 'error');
            return { success: false, reason: 'GEMLOGIN_NOT_RUNNING', count: 0 };
        }

        const db = this.loadDB();
        const loggedIn = Object.entries(db).filter(([_, v]) => v.status === 'logged_in');
        if (loggedIn.length === 0) return { success: false, reason: 'NO_PROFILES', count: 0 };

        this.log(`🚀 Mở GemLogin browser...`, 'info');
        try {
            const browser = await this.connectToGemLogin();
            const page = await browser.newPage();
            await page.goto('https://myaccount.google.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
            this.log(`✅ Browser đã mở (${loggedIn.length} accounts đã login)`, 'success');
            return { success: true, count: loggedIn.length };
        } catch (e) {
            this.log(`❌ Lỗi: ${e.message}`, 'error');
            return { success: false, reason: 'GEMLOGIN_ERROR', count: 0 };
        }
    }

    cleanProfiles() {
        const db = this.loadDB();
        const entries = Object.entries(db);
        const toDelete = entries.filter(([_, v]) => v.status !== 'logged_in');

        if (toDelete.length === 0) return { deleted: 0, kept: entries.length };

        for (const [email, entry] of toDelete) {
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
        this.log('✖ Đóng GemLogin profile...', 'warning');
        if (this.gemloginProfileId) {
            await closeGemLoginProfile(this.gemloginProfileId);
        }
        this.openBrowsers = new Map();
        this.log('✅ Đã đóng GemLogin browser', 'success');
        return 1;
    }

    // ---- Accounts file ----
    readAccountsFile() {
        if (!fs.existsSync(CONFIG.ACCOUNTS_FILE)) return '';
        return fs.readFileSync(CONFIG.ACCOUNTS_FILE, 'utf8');
    }

    saveAccountsFile(content) {
        fs.writeFileSync(CONFIG.ACCOUNTS_FILE, content, 'utf8');
    }
}

module.exports = { ProfileWorker, checkGemLoginRunning, getGemLoginProfiles, CONFIG };
