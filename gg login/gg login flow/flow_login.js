/**
 * Google Flow Login - PARALLEL & FAST VERSION
 * 
 * Features:
 * - Đọc accounts từ accounts.txt (format: email|pass)
 * - Chạy TẤT CẢ accounts CÙNG LÚC (parallel)
 * - Nhập liệu NHANH (delay 10-20ms)
 * - Output: email|pass|STATUS
 * - Giữ browsers mở để kiểm tra thủ công
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');

puppeteer.use(StealthPlugin());

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

    // Lưu vào accounts.json
    const jsonPath = path.join(__dirname, 'accounts.json');
    const jsonData = {
        accounts,
        settings: {
            headless: false,
            slowMo: 0,
            timeout: 30000
        }
    };
    fs.writeFileSync(jsonPath, JSON.stringify(jsonData, null, 2));
    console.log(`📄 Đã convert ${accounts.length} accounts từ accounts.txt → accounts.json`);

    return accounts;
}

// Delay ngắn
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Nhập text NHANH
async function fastType(page, selector, text) {
    try {
        await page.waitForSelector(selector, { visible: true, timeout: 15000 });
        await page.click(selector);
        await delay(100);

        // Clear và paste nhanh
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

// Login 1 account
async function loginAccount(email, password, index) {
    const startTime = Date.now();
    console.log(`[${index + 1}] 🚀 Bắt đầu: ${email}`);

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
        defaultViewport: null  // Full screen
    });

    const page = await browser.newPage();

    await page.setUserAgent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    );

    await page.evaluateOnNewDocument(() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    });

    let result = { email, password, status: 'UNKNOWN', time: 0 };

    try {
        // Bước 1: Vào Flow
        console.log(`[${index + 1}] 📍 Vào Flow...`);
        await page.goto('https://labs.google/fx/tools/flow', {
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });

        await delay(2000);

        // Bước 2: Click "Create with Flow"
        console.log(`[${index + 1}] 🖱️ Click Create with Flow...`);
        await page.evaluate(() => {
            const buttons = document.querySelectorAll('button, a, [role="button"]');
            for (const btn of buttons) {
                if (btn.textContent.includes('Create with Flow') ||
                    btn.textContent.includes('Start creating')) {
                    btn.click();
                    return true;
                }
            }
            // Thử click link có chứa text
            const links = document.querySelectorAll('a');
            for (const link of links) {
                if (link.href && link.href.includes('flow')) {
                    link.click();
                    return true;
                }
            }
            return false;
        });

        await delay(3000);

        // Kiểm tra URL
        const currentUrl = page.url();
        console.log(`[${index + 1}] 📍 URL: ${currentUrl.substring(0, 60)}...`);

        // Bước 3: Login nếu cần
        if (currentUrl.includes('accounts.google.com')) {
            console.log(`[${index + 1}] 📧 Nhập email...`);
            await fastType(page, 'input[type="email"]', email);
            await delay(300);

            // Click Next
            const nextClicked = await page.evaluate(() => {
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

            // Kiểm tra lỗi email
            const pageContent = await page.content();
            if (pageContent.includes('Couldn\'t find') || pageContent.includes('Không tìm thấy')) {
                result.status = 'EMAIL_NOT_FOUND';
                console.log(`[${index + 1}] ❌ Email không tồn tại!`);
            } else {
                // Nhập password
                try {
                    console.log(`[${index + 1}] 🔐 Nhập password...`);
                    await page.waitForSelector('input[type="password"]', { visible: true, timeout: 10000 });
                    await fastType(page, 'input[type="password"]', password);
                    await delay(300);

                    // Click Sign In
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

                    // Kiểm tra kết quả
                    const finalUrl = page.url();
                    const finalContent = await page.content();

                    if (finalContent.includes('Wrong password') || finalContent.includes('Sai mật khẩu')) {
                        result.status = 'WRONG_PASSWORD';
                        console.log(`[${index + 1}] ❌ Sai mật khẩu!`);
                    } else if (finalUrl.includes('labs.google') || finalUrl.includes('flow')) {
                        result.status = 'SUCCESS';
                        console.log(`[${index + 1}] ✅ Thành công!`);
                    } else if (finalContent.includes('verify') || finalContent.includes('Verify')) {
                        result.status = 'NEED_VERIFY';
                        console.log(`[${index + 1}] ⚠️ Cần xác minh!`);
                    } else {
                        result.status = 'CHECK_MANUALLY';
                        console.log(`[${index + 1}] ⚠️ Kiểm tra thủ công!`);
                    }

                } catch (passError) {
                    result.status = 'PASSWORD_PAGE_ERROR';
                    console.log(`[${index + 1}] ❌ Lỗi trang password!`);
                }
            }
        } else {
            result.status = 'NO_LOGIN_PAGE';
            console.log(`[${index + 1}] ⚠️ Không chuyển đến login page`);
        }

    } catch (error) {
        result.status = `ERROR: ${error.message.substring(0, 50)}`;
        console.log(`[${index + 1}] ❌ Lỗi: ${error.message}`);
    }

    result.time = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`[${index + 1}] ⏱️ Hoàn thành trong ${result.time}s`);

    // KHÔNG đóng browser
    return { result, browser, page };
}

async function main() {
    console.log('\n' + '═'.repeat(70));
    console.log('   🎬 GOOGLE FLOW LOGIN - PARALLEL & FAST VERSION 🎬');
    console.log('═'.repeat(70) + '\n');

    // Load accounts
    const accounts = loadAccountsFromTxt();
    console.log(`\n📋 Tổng số accounts: ${accounts.length}`);
    console.log('🚀 Chạy TẤT CẢ accounts CÙNG LÚC...\n');

    const startTime = Date.now();

    // Chạy SONG SONG tất cả accounts
    const promises = accounts.map((acc, i) => loginAccount(acc.email, acc.password, i));
    const results = await Promise.all(promises);

    const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);

    // Hiển thị kết quả
    console.log('\n' + '═'.repeat(70));
    console.log('                      📊 KẾT QUẢ OUTPUT');
    console.log('═'.repeat(70) + '\n');

    results.forEach(({ result }) => {
        const statusIcon = result.status === 'SUCCESS' ? '✅' : '❌';
        console.log(`${result.email}|${result.password}|${statusIcon} ${result.status}`);
    });

    console.log('\n' + '═'.repeat(70));
    console.log(`⏱️ Tổng thời gian: ${totalTime}s`);
    console.log(`✅ Thành công: ${results.filter(r => r.result.status === 'SUCCESS').length}/${accounts.length}`);
    console.log('🛑 Tất cả browsers đang mở để kiểm tra thủ công.');
    console.log('   Nhấn Ctrl+C để thoát.');
    console.log('═'.repeat(70) + '\n');

    // Lưu kết quả
    const outputResults = results.map(r => r.result);
    fs.writeFileSync(
        path.join(__dirname, 'flow_results.json'),
        JSON.stringify(outputResults, null, 2)
    );

    // Giữ script chạy
    await new Promise(() => { });
}

main().catch(console.error);
