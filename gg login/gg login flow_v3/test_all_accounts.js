/**
 * Google Login Automation Script - Test All Accounts
 * Chạy test tất cả tài khoản và capture screenshot kết quả
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');

puppeteer.use(StealthPlugin());

const configPath = path.join(__dirname, 'accounts.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

function randomDelay(min = 500, max = 1500) {
    return new Promise(resolve => {
        const delay = Math.floor(Math.random() * (max - min + 1)) + min;
        setTimeout(resolve, delay);
    });
}

async function humanType(page, selector, text) {
    try {
        await page.waitForSelector(selector, { visible: true, timeout: 20000 });
        await page.click(selector);
        await randomDelay(300, 600);

        await page.evaluate((sel) => {
            const element = document.querySelector(sel);
            if (element) element.value = '';
        }, selector);

        for (const char of text) {
            await page.type(selector, char, { delay: Math.floor(Math.random() * 80) + 40 });
        }
    } catch (error) {
        console.log(`⚠️ Không tìm thấy selector: ${selector}`);
        throw error;
    }
}

async function testLogin(email, password, accountIndex) {
    console.log(`\n${'═'.repeat(50)}`);
    console.log(`🔐 TEST ACCOUNT ${accountIndex + 1}: ${email}`);
    console.log(`${'═'.repeat(50)}`);

    const browser = await puppeteer.launch({
        headless: false,
        slowMo: 30,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--window-size=1366,768'
        ],
        defaultViewport: { width: 1366, height: 768 }
    });

    const page = await browser.newPage();

    await page.setUserAgent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    );

    await page.evaluateOnNewDocument(() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    });

    const screenshotDir = path.join(__dirname, 'screenshots');
    if (!fs.existsSync(screenshotDir)) {
        fs.mkdirSync(screenshotDir, { recursive: true });
    }

    let result = { email, success: false, error: null, screenshot: null };

    try {
        // Bước 1: Truy cập trang login
        console.log('📍 Đang truy cập trang đăng nhập Google...');
        await page.goto('https://accounts.google.com/signin/v2/identifier', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });

        await randomDelay(2000, 3000);

        // Screenshot trang login
        const loginScreenshot = path.join(screenshotDir, `${accountIndex + 1}_01_login_page.png`);
        await page.screenshot({ path: loginScreenshot, fullPage: true });
        console.log(`📸 Screenshot: ${loginScreenshot}`);

        // Bước 2: Nhập Email
        console.log('📧 Đang nhập email...');
        await humanType(page, 'input[type="email"]', email);

        await randomDelay(1000, 1500);

        // Bước 3: Click Next
        console.log('➡️ Đang click nút Tiếp theo...');
        const nextButtons = ['#identifierNext', '#identifierNext button', 'button[jsname="LgbsSe"]'];

        for (const selector of nextButtons) {
            try {
                await page.waitForSelector(selector, { visible: true, timeout: 3000 });
                await page.click(selector);
                break;
            } catch (e) { continue; }
        }

        await randomDelay(3000, 4000);

        // Screenshot sau khi nhập email
        const afterEmailScreenshot = path.join(screenshotDir, `${accountIndex + 1}_02_after_email.png`);
        await page.screenshot({ path: afterEmailScreenshot, fullPage: true });
        console.log(`📸 Screenshot: ${afterEmailScreenshot}`);

        // Kiểm tra lỗi email
        const pageContent = await page.content();
        const currentUrl = page.url();

        if (pageContent.includes('Couldn\'t find your Google Account') ||
            pageContent.includes('Không tìm thấy Tài khoản Google') ||
            pageContent.includes('couldn\'t find') ||
            pageContent.includes('Enter a valid email')) {
            result.error = 'EMAIL_NOT_FOUND - Email không tồn tại trong hệ thống Google';
            console.log('❌ LỖI: Email không tồn tại trong Google!');
        } else {
            // Thử nhập password
            try {
                console.log('🔐 Đang chờ trang mật khẩu...');
                const passwordSelector = 'input[type="password"]';
                await page.waitForSelector(passwordSelector, { visible: true, timeout: 10000 });

                console.log('🔑 Đang nhập mật khẩu...');
                await humanType(page, passwordSelector, password);

                await randomDelay(1000, 1500);

                // Click Sign In
                console.log('✅ Đang đăng nhập...');
                const signInButtons = ['#passwordNext', '#passwordNext button'];

                for (const selector of signInButtons) {
                    try {
                        await page.waitForSelector(selector, { visible: true, timeout: 3000 });
                        await page.click(selector);
                        break;
                    } catch (e) { continue; }
                }

                await randomDelay(4000, 5000);

                // Screenshot sau khi đăng nhập
                const afterLoginScreenshot = path.join(screenshotDir, `${accountIndex + 1}_03_after_login.png`);
                await page.screenshot({ path: afterLoginScreenshot, fullPage: true });
                console.log(`📸 Screenshot: ${afterLoginScreenshot}`);
                result.screenshot = afterLoginScreenshot;

                // Kiểm tra kết quả
                const finalUrl = page.url();
                const finalContent = await page.content();

                if (finalUrl.includes('myaccount.google.com') ||
                    finalUrl.includes('mail.google.com') ||
                    !finalUrl.includes('signin')) {
                    result.success = true;
                    result.error = null;
                    console.log('🎉 ĐĂNG NHẬP THÀNH CÔNG!');
                } else if (finalContent.includes('Wrong password') ||
                    finalContent.includes('Sai mật khẩu')) {
                    result.error = 'WRONG_PASSWORD - Mật khẩu không đúng';
                    console.log('❌ LỖI: Mật khẩu không đúng!');
                } else if (finalContent.includes('verify') ||
                    finalContent.includes('Verify') ||
                    finalContent.includes('xác minh')) {
                    result.error = 'VERIFICATION_REQUIRED - Google yêu cầu xác minh (2FA/Phone)';
                    console.log('⚠️ CẦN XÁC MINH: Google yêu cầu xác minh thêm!');
                } else if (finalContent.includes('captcha') ||
                    finalContent.includes('robot')) {
                    result.error = 'CAPTCHA - Google yêu cầu giải CAPTCHA';
                    console.log('⚠️ CAPTCHA: Google yêu cầu giải CAPTCHA!');
                } else {
                    result.error = 'UNKNOWN - Không xác định được trạng thái (xem screenshot)';
                    console.log('⚠️ KHÔNG XÁC ĐỊNH: Kiểm tra screenshot để biết chi tiết');
                }

            } catch (passError) {
                result.error = `PASSWORD_PAGE_ERROR - Không tìm thấy trang mật khẩu: ${passError.message}`;
                console.log('❌ LỖI: Không tìm thấy trang mật khẩu!');

                const errorScreenshot = path.join(screenshotDir, `${accountIndex + 1}_error.png`);
                await page.screenshot({ path: errorScreenshot, fullPage: true });
                result.screenshot = errorScreenshot;
            }
        }

    } catch (error) {
        result.error = `EXCEPTION - ${error.message}`;
        console.error('❌ Lỗi:', error.message);

        const errorScreenshot = path.join(screenshotDir, `${accountIndex + 1}_exception.png`);
        await page.screenshot({ path: errorScreenshot, fullPage: true });
        result.screenshot = errorScreenshot;
    }

    await browser.close();
    return result;
}

async function main() {
    console.log('═══════════════════════════════════════════════════');
    console.log('     🔐 GPM Google Login - TEST ALL ACCOUNTS 🔐     ');
    console.log('═══════════════════════════════════════════════════\n');
    console.log(`📋 Số tài khoản cần test: ${config.accounts.length}\n`);

    const results = [];

    for (let i = 0; i < config.accounts.length; i++) {
        const account = config.accounts[i];
        const result = await testLogin(account.email, account.password, i);
        results.push(result);

        // Delay giữa các lần test
        if (i < config.accounts.length - 1) {
            console.log('\n⏳ Chờ 5 giây trước khi test tài khoản tiếp theo...\n');
            await new Promise(r => setTimeout(r, 5000));
        }
    }

    // Tổng kết
    console.log('\n\n' + '═'.repeat(60));
    console.log('                    📊 KẾT QUẢ TỔNG HỢP                    ');
    console.log('═'.repeat(60));

    results.forEach((r, i) => {
        const status = r.success ? '✅ THÀNH CÔNG' : '❌ THẤT BẠI';
        console.log(`\n${i + 1}. ${r.email}`);
        console.log(`   Trạng thái: ${status}`);
        if (r.error) console.log(`   Lỗi: ${r.error}`);
        if (r.screenshot) console.log(`   Screenshot: ${r.screenshot}`);
    });

    console.log('\n' + '═'.repeat(60));
    console.log(`📁 Tất cả screenshots được lưu tại: ${path.join(__dirname, 'screenshots')}`);
    console.log('═'.repeat(60) + '\n');

    // Lưu kết quả ra file
    const resultsPath = path.join(__dirname, 'test_results.json');
    fs.writeFileSync(resultsPath, JSON.stringify(results, null, 2));
    console.log(`📄 Kết quả đã lưu vào: ${resultsPath}`);
}

main().catch(console.error);
