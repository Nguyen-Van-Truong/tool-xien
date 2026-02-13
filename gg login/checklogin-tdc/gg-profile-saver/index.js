/**
 * GG Profile Saver - Login Google accounts & lưu mỗi acc vào 1 profile riêng
 * Profiles được lưu trong saved_profiles/ - tách biệt hoàn toàn với browser chính
 * 
 * Commands:
 *   loginall  - Login tất cả accounts trong accounts.txt
 *   import    - Import accounts từ tdc-login-tool và gg login flow_v3
 *   login     - Login 1 account cụ thể: node index.js login email pass
 *   open      - Mở profile đã login: node index.js open email
 *   openall   - Mở tất cả profiles đã login thành công
 *   list      - Liệt kê tất cả profiles
 *   clean     - Xóa profiles bị lỗi, giữ profiles thành công
 *   delete    - Xóa 1 profile: node index.js delete email
 *   backup    - Backup tất cả profiles ra file zip
 *   restore   - Restore profiles từ file zip
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

puppeteer.use(StealthPlugin());

// ======================== CONFIG ========================
const CONFIG = {
    PROFILES_DIR: path.join(__dirname, 'saved_profiles'),
    DB_FILE: path.join(__dirname, 'profiles_db.json'),
    ACCOUNTS_FILE: path.join(__dirname, 'accounts.txt'),
    BACKUP_DIR: path.join(__dirname, 'backups'),
    LOGIN_URL: 'https://accounts.google.com/signin',
    CHECK_URL: 'https://myaccount.google.com',
    VERIFY_WAIT: 120000, // 120s chờ xác minh thủ công
    DELAY_BETWEEN: 2000,  // delay giữa mỗi account
};

// ======================== DATABASE ========================
function loadDB() {
    if (fs.existsSync(CONFIG.DB_FILE)) {
        return JSON.parse(fs.readFileSync(CONFIG.DB_FILE, 'utf8'));
    }
    return {};
}

function saveDB(db) {
    fs.writeFileSync(CONFIG.DB_FILE, JSON.stringify(db, null, 2), 'utf8');
}

function getNextProfileNum(db) {
    let max = 0;
    for (const key of Object.keys(db)) {
        const num = parseInt(db[key].profileDir.replace('Profile_', ''));
        if (num > max) max = num;
    }
    return max + 1;
}

// ======================== ACCOUNTS ========================
function loadAccounts(filePath) {
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

// ======================== BROWSER ========================
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

function detectBrowser() {
    for (const browser of BROWSER_LIST) {
        for (const p of browser.paths) {
            if (fs.existsSync(p)) return { name: browser.name, path: p };
        }
    }
    return null; // fallback to Puppeteer Chromium
}

function delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

async function fastType(page, selector, text) {
    await page.waitForSelector(selector, { visible: true, timeout: 15000 });
    await page.click(selector);
    await delay(100);
    await page.evaluate((sel, txt) => {
        const el = document.querySelector(sel);
        if (el) {
            el.value = txt;
            el.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }, selector, text);
    await delay(100);
}

async function launchProfileBrowser(profileDir, headless = false) {
    const browser = detectBrowser();
    const userDataDir = CONFIG.PROFILES_DIR;

    const launchArgs = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-blink-features=AutomationControlled',
        '--disable-infobars',
        '--start-maximized',
        `--profile-directory=${profileDir}`
    ];

    const launchOptions = {
        headless: headless ? 'new' : false,
        args: launchArgs,
        userDataDir: userDataDir,
        defaultViewport: null,
    };

    if (browser) launchOptions.executablePath = browser.path;

    return await puppeteer.launch(launchOptions);
}

// ======================== LOGIN FLOW ========================
async function loginAccount(email, password, profileDir) {
    console.log(`\n🚀 Login: ${email} → ${profileDir}`);

    let browser;
    try {
        browser = await launchProfileBrowser(profileDir);
    } catch (err) {
        console.log(`   ❌ Không mở được browser: ${err.message}`);
        return { status: 'error', reason: 'BROWSER_ERROR' };
    }

    const page = await browser.newPage();
    await page.setUserAgent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    );
    await page.evaluateOnNewDocument(() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    });

    let result = { status: 'error', reason: 'UNKNOWN' };

    try {
        // Step 1: Vào Google login
        console.log(`   📍 Vào trang đăng nhập...`);
        await page.goto(CONFIG.LOGIN_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await delay(2000);

        // Step 2: Nhập email
        console.log(`   📧 Nhập email...`);
        await fastType(page, 'input[type="email"]', email);
        await delay(300);

        await page.evaluate(() => {
            const btns = document.querySelectorAll('#identifierNext, button');
            for (const btn of btns) {
                if (btn.id === 'identifierNext' || btn.textContent.includes('Next') || btn.textContent.includes('Tiếp')) {
                    btn.click(); return true;
                }
            }
            return false;
        });
        await delay(4000);

        // Check email errors
        const afterEmailContent = await page.content();
        const afterEmailUrl = page.url();

        if (afterEmailUrl.includes('deletedaccount') ||
            afterEmailContent.includes('Account deleted') ||
            afterEmailContent.includes('Tài khoản đã bị xóa')) {
            console.log(`   🗑️ Account đã bị xóa!`);
            await browser.close();
            return { status: 'email_error', reason: 'ACCOUNT_DELETED' };
        }

        if (afterEmailContent.includes("Couldn't find") || afterEmailContent.includes('Không tìm thấy')) {
            console.log(`   ❌ Email không tồn tại!`);
            await browser.close();
            return { status: 'email_error', reason: 'EMAIL_NOT_FOUND' };
        }

        // Step 3: Nhập password
        try {
            console.log(`   🔐 Chờ trang password...`);
            await page.waitForSelector('input[type="password"]', { visible: true, timeout: 10000 });

            console.log(`   🔑 Nhập password...`);
            await fastType(page, 'input[type="password"]', password);
            await delay(300);

            await page.evaluate(() => {
                const btns = document.querySelectorAll('#passwordNext, button');
                for (const btn of btns) {
                    if (btn.id === 'passwordNext' || btn.textContent.includes('Next') || btn.textContent.includes('Tiếp')) {
                        btn.click(); return true;
                    }
                }
                return false;
            });
            await delay(5000);
        } catch (passError) {
            console.log(`   ⚠️ Không thấy trang password (CAPTCHA?)`);
            await browser.close();
            return { status: 'error', reason: 'NO_PASSWORD_PAGE' };
        }

        // Step 4: Check kết quả
        const finalContent = await page.content();
        const finalUrl = page.url();

        // Sai mật khẩu
        if (finalContent.includes('Wrong password') || finalContent.includes('Sai mật khẩu') ||
            finalContent.includes('password was changed') || finalContent.includes('mật khẩu đã được thay đổi') ||
            finalUrl.includes('challenge/pwd')) {
            console.log(`   ❌ Sai mật khẩu!`);
            await browser.close();
            return { status: 'wrong_password', reason: 'WRONG_PASSWORD' };
        }

        // Challenge - cần xác minh
        if (finalUrl.includes('challenge/') || finalUrl.includes('signin/rejected') ||
            finalContent.includes('Verify it') || finalContent.includes('Verify your identity') ||
            finalContent.includes('mã xác minh') || finalContent.includes('Xác minh danh tính')) {

            console.log(`   📱 Cần xác minh! Chờ ${CONFIG.VERIFY_WAIT / 1000}s để bạn xử lý thủ công...`);
            console.log(`   ⏳ Hãy hoàn thành xác minh trong cửa sổ browser...`);

            // Chờ user hoàn thành xác minh hoặc timeout
            const verifyStart = Date.now();
            let verified = false;

            while (Date.now() - verifyStart < CONFIG.VERIFY_WAIT) {
                await delay(3000);
                const currentUrl = page.url();
                if (currentUrl.includes('myaccount.google.com') ||
                    !currentUrl.includes('accounts.google.com') ||
                    currentUrl.includes('google.com/search')) {
                    verified = true;
                    break;
                }
                const remaining = Math.ceil((CONFIG.VERIFY_WAIT - (Date.now() - verifyStart)) / 1000);
                process.stdout.write(`\r   ⏳ Còn ${remaining}s...   `);
            }
            console.log('');

            if (verified) {
                console.log(`   ✅ Xác minh thành công!`);
                result = { status: 'logged_in', reason: 'VERIFIED_MANUALLY' };
            } else {
                console.log(`   ⏰ Hết thời gian chờ xác minh`);
                await browser.close();
                return { status: 'needs_verification', reason: 'VERIFY_TIMEOUT' };
            }
        }

        // Step 5: Check speedbump
        if (result.status !== 'logged_in') {
            if (finalUrl.includes('speedbump')) {
                console.log(`   ⚡ Speedbump!`);
                await delay(1500);

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

                await delay(2000);
                console.log(`   ✅ Speedbump OK!`);
                result = { status: 'logged_in', reason: 'SPEEDBUMP_ACCEPTED' };
            } else if (finalUrl.includes('myaccount.google.com') ||
                       finalUrl.includes('google.com/search') ||
                       !finalUrl.includes('accounts.google.com')) {
                result = { status: 'logged_in', reason: 'LOGIN_OK' };
                console.log(`   ✅ Login thành công!`);
            } else {
                // Chờ thêm 3s rồi check lại
                await delay(3000);
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
                    await delay(2000);
                    result = { status: 'logged_in', reason: 'SPEEDBUMP_ACCEPTED' };
                    console.log(`   ✅ Speedbump OK!`);
                } else if (!retryUrl.includes('accounts.google.com')) {
                    result = { status: 'logged_in', reason: 'LOGIN_OK' };
                    console.log(`   ✅ Login thành công!`);
                } else {
                    console.log(`   ⚠️ Kẹt ở trang login`);
                    await browser.close();
                    return { status: 'error', reason: 'STUCK_AT_LOGIN' };
                }
            }
        }

        // Step 6: Nếu login thành công, verify session bằng myaccount
        if (result.status === 'logged_in') {
            console.log(`   🔍 Kiểm tra session...`);
            try {
                await page.goto(CONFIG.CHECK_URL, { waitUntil: 'domcontentloaded', timeout: 15000 });
                await delay(2000);
                const checkUrl = page.url();
                if (checkUrl.includes('myaccount.google.com')) {
                    console.log(`   ✅ Session OK! Profile đã lưu.`);
                } else {
                    console.log(`   ⚠️ Session check redirect, nhưng profile vẫn lưu.`);
                }
            } catch (e) {
                console.log(`   ⚠️ Không check được session, nhưng profile vẫn lưu.`);
            }
        }

    } catch (error) {
        console.log(`   ❌ Lỗi: ${error.message}`);
        result = { status: 'error', reason: 'ERROR' };
    }

    try { await browser.close(); } catch (e) {}
    return result;
}

// ======================== COMMANDS ========================

async function cmdLoginAll() {
    const accounts = loadAccounts(CONFIG.ACCOUNTS_FILE);
    if (accounts.length === 0) {
        console.log('❌ Không có account nào trong accounts.txt');
        console.log('   Thêm accounts theo format: email|password');
        return;
    }

    const db = loadDB();
    console.log(`\n📋 Tìm thấy ${accounts.length} accounts`);

    // Lọc accounts chưa login thành công
    const toLogin = accounts.filter(a => {
        const entry = db[a.email];
        return !entry || entry.status !== 'logged_in';
    });

    if (toLogin.length === 0) {
        console.log('✅ Tất cả accounts đã login thành công!');
        console.log('   Dùng "node index.js list" để xem danh sách');
        return;
    }

    console.log(`🚀 Cần login ${toLogin.length} accounts (bỏ qua ${accounts.length - toLogin.length} đã OK)\n`);

    let passed = 0, failed = 0;
    for (const acc of toLogin) {
        // Assign profile dir
        let profileDir;
        if (db[acc.email]) {
            profileDir = db[acc.email].profileDir;
        } else {
            const num = getNextProfileNum(db);
            profileDir = `Profile_${num}`;
        }

        const result = await loginAccount(acc.email, acc.password, profileDir);

        db[acc.email] = {
            profileDir,
            status: result.status,
            reason: result.reason,
            lastLogin: new Date().toISOString(),
        };
        saveDB(db);

        if (result.status === 'logged_in') passed++;
        else failed++;

        console.log(`   📊 Kết quả: ${result.status} (${result.reason})`);

        if (toLogin.indexOf(acc) < toLogin.length - 1) {
            await delay(CONFIG.DELAY_BETWEEN);
        }
    }

    console.log(`\n${'='.repeat(50)}`);
    console.log(`📊 KẾT QUẢ: ${passed} thành công / ${failed} thất bại / ${accounts.length} tổng`);
    console.log(`${'='.repeat(50)}`);
}

async function cmdImport() {
    const importSources = [
        { name: 'tdc-login-tool/passed.txt', path: path.join(__dirname, '..', 'tdc-login-tool', 'passed.txt') },
        { name: 'tdc-login-tool/has_phone.txt', path: path.join(__dirname, '..', 'tdc-login-tool', 'has_phone.txt') },
        { name: 'gg login flow_v3/has_flow.txt', path: path.join(__dirname, '..', '..', '..', 'gg login flow_v3', 'has_flow.txt') },
        { name: 'gg login flow_v3/no_flow.txt', path: path.join(__dirname, '..', '..', '..', 'gg login flow_v3', 'no_flow.txt') },
    ];

    // Load existing accounts to avoid duplicates
    const existing = new Set(loadAccounts(CONFIG.ACCOUNTS_FILE).map(a => a.email));
    let totalImported = 0;

    console.log('\n📥 Import accounts từ các tool khác:\n');

    for (const source of importSources) {
        if (!fs.existsSync(source.path)) {
            console.log(`   ⚠️ ${source.name} - không tìm thấy`);
            continue;
        }

        const accounts = loadAccounts(source.path);
        const newAccounts = accounts.filter(a => !existing.has(a.email));

        if (newAccounts.length === 0) {
            console.log(`   ✅ ${source.name} - ${accounts.length} acc (tất cả đã có)`);
            continue;
        }

        const lines = newAccounts.map(a => `${a.email}|${a.password}`).join('\n') + '\n';
        fs.appendFileSync(CONFIG.ACCOUNTS_FILE, lines);

        newAccounts.forEach(a => existing.add(a.email));
        totalImported += newAccounts.length;
        console.log(`   📥 ${source.name} - import ${newAccounts.length} acc mới (bỏ ${accounts.length - newAccounts.length} trùng)`);
    }

    console.log(`\n✅ Tổng import: ${totalImported} accounts mới`);
    console.log(`📋 Tổng trong accounts.txt: ${existing.size} accounts`);
    if (totalImported > 0) {
        console.log(`\n💡 Chạy "node index.js loginall" để login tất cả`);
    }
}

async function cmdLogin(email, password) {
    if (!email || !password) {
        console.log('❌ Cú pháp: node index.js login <email> <password>');
        return;
    }

    const db = loadDB();
    let profileDir;

    if (db[email]) {
        profileDir = db[email].profileDir;
        console.log(`📂 Dùng profile cũ: ${profileDir}`);
    } else {
        const num = getNextProfileNum(db);
        profileDir = `Profile_${num}`;
        console.log(`📂 Tạo profile mới: ${profileDir}`);
    }

    const result = await loginAccount(email, password, profileDir);

    db[email] = {
        profileDir,
        status: result.status,
        reason: result.reason,
        lastLogin: new Date().toISOString(),
    };
    saveDB(db);

    // Thêm vào accounts.txt nếu chưa có
    const existing = loadAccounts(CONFIG.ACCOUNTS_FILE).map(a => a.email);
    if (!existing.includes(email)) {
        fs.appendFileSync(CONFIG.ACCOUNTS_FILE, `${email}|${password}\n`);
    }

    console.log(`\n📊 Kết quả: ${result.status} (${result.reason})`);
}

async function cmdOpen(email) {
    if (!email) {
        console.log('❌ Cú pháp: node index.js open <email>');
        return;
    }

    const db = loadDB();
    if (!db[email]) {
        console.log(`❌ Không tìm thấy profile cho ${email}`);
        console.log('   Dùng "node index.js list" để xem danh sách');
        return;
    }

    const entry = db[email];
    console.log(`\n📂 Mở profile: ${entry.profileDir} (${email})`);
    console.log(`   Status: ${entry.status} | Last: ${entry.lastLogin}`);

    const browser = await launchProfileBrowser(entry.profileDir);
    const page = await browser.newPage();
    await page.goto('https://myaccount.google.com', { waitUntil: 'domcontentloaded', timeout: 30000 });

    console.log('   ✅ Browser đã mở! Đóng browser khi xong.');
    console.log('   ⏳ Chờ browser đóng...');

    // Chờ browser đóng
    await new Promise(resolve => browser.on('disconnected', resolve));
    console.log('   ✅ Browser đã đóng.');
}

async function cmdOpenAll() {
    const db = loadDB();
    const loggedIn = Object.entries(db).filter(([_, v]) => v.status === 'logged_in');

    if (loggedIn.length === 0) {
        console.log('❌ Chưa có profile nào login thành công');
        return;
    }

    console.log(`\n🚀 Mở ${loggedIn.length} profiles đã login thành công:\n`);

    const browsers = [];
    for (const [email, entry] of loggedIn) {
        console.log(`   📂 ${email} → ${entry.profileDir}`);
        try {
            const browser = await launchProfileBrowser(entry.profileDir);
            const page = await browser.newPage();
            await page.goto('https://myaccount.google.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
            browsers.push(browser);
            await delay(1000);
        } catch (e) {
            console.log(`   ⚠️ Lỗi mở ${email}: ${e.message}`);
        }
    }

    console.log(`\n✅ Đã mở ${browsers.length} browsers! Đóng tất cả khi xong.`);
    console.log('⏳ Chờ tất cả browsers đóng...');

    // Chờ tất cả browser đóng
    await Promise.all(browsers.map(b => new Promise(resolve => b.on('disconnected', resolve))));
    console.log('✅ Tất cả browsers đã đóng.');
}

function cmdList() {
    const db = loadDB();
    const entries = Object.entries(db);

    if (entries.length === 0) {
        console.log('📋 Chưa có profile nào');
        console.log('   Dùng "node index.js loginall" hoặc "node index.js import" để bắt đầu');
        return;
    }

    console.log(`\n📋 Danh sách ${entries.length} profiles:\n`);
    console.log('  #  | Profile     | Status            | Email');
    console.log('-----|-------------|-------------------|-------------------------------');

    let i = 1;
    let logged = 0, failed = 0;
    for (const [email, entry] of entries) {
        const statusIcon = entry.status === 'logged_in' ? '✅' :
                          entry.status === 'wrong_password' ? '❌' :
                          entry.status === 'needs_verification' ? '📱' :
                          entry.status === 'email_error' ? '🗑️' : '⚠️';
        console.log(`  ${String(i).padStart(2)} | ${entry.profileDir.padEnd(11)} | ${statusIcon} ${entry.status.padEnd(15)} | ${email}`);
        if (entry.status === 'logged_in') logged++;
        else failed++;
        i++;
    }

    console.log(`\n📊 Tổng: ${logged} thành công ✅ | ${failed} thất bại ❌`);
}

function cmdClean() {
    const db = loadDB();
    const entries = Object.entries(db);
    const toDelete = entries.filter(([_, v]) => v.status !== 'logged_in');

    if (toDelete.length === 0) {
        console.log('✅ Không có profile lỗi nào cần xóa');
        return;
    }

    console.log(`\n🧹 Xóa ${toDelete.length} profiles lỗi (giữ ${entries.length - toDelete.length} thành công):\n`);

    for (const [email, entry] of toDelete) {
        const profilePath = path.join(CONFIG.PROFILES_DIR, entry.profileDir);
        if (fs.existsSync(profilePath)) {
            try {
                fs.rmSync(profilePath, { recursive: true, force: true });
                console.log(`   🗑️ ${email} (${entry.profileDir}) - ${entry.status}`);
            } catch (e) {
                console.log(`   ⚠️ Không xóa được ${profilePath}: ${e.message}`);
            }
        }
        delete db[email];
    }

    saveDB(db);
    console.log(`\n✅ Đã xóa ${toDelete.length} profiles lỗi`);
}

function cmdDelete(email) {
    if (!email) {
        console.log('❌ Cú pháp: node index.js delete <email>');
        return;
    }

    const db = loadDB();
    if (!db[email]) {
        console.log(`❌ Không tìm thấy profile cho ${email}`);
        return;
    }

    const entry = db[email];
    const profilePath = path.join(CONFIG.PROFILES_DIR, entry.profileDir);

    if (fs.existsSync(profilePath)) {
        fs.rmSync(profilePath, { recursive: true, force: true });
    }

    delete db[email];
    saveDB(db);
    console.log(`🗑️ Đã xóa profile ${entry.profileDir} (${email})`);
}

function cmdBackup() {
    if (!fs.existsSync(CONFIG.BACKUP_DIR)) {
        fs.mkdirSync(CONFIG.BACKUP_DIR, { recursive: true });
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const backupName = `backup_${timestamp}`;
    const backupPath = path.join(CONFIG.BACKUP_DIR, backupName);

    console.log(`\n💾 Backup profiles → ${backupName}\n`);

    // Copy profiles_db.json
    if (fs.existsSync(CONFIG.DB_FILE)) {
        fs.mkdirSync(backupPath, { recursive: true });
        fs.copyFileSync(CONFIG.DB_FILE, path.join(backupPath, 'profiles_db.json'));
        console.log('   ✅ profiles_db.json');
    }

    // Copy saved_profiles folder
    if (fs.existsSync(CONFIG.PROFILES_DIR)) {
        try {
            execSync(`xcopy "${CONFIG.PROFILES_DIR}" "${path.join(backupPath, 'saved_profiles')}\\" /E /I /Q /Y`, { stdio: 'pipe' });
            console.log('   ✅ saved_profiles/');
        } catch (e) {
            console.log(`   ⚠️ Lỗi copy saved_profiles: ${e.message}`);
        }
    }

    // Copy accounts.txt
    if (fs.existsSync(CONFIG.ACCOUNTS_FILE)) {
        fs.copyFileSync(CONFIG.ACCOUNTS_FILE, path.join(backupPath, 'accounts.txt'));
        console.log('   ✅ accounts.txt');
    }

    console.log(`\n✅ Backup hoàn thành: ${backupPath}`);
}

function cmdRestore(backupName) {
    if (!backupName) {
        // List available backups
        if (!fs.existsSync(CONFIG.BACKUP_DIR)) {
            console.log('❌ Thư mục backups/ không tồn tại');
            return;
        }
        const backups = fs.readdirSync(CONFIG.BACKUP_DIR).filter(f =>
            fs.statSync(path.join(CONFIG.BACKUP_DIR, f)).isDirectory()
        );
        if (backups.length === 0) {
            console.log('❌ Không có backup nào');
            return;
        }
        console.log('\n📋 Backups có sẵn:\n');
        backups.forEach((b, i) => console.log(`   ${i + 1}. ${b}`));
        console.log(`\n💡 Dùng: node index.js restore <tên_backup>`);
        return;
    }

    const backupPath = path.join(CONFIG.BACKUP_DIR, backupName);
    if (!fs.existsSync(backupPath)) {
        console.log(`❌ Không tìm thấy backup: ${backupName}`);
        return;
    }

    console.log(`\n♻️ Restore từ ${backupName}:\n`);

    const dbBackup = path.join(backupPath, 'profiles_db.json');
    if (fs.existsSync(dbBackup)) {
        fs.copyFileSync(dbBackup, CONFIG.DB_FILE);
        console.log('   ✅ profiles_db.json');
    }

    const profilesBackup = path.join(backupPath, 'saved_profiles');
    if (fs.existsSync(profilesBackup)) {
        try {
            execSync(`xcopy "${profilesBackup}" "${CONFIG.PROFILES_DIR}\\" /E /I /Q /Y`, { stdio: 'pipe' });
            console.log('   ✅ saved_profiles/');
        } catch (e) {
            console.log(`   ⚠️ Lỗi copy saved_profiles: ${e.message}`);
        }
    }

    const accBackup = path.join(backupPath, 'accounts.txt');
    if (fs.existsSync(accBackup)) {
        fs.copyFileSync(accBackup, CONFIG.ACCOUNTS_FILE);
        console.log('   ✅ accounts.txt');
    }

    console.log(`\n✅ Restore hoàn thành!`);
}

// ======================== MAIN ========================
async function main() {
    const args = process.argv.slice(2);
    const command = (args[0] || '').toLowerCase();

    console.log('╔══════════════════════════════════════════╗');
    console.log('║     GG Profile Saver v1.0                ║');
    console.log('║     Lưu mỗi acc Google vào 1 profile     ║');
    console.log('╚══════════════════════════════════════════╝');

    // Ensure directories exist
    if (!fs.existsSync(CONFIG.PROFILES_DIR)) fs.mkdirSync(CONFIG.PROFILES_DIR, { recursive: true });

    switch (command) {
        case 'loginall':
            await cmdLoginAll();
            break;
        case 'import':
            await cmdImport();
            break;
        case 'login':
            await cmdLogin(args[1], args[2]);
            break;
        case 'open':
            await cmdOpen(args[1]);
            break;
        case 'openall':
            await cmdOpenAll();
            break;
        case 'list':
            cmdList();
            break;
        case 'clean':
            cmdClean();
            break;
        case 'delete':
            cmdDelete(args[1]);
            break;
        case 'backup':
            cmdBackup();
            break;
        case 'restore':
            cmdRestore(args[1]);
            break;
        default:
            console.log('\n📖 Cách dùng:\n');
            console.log('  node index.js loginall              Login tất cả accounts trong accounts.txt');
            console.log('  node index.js import                Import accounts từ các tool khác');
            console.log('  node index.js login <email> <pass>  Login 1 account cụ thể');
            console.log('  node index.js open <email>          Mở browser với profile đã login');
            console.log('  node index.js openall               Mở tất cả profiles thành công');
            console.log('  node index.js list                  Xem danh sách profiles');
            console.log('  node index.js clean                 Xóa profiles lỗi, giữ profiles OK');
            console.log('  node index.js delete <email>        Xóa 1 profile cụ thể');
            console.log('  node index.js backup                Backup toàn bộ profiles');
            console.log('  node index.js restore [name]        Restore profiles từ backup');
            console.log('\n💡 Bắt đầu: Thêm accounts vào accounts.txt rồi chạy "node index.js loginall"');
            console.log('   Hoặc chạy "node index.js import" để import từ tdc-login-tool');
            break;
    }
}

main().catch(err => {
    console.error('❌ Fatal error:', err.message);
    process.exit(1);
});
