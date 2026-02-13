/**
 * GG Profile Saver (GemLogin) - Worker
 * Login Google accounts qua GemLogin profile, lưu sub-profile cho mỗi acc
 * 
 * Flow: GemLogin API start profile → CDP endpoint → puppeteer-core connect → login
 */
const fs = require('fs');
const path = require('path');
const os = require('os');
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
    GEMLOGIN_PROFILES_BASE: path.join(os.homedir(), '.gemlogin', 'profile', 'profiles'),
    OLD_DB_FILE: path.join(__dirname, '..', 'gg-profile-saver', 'profiles_db.json'),
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
        // Get list of sub-profiles already assigned in DB for current GemLogin profile
        const usedNames = new Set();
        for (const entry of Object.values(db)) {
            if (String(entry.gemloginProfileId) === String(this.gemloginProfileId)) {
                usedNames.add(entry.profileDir);
            }
        }

        // Read Local State to get available sub-profile names
        const profilePath = path.join(CONFIG.GEMLOGIN_PROFILES_BASE, String(this.gemloginProfileId));
        const localStatePath = path.join(profilePath, 'Local State');
        const allNames = [];
        if (fs.existsSync(localStatePath)) {
            try {
                const localState = JSON.parse(fs.readFileSync(localStatePath, 'utf8'));
                const infoCache = localState?.profile?.info_cache || {};
                for (const info of Object.values(infoCache)) {
                    if (info.name) allNames.push(info.name);
                }
            } catch {}
        }

        // Sort by number suffix
        allNames.sort((a, b) => {
            const na = parseInt((a.match(/(\d+)$/) || [0, 0])[1]);
            const nb = parseInt((b.match(/(\d+)$/) || [0, 0])[1]);
            return na - nb;
        });

        // Return first unused sub-profile name
        for (const name of allNames) {
            if (!usedNames.has(name)) return name;
        }

        // All used — return next number
        return null;
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
        let data;
        try {
            data = await startGemLoginProfile(this.gemloginProfileId);
        } catch (err) {
            // Profile might be already running → close and retry
            if (err.message.includes('not ready') || err.message.includes('status')) {
                this.log('   ⚠️ Profile đang chạy, đóng và mở lại...', 'warning');
                await closeGemLoginProfile(this.gemloginProfileId);
                await this.delay(2000);
                data = await startGemLoginProfile(this.gemloginProfileId);
            } else {
                throw err;
            }
        }

        const debugAddress = data.remote_debugging_address; // "127.0.0.1:PORT"
        this.debugAddress = debugAddress; // cache for later use
        const wsUrl = await this.getWsEndpoint(debugAddress);
        const browser = await puppeteer.connect({
            browserWSEndpoint: wsUrl,
            defaultViewport: null,
        });

        return browser;
    }

    /**
     * Click a sub-profile in the GemLogin profile picker via CDP mouse click.
     * GemLogin starts Chrome at chrome://profile-picker/ with sub-profiles (github1, github2, ...).
     * Synthetic JS clicks don't work — must use real mouse coordinates.
     * After clicking, Chrome opens a NEW window under that sub-profile.
     * Returns the new page in the sub-profile window.
     */
    async clickSubProfile(browser, subProfileName) {
        const pages = await browser.pages();
        const pickerPage = pages.find(p => p.url().includes('profile-picker'));
        if (!pickerPage) {
            throw new Error('Không tìm thấy profile picker');
        }

        // Find the card index matching subProfileName via aria-label
        const cardInfo = await pickerPage.evaluate((targetName) => {
            const app = document.querySelector('profile-picker-app');
            if (!app?.shadowRoot) return { error: 'no app shadowRoot' };
            const mainView = app.shadowRoot.querySelector('profile-picker-main-view');
            if (!mainView?.shadowRoot) return { error: 'no mainView shadowRoot' };
            const cards = mainView.shadowRoot.querySelectorAll('profile-card');

            for (let i = 0; i < cards.length; i++) {
                const sr = cards[i].shadowRoot;
                if (!sr) continue;
                const btn = sr.querySelector('#profileCardButton');
                if (!btn) continue;
                const label = btn.getAttribute('aria-label') || '';
                // "Open github2 profile"
                if (label.includes(targetName)) {
                    const rect = btn.getBoundingClientRect();
                    return { index: i, label, x: rect.x + rect.width / 2, y: rect.y + rect.height / 2, found: true };
                }
            }

            // Fallback: return all labels for debugging
            const allLabels = [];
            for (const card of cards) {
                const sr = card.shadowRoot;
                if (!sr) continue;
                const btn = sr.querySelector('#profileCardButton');
                allLabels.push(btn?.getAttribute('aria-label') || '?');
            }
            return { error: `Không tìm thấy "${targetName}"`, allLabels };
        }, subProfileName);

        if (!cardInfo.found) {
            // Card might be off-screen, scroll to it
            const scrollResult = await pickerPage.evaluate((targetName) => {
                const app = document.querySelector('profile-picker-app');
                if (!app?.shadowRoot) return { error: 'no app' };
                const mainView = app.shadowRoot.querySelector('profile-picker-main-view');
                if (!mainView?.shadowRoot) return { error: 'no mainView' };
                const cards = mainView.shadowRoot.querySelectorAll('profile-card');

                for (let i = 0; i < cards.length; i++) {
                    const sr = cards[i].shadowRoot;
                    if (!sr) continue;
                    const btn = sr.querySelector('#profileCardButton');
                    if (!btn) continue;
                    const label = btn.getAttribute('aria-label') || '';
                    if (label.includes(targetName)) {
                        cards[i].scrollIntoView({ block: 'center' });
                        return { scrolled: true, index: i };
                    }
                }
                return { error: 'not found after scroll' };
            }, subProfileName);

            if (scrollResult.error) {
                throw new Error(cardInfo.error || `Sub-profile "${subProfileName}" không tìm thấy`);
            }

            await this.delay(500);

            // Re-get coordinates after scroll
            const retryInfo = await pickerPage.evaluate((targetName) => {
                const app = document.querySelector('profile-picker-app');
                const mainView = app.shadowRoot.querySelector('profile-picker-main-view');
                const cards = mainView.shadowRoot.querySelectorAll('profile-card');
                for (const card of cards) {
                    const sr = card.shadowRoot;
                    if (!sr) continue;
                    const btn = sr.querySelector('#profileCardButton');
                    if (!btn) continue;
                    if ((btn.getAttribute('aria-label') || '').includes(targetName)) {
                        const rect = btn.getBoundingClientRect();
                        return { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2, found: true };
                    }
                }
                return { found: false };
            }, subProfileName);

            if (!retryInfo.found) {
                throw new Error(`Sub-profile "${subProfileName}" không tìm thấy sau khi scroll`);
            }

            // Click with real mouse
            await pickerPage.mouse.click(retryInfo.x, retryInfo.y);
        } else {
            // Click with real mouse at the card center
            await pickerPage.mouse.click(cardInfo.x, cardInfo.y);
        }

        this.log(`   🖱️ Đã click sub-profile: ${subProfileName}`, 'info');

        // Wait for new window/target to appear
        const newTarget = await browser.waitForTarget(
            t => t.type() === 'page' && !t.url().includes('profile-picker') && t.url() !== 'about:blank',
            { timeout: 15000 }
        ).catch(() => null);

        if (newTarget) {
            const newPage = await newTarget.page();
            return newPage;
        }

        // Fallback: check for new pages
        await this.delay(3000);
        const allPages = await browser.pages();
        const nonPickerPages = allPages.filter(p => !p.url().includes('profile-picker'));
        if (nonPickerPages.length > 0) {
            return nonPickerPages[nonPickerPages.length - 1];
        }

        // Last fallback: new tab on about:blank means sub-profile opened
        const blankPages = allPages.filter(p => p.url() === 'about:blank' || p.url().startsWith('chrome://newtab'));
        if (blankPages.length > 0) {
            return blankPages[blankPages.length - 1];
        }

        throw new Error('Sub-profile window không mở được sau khi click');
    }

    /**
     * Connect to GemLogin and select a specific sub-profile.
     * Returns { browser, page } where page is inside the sub-profile.
     */
    async connectToSubProfile(subProfileName) {
        const browser = await this.connectToGemLogin();
        this.log(`   📋 Chọn sub-profile: ${subProfileName}...`, 'info');
        const page = await this.clickSubProfile(browser, subProfileName);
        return { browser, page };
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

        // Assign sub-profiles to accounts
        const needLogin = [];
        for (const acc of uniqueAccounts) {
            db = this.loadDB();
            if (db[acc.email]) {
                acc.profileDir = db[acc.email].profileDir;
            } else {
                const nextProfile = this.getNextProfileNum(db);
                if (!nextProfile) {
                    this.log(`❌ Hết sub-profile trống cho ${acc.email}!`, 'error');
                    continue;
                }
                acc.profileDir = nextProfile;
                db[acc.email] = { profileDir: acc.profileDir, gemloginProfileId: this.gemloginProfileId, status: 'pending', reason: '', lastLogin: '' };
                this.saveDB(db);
            }
            needLogin.push(acc);
        }

        const totalWork = needLogin.length;
        this.log(`🚀 Bắt đầu login ${totalWork} accounts qua GemLogin (Profile ID: ${this.gemloginProfileId})...`, 'info');

        let loggedIn = 0, failed = 0;

        // Login tuần tự: mỗi account = start GemLogin → click sub-profile → login → close
        for (let i = 0; i < needLogin.length && this.isRunning; i++) {
            const acc = needLogin[i];
            if (!acc.password) { failed++; continue; }

            const result = await this.loginInSubProfile(acc.email, acc.password, acc.profileDir, i, totalWork);
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

            // Close GemLogin profile between accounts
            await closeGemLoginProfile(this.gemloginProfileId);
            if (this.isRunning && i < needLogin.length - 1) await this.delay(CONFIG.DELAY_BETWEEN);
        }

        const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
        this.sendComplete({ total: totalWork, loggedIn, failed, skipped: 0, totalTime });
        this.isRunning = false;
    }

    /**
     * Login 1 account trong 1 GemLogin sub-profile.
     * Flow: start GemLogin → click sub-profile card → login Google trong window mới
     */
    async loginInSubProfile(email, password, profileDir, index, total) {
        if (!this.isRunning) return null;

        const startTime = Date.now();
        this.log(`[${index + 1}/${total}] 🚀 ${email} → ${profileDir}`, 'info');
        this.sendProgress(index, total, `${index + 1}/${total}: ${email}`);

        let browser, page;
        try {
            ({ browser, page } = await this.connectToSubProfile(profileDir));
        } catch (err) {
            this.log(`   ❌ Không kết nối sub-profile: ${err.message}`, 'error');
            return { email, password, profileDir, status: 'error', reason: 'GEMLOGIN_ERROR', time: 0 };
        }

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
    getProfiles(gemloginProfileId) {
        const db = this.loadDB();

        if (!gemloginProfileId) {
            return Object.entries(db).map(([email, entry]) => ({ email, ...entry }));
        }

        const profilePath = path.join(CONFIG.GEMLOGIN_PROFILES_BASE, String(gemloginProfileId));

        // Read Local State to get GemLogin sub-profile display names
        const nameMap = {}; // "Default" -> "github1", "Profile 1" -> "github2", etc.
        const localStatePath = path.join(profilePath, 'Local State');
        if (fs.existsSync(localStatePath)) {
            try {
                const localState = JSON.parse(fs.readFileSync(localStatePath, 'utf8'));
                const infoCache = localState?.profile?.info_cache || {};
                for (const [dirName, info] of Object.entries(infoCache)) {
                    if (info.name) nameMap[dirName] = info.name;
                }
            } catch {}
        }

        // Scan disk for sub-profile directories
        let diskDirs = [];
        if (fs.existsSync(profilePath)) {
            diskDirs = fs.readdirSync(profilePath, { withFileTypes: true })
                .filter(d => d.isDirectory() && /^(Default|Profile \d+)$/.test(d.name))
                .map(d => d.name);
        }

        // Load old DB for email recovery
        let oldDB = {};
        if (fs.existsSync(CONFIG.OLD_DB_FILE)) {
            try { oldDB = JSON.parse(fs.readFileSync(CONFIG.OLD_DB_FILE, 'utf8')); } catch {}
        }
        // Old DB reverse map: "Profile_1" -> { email, status, ... }
        const oldDirToEmail = {};
        for (const [email, entry] of Object.entries(oldDB)) {
            oldDirToEmail[entry.profileDir] = { email, ...entry };
        }

        // New DB: collect entries already mapped to this GemLogin profile
        const dbByDir = {};
        for (const [email, entry] of Object.entries(db)) {
            if (String(entry.gemloginProfileId) === String(gemloginProfileId)) {
                dbByDir[entry.profileDir] = { email, ...entry };
            }
        }

        const results = [];
        const seenDirs = new Set();
        let imported = 0;

        for (const dirName of diskDirs) {
            if (seenDirs.has(dirName)) continue;
            seenDirs.add(dirName);

            const displayName = nameMap[dirName] || dirName;

            // Check new DB first (by dir name or display name)
            const dbEntry = dbByDir[dirName] || dbByDir[displayName];
            if (dbEntry) {
                results.push({ ...dbEntry, profileDir: displayName });
                continue;
            }

            // Try old DB: "Profile 1" -> "Profile_1"
            const oldDBKey = dirName.replace(/ /g, '_');
            const oldEntry = oldDirToEmail[oldDBKey] || oldDirToEmail[dirName];

            if (oldEntry) {
                // Import from old DB into new DB
                db[oldEntry.email] = {
                    profileDir: displayName,
                    gemloginProfileId: gemloginProfileId,
                    status: oldEntry.status || 'unknown',
                    reason: oldEntry.reason || '',
                    lastLogin: oldEntry.lastLogin || '',
                };
                results.push({
                    email: oldEntry.email,
                    profileDir: displayName,
                    gemloginProfileId: gemloginProfileId,
                    status: oldEntry.status || 'unknown',
                    reason: oldEntry.reason || '',
                    lastLogin: oldEntry.lastLogin || '',
                });
                imported++;
            } else {
                // Unknown - no email info
                results.push({
                    email: '',
                    profileDir: displayName,
                    gemloginProfileId: gemloginProfileId,
                    status: 'unknown',
                    reason: '',
                    lastLogin: '',
                });
            }
        }

        if (imported > 0) {
            this.saveDB(db);
        }

        // Sort by number extracted from display name (github1, github2, ...)
        results.sort((a, b) => {
            const numA = parseInt((a.profileDir.match(/(\d+)$/) || [0, 0])[1]);
            const numB = parseInt((b.profileDir.match(/(\d+)$/) || [0, 0])[1]);
            return numA - numB;
        });

        return results;
    }

    async openProfile(profileDir) {
        this.log(`📂 Mở GemLogin sub-profile (${profileDir})...`, 'info');

        try {
            const { browser, page } = await this.connectToSubProfile(profileDir);
            await page.goto('https://myaccount.google.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
            this.log(`✅ Browser đã mở cho ${profileDir}`, 'success');
            browser.disconnect(); // disconnect puppeteer, keep browser open
            return { success: true };
        } catch (e) {
            this.log(`❌ Không mở được: ${e.message}`, 'error');
            return { success: false, reason: e.message };
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
