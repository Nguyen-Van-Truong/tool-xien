/**
 * Google Flow Login V2 - WITH FLOW CHECK
 * 
 * Features:
 * - Đọc accounts từ accounts.txt (format: email|pass)
 * - Mở theo thứ tự với delay 1s
 * - Kiểm tra Flow availability qua API sau login
 * - 3 trạng thái: LOGIN_FAILED, HAS_FLOW, NO_FLOW
 * - Lưu kết quả REALTIME sau mỗi account
 * - Giữ browsers mở để kiểm tra thủ công
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');

puppeteer.use(StealthPlugin());

const RESULTS_FILE = path.join(__dirname, 'flow_results.json');

// Đọc accounts từ accounts.txt
function loadAccountsFromTxt() {
    const txtPath = path.join(__dirname, 'accounts.txt');

    if (!fs.existsSync(txtPath)) {
        console.log('❌ Không tìm thấy accounts.txt');
        process.exit(1);
    }

    const content = fs.readFileSync(txtPath, 'utf8');
    const lines = content.trim().split('\n').filter(line => line.trim());

    const accounts = lines.map(line => {
        const [email, password] = line.trim().split('|');
        return { email: email.trim(), password: password.trim() };
    });

    console.log(`📄 Đã load ${accounts.length} accounts từ accounts.txt`);
    return accounts;
}

// Delay
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// File paths cho 3 trường hợp
const HAS_FLOW_FILE = path.join(__dirname, 'has_flow.txt');
const NO_FLOW_FILE = path.join(__dirname, 'no_flow.txt');
const LOGIN_FAILED_FILE = path.join(__dirname, 'login_failed.txt');

// Lưu kết quả REALTIME (sau mỗi account)
function saveResultRealtime(result) {
    let results = [];

    // Đọc file cũ nếu có
    if (fs.existsSync(RESULTS_FILE)) {
        try {
            results = JSON.parse(fs.readFileSync(RESULTS_FILE, 'utf8'));
        } catch (e) {
            results = [];
        }
    }

    // Append kết quả mới
    results.push(result);

    // Lưu vào JSON
    fs.writeFileSync(RESULTS_FILE, JSON.stringify(results, null, 2));

    // Lưu vào file txt tương ứng
    const line = `${result.email}|${result.password}\n`;

    if (result.status === 'HAS_FLOW') {
        fs.appendFileSync(HAS_FLOW_FILE, line);
    } else if (result.status === 'NO_FLOW') {
        fs.appendFileSync(NO_FLOW_FILE, line);
    } else {
        fs.appendFileSync(LOGIN_FAILED_FILE, line);
    }

    console.log(`💾 Đã lưu: ${result.email} → ${result.status}`);
}

// Reset file kết quả khi bắt đầu - XÓA file cũ trước
function resetResultsFile() {
    // Xóa file cũ nếu tồn tại
    if (fs.existsSync(RESULTS_FILE)) fs.unlinkSync(RESULTS_FILE);
    if (fs.existsSync(HAS_FLOW_FILE)) fs.unlinkSync(HAS_FLOW_FILE);
    if (fs.existsSync(NO_FLOW_FILE)) fs.unlinkSync(NO_FLOW_FILE);
    if (fs.existsSync(LOGIN_FAILED_FILE)) fs.unlinkSync(LOGIN_FAILED_FILE);

    // Tạo file mới trống
    fs.writeFileSync(RESULTS_FILE, '[]');
    fs.writeFileSync(HAS_FLOW_FILE, '');
    fs.writeFileSync(NO_FLOW_FILE, '');
    fs.writeFileSync(LOGIN_FAILED_FILE, '');

    console.log('🗑️ Đã xóa kết quả cũ, sẵn sàng chạy mới!');
}

// Nhập text NHANH
async function fastType(page, selector, text) {
    try {
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
    } catch (error) {
        throw error;
    }
}

// Kiểm tra Flow availability qua API
async function checkFlowAvailability(page) {
    try {
        // Chờ 2s cho page load hoàn toàn trước khi gọi API
        await delay(2000);

        console.log(`   🔍 Kiểm tra Flow availability...`);

        const response = await page.evaluate(async () => {
            try {
                const res = await fetch('https://labs.google/fx/api/trpc/general.fetchToolAvailability?input=%7B%22json%22%3A%7B%22tool%22%3A%22PINHOLE%22%7D%7D');
                const data = await res.json();
                return data;
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

// Login 1 account
async function loginAccount(email, password, index, total) {
    const startTime = Date.now();
    console.log(`\n${'─'.repeat(60)}`);
    console.log(`[${index + 1}/${total}] 🚀 ${email}`);
    console.log(`${'─'.repeat(60)}`);

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
        // Bước 1: Vào Flow
        console.log(`   📍 Vào Flow...`);
        await page.goto('https://labs.google/fx/tools/flow', {
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });

        await delay(2000);

        // Bước 2: Click "Create with Flow"
        console.log(`   🖱️ Click Create with Flow...`);
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

        await delay(3000);

        const currentUrl = page.url();

        // Bước 3: Login nếu cần
        if (currentUrl.includes('accounts.google.com')) {

            let loginSuccess = false;
            let retryCount = 0;
            const maxRetries = 3;

            while (!loginSuccess && retryCount < maxRetries) {
                retryCount++;

                if (retryCount > 1) {
                    console.log(`   🔄 Thử lại lần ${retryCount}/${maxRetries}...`);
                    await page.goto('https://labs.google/fx/tools/flow', {
                        waitUntil: 'domcontentloaded',
                        timeout: 30000
                    });
                    await delay(2000);

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
                    await delay(3000);
                }

                try {
                    console.log(`   📧 Nhập email...`);
                    await fastType(page, 'input[type="email"]', email);
                    await delay(300);

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

                    await delay(2500);

                    const pageContent = await page.content();
                    if (pageContent.includes('Couldn\'t find') || pageContent.includes('Không tìm thấy')) {
                        result.status = 'LOGIN_FAILED';
                        result.flowState = 'EMAIL_NOT_FOUND';
                        console.log(`   ❌ Email không tồn tại!`);
                        loginSuccess = true;
                    } else {
                        try {
                            console.log(`   🔐 Chờ trang password...`);
                            await page.waitForSelector('input[type="password"]', { visible: true, timeout: 8000 });

                            console.log(`   🔑 Nhập password...`);
                            await fastType(page, 'input[type="password"]', password);
                            await delay(300);

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

                            await delay(4000);

                            const finalUrl = page.url();
                            const finalContent = await page.content();

                            if (finalContent.includes('Wrong password') || finalContent.includes('Sai mật khẩu')) {
                                result.status = 'LOGIN_FAILED';
                                result.flowState = 'WRONG_PASSWORD';
                                console.log(`   ❌ Sai mật khẩu!`);
                            } else if (finalContent.includes('verify') || finalContent.includes('Verify')) {
                                result.status = 'LOGIN_FAILED';
                                result.flowState = 'NEED_VERIFY';
                                console.log(`   ⚠️ Cần xác minh!`);
                            } else {
                                // Có thể đã login thành công - thử navigate về Flow và check API
                                console.log(`   🔄 Thử chuyển về Flow page...`);

                                try {
                                    // Navigate về Flow
                                    await page.goto('https://labs.google/fx/tools/flow', {
                                        waitUntil: 'domcontentloaded',
                                        timeout: 15000
                                    });
                                    await delay(3000);

                                    // Kiểm tra Flow availability
                                    const flowCheck = await checkFlowAvailability(page);
                                    result.flowState = flowCheck.state;

                                    if (flowCheck.available) {
                                        result.status = 'HAS_FLOW';
                                        console.log(`   🎬 CÓ FLOW! (${flowCheck.state})`);
                                    } else if (flowCheck.state === 'UNAVAILABLE_LOW_REPUTATION') {
                                        result.status = 'NO_FLOW';
                                        console.log(`   ⚠️ KHÔNG CÓ FLOW (${flowCheck.state})`);
                                    } else if (flowCheck.state === 'API_ERROR' || flowCheck.state === 'CHECK_ERROR') {
                                        result.status = 'CHECK_MANUALLY';
                                        console.log(`   ⚠️ Không kiểm tra được API, check thủ công!`);
                                    } else {
                                        result.status = 'NO_FLOW';
                                        console.log(`   ⚠️ KHÔNG CÓ FLOW (${flowCheck.state})`);
                                    }
                                } catch (navError) {
                                    result.status = 'CHECK_MANUALLY';
                                    result.flowState = 'NAV_ERROR';
                                    console.log(`   ⚠️ Không navigate được, check thủ công!`);
                                }
                            }

                            loginSuccess = true;

                        } catch (passError) {
                            console.log(`   ⚠️ Không thấy trang password (có thể CAPTCHA)`);

                            if (retryCount >= maxRetries) {
                                result.status = 'LOGIN_FAILED';
                                result.flowState = 'CAPTCHA_OR_ERROR';
                                console.log(`   ❌ Đã thử ${maxRetries} lần, không qua được!`);
                            }
                        }
                    }
                } catch (err) {
                    console.log(`   ⚠️ Lỗi: ${err.message}`);
                    if (retryCount >= maxRetries) {
                        result.status = 'LOGIN_FAILED';
                        result.flowState = 'ERROR';
                    }
                }
            }
        } else {
            result.status = 'LOGIN_FAILED';
            result.flowState = 'NO_LOGIN_PAGE';
            console.log(`   ⚠️ Không chuyển đến login page`);
        }

    } catch (error) {
        result.status = 'LOGIN_FAILED';
        result.flowState = `ERROR: ${error.message.substring(0, 30)}`;
        console.log(`   ❌ Lỗi: ${error.message}`);
    }

    result.time = ((Date.now() - startTime) / 1000).toFixed(1);

    // Lưu kết quả REALTIME
    saveResultRealtime(result);

    console.log(`   ⏱️ Hoàn thành trong ${result.time}s`);

    return { result, browser, page };
}

async function main() {
    console.log('\n' + '═'.repeat(70));
    console.log('   🎬 GOOGLE FLOW LOGIN V2 - WITH FLOW CHECK 🎬');
    console.log('═'.repeat(70) + '\n');

    // Reset file kết quả
    resetResultsFile();

    // Load accounts
    const accounts = loadAccountsFromTxt();
    console.log(`📋 Tổng số accounts: ${accounts.length}`);
    console.log('🚀 Mở theo thứ tự với delay 1s...\n');

    const startTime = Date.now();
    const allResults = [];

    // Chạy lần lượt theo thứ tự
    for (let i = 0; i < accounts.length; i++) {
        const acc = accounts[i];

        if (i > 0) {
            await delay(1000);
        }

        const promise = loginAccount(acc.email, acc.password, i, accounts.length);
        allResults.push(promise);
    }

    // Chờ tất cả hoàn thành
    const finalResults = await Promise.all(allResults);

    const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);

    // Hiển thị kết quả cuối
    console.log('\n\n' + '═'.repeat(70));
    console.log('                      📊 KẾT QUẢ TỔNG HỢP');
    console.log('═'.repeat(70) + '\n');

    let hasFlow = 0, noFlow = 0, loginFailed = 0;

    finalResults.forEach(({ result }) => {
        let icon = '❓';
        if (result.status === 'HAS_FLOW') { icon = '✅'; hasFlow++; }
        else if (result.status === 'NO_FLOW') { icon = '⚠️'; noFlow++; }
        else { icon = '❌'; loginFailed++; }

        console.log(`${icon} ${result.email}|${result.password}|${result.status}|${result.flowState}`);
    });

    console.log('\n' + '═'.repeat(70));
    console.log(`⏱️ Tổng thời gian: ${totalTime}s`);
    console.log(`✅ HAS_FLOW: ${hasFlow} | ⚠️ NO_FLOW: ${noFlow} | ❌ LOGIN_FAILED: ${loginFailed}`);
    console.log(`📁 Kết quả đã lưu: ${RESULTS_FILE}`);
    console.log('🛑 Browsers đang mở để kiểm tra thủ công.');
    console.log('   Nhấn Ctrl+C để thoát.');
    console.log('═'.repeat(70) + '\n');

    // Giữ script chạy
    await new Promise(() => { });
}

main().catch(console.error);
