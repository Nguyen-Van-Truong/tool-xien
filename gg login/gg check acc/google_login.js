/**
 * Google Login Automation Script
 * Sử dụng Puppeteer với Stealth Plugin để đăng nhập Google
 * 
 * Cách sử dụng:
 * 1. Chỉnh sửa accounts.json với email/password của bạn
 * 2. Chạy: npm install
 * 3. Chạy: npm start hoặc node google_login.js
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');

// Sử dụng Stealth Plugin để tránh bị phát hiện là bot
puppeteer.use(StealthPlugin());

// Đọc cấu hình từ accounts.json
const configPath = path.join(__dirname, 'accounts.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

// Hàm delay ngẫu nhiên để mô phỏng hành vi người dùng
function randomDelay(min = 500, max = 1500) {
    return new Promise(resolve => {
        const delay = Math.floor(Math.random() * (max - min + 1)) + min;
        setTimeout(resolve, delay);
    });
}

// Hàm gõ text với tốc độ ngẫu nhiên (giống người thật)
async function humanType(page, selector, text) {
    try {
        await page.waitForSelector(selector, { visible: true, timeout: 20000 });
        await page.click(selector);
        await randomDelay(300, 600);

        // Clear existing text first
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

// Hàm chính để đăng nhập Google
async function loginGoogle(email, password) {
    console.log(`\n🚀 Bắt đầu đăng nhập với email: ${email}`);

    const browser = await puppeteer.launch({
        headless: config.settings.headless,
        slowMo: config.settings.slowMo,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--window-size=1366,768',
            '--start-maximized'
        ],
        defaultViewport: {
            width: 1366,
            height: 768
        }
    });

    const page = await browser.newPage();

    // Thiết lập user agent
    await page.setUserAgent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    );

    // Ẩn webdriver flag
    await page.evaluateOnNewDocument(() => {
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
    });

    try {
        // Bước 1: Truy cập trang đăng nhập Google
        console.log('📍 Đang truy cập trang đăng nhập Google...');
        await page.goto('https://accounts.google.com/signin/v2/identifier', {
            waitUntil: 'networkidle2',
            timeout: config.settings.timeout
        });

        await randomDelay(1000, 2000);

        // Bước 2: Nhập Email
        console.log('📧 Đang nhập email...');
        const emailSelector = 'input[type="email"]';
        await humanType(page, emailSelector, email);

        await randomDelay(500, 1000);

        // Bước 3: Click nút Next
        console.log('➡️ Đang click nút Tiếp theo...');
        const nextButtonSelectors = [
            '#identifierNext',
            '#identifierNext button',
            'button[jsname="LgbsSe"]'
        ];

        for (const selector of nextButtonSelectors) {
            try {
                await page.waitForSelector(selector, { visible: true, timeout: 3000 });
                await page.click(selector);
                break;
            } catch (e) {
                continue;
            }
        }

        await randomDelay(2000, 3000);

        // Bước 4: Chờ trang mật khẩu load
        console.log('🔐 Đang chờ trang mật khẩu...');
        const passwordSelector = 'input[type="password"]';
        await page.waitForSelector(passwordSelector, { visible: true, timeout: 15000 });

        await randomDelay(1000, 2000);

        // Bước 5: Nhập mật khẩu
        console.log('🔑 Đang nhập mật khẩu...');
        await humanType(page, passwordSelector, password);

        await randomDelay(500, 1000);

        // Bước 6: Click nút Sign In
        console.log('✅ Đang đăng nhập...');
        const signInButtonSelectors = [
            '#passwordNext',
            '#passwordNext button',
            'button[jsname="LgbsSe"]'
        ];

        for (const selector of signInButtonSelectors) {
            try {
                await page.waitForSelector(selector, { visible: true, timeout: 3000 });
                await page.click(selector);
                break;
            } catch (e) {
                continue;
            }
        }

        // Bước 7: Chờ đăng nhập thành công
        await randomDelay(3000, 5000);

        // Kiểm tra kết quả
        const currentUrl = page.url();

        if (currentUrl.includes('myaccount.google.com') ||
            currentUrl.includes('mail.google.com') ||
            !currentUrl.includes('signin')) {
            console.log('🎉 ĐĂNG NHẬP THÀNH CÔNG!');
            console.log(`📍 URL hiện tại: ${currentUrl}`);

            // Lưu cookies để sử dụng lại sau
            const cookies = await page.cookies();
            const cookiesPath = path.join(__dirname, `cookies_${email.split('@')[0]}.json`);
            fs.writeFileSync(cookiesPath, JSON.stringify(cookies, null, 2));
            console.log(`💾 Đã lưu cookies vào: ${cookiesPath}`);

            return { success: true, browser, page };
        } else {
            // Có thể gặp CAPTCHA hoặc 2FA
            console.log('⚠️ Có thể cần xác thực bổ sung (CAPTCHA/2FA)');
            console.log(`📍 URL hiện tại: ${currentUrl}`);

            // Giữ browser mở để người dùng xử lý thủ công
            console.log('⏳ Giữ browser mở 60 giây để xử lý thủ công...');
            await new Promise(resolve => setTimeout(resolve, 60000));

            return { success: false, browser, page, reason: 'Cần xác thực bổ sung' };
        }

    } catch (error) {
        console.error('❌ Lỗi:', error.message);

        // Screenshot lỗi để debug
        const screenshotPath = path.join(__dirname, `error_${Date.now()}.png`);
        await page.screenshot({ path: screenshotPath, fullPage: true });
        console.log(`📸 Đã lưu screenshot lỗi: ${screenshotPath}`);

        return { success: false, browser, page, error: error.message };
    }
}

// Hàm đăng nhập với cookies đã lưu (nhanh hơn)
async function loginWithCookies(email) {
    const cookiesPath = path.join(__dirname, `cookies_${email.split('@')[0]}.json`);

    if (!fs.existsSync(cookiesPath)) {
        console.log('⚠️ Không tìm thấy cookies đã lưu, sẽ đăng nhập mới...');
        return null;
    }

    console.log('🍪 Đang thử đăng nhập với cookies đã lưu...');

    const browser = await puppeteer.launch({
        headless: config.settings.headless,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    const cookies = JSON.parse(fs.readFileSync(cookiesPath, 'utf8'));
    await page.setCookie(...cookies);

    await page.goto('https://mail.google.com', { waitUntil: 'networkidle2' });

    const currentUrl = page.url();
    if (currentUrl.includes('mail.google.com/mail')) {
        console.log('🎉 Đăng nhập bằng cookies thành công!');
        return { success: true, browser, page };
    } else {
        console.log('⚠️ Cookies đã hết hạn, cần đăng nhập lại...');
        await browser.close();
        return null;
    }
}

// Hàm chính
async function main() {
    console.log('═══════════════════════════════════════════');
    console.log('     🔐 GPM Google Login Automation 🔐     ');
    console.log('═══════════════════════════════════════════\n');

    // Lấy account đầu tiên từ config
    const account = config.accounts[0];

    if (account.email === 'your-email@gmail.com') {
        console.log('⚠️ Vui lòng cấu hình email/password trong file accounts.json');
        console.log('📁 Đường dẫn: ' + configPath);
        process.exit(1);
    }

    // Thử đăng nhập với cookies trước
    let result = await loginWithCookies(account.email);

    // Nếu không có cookies hoặc hết hạn, đăng nhập mới
    if (!result) {
        result = await loginGoogle(account.email, account.password);
    }

    if (result && result.success) {
        console.log('\n✨ Script hoàn thành thành công!');
        console.log('💡 Browser vẫn đang mở, bạn có thể tiếp tục sử dụng...');

        // Giữ browser mở
        // Uncomment dòng dưới nếu muốn tự động đóng browser
        // await result.browser.close();
    } else {
        console.log('\n❌ Đăng nhập không thành công.');
        if (result && result.browser) {
            await result.browser.close();
        }
    }
}

// Chạy script
main().catch(console.error);
