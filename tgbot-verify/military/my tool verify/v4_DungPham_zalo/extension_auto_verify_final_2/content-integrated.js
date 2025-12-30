// Content script for ChatGPT account signup + verify automation
let isRunning = false;
let currentDataIndex = 0;
let dataArray = []; // Veterans data array
let chatgptAccount = null; // Single ChatGPT account (6 fields)
let stats = {
    processed: 0,
    success: 0,
    failed: 0
};
let currentEmail = ''; // For verify email generation
let mailRetryCount = 0;
const MAX_MAIL_RETRIES = 10;

// Parse data from format: email-chatgpt|pass-chatgpt|email-login|pass-email|refresh_token|client_id|first|last|branch|month|day|year
function parseAccountData(dataString) {
    const lines = dataString.trim().split('\n').filter(line => line.trim());
    return lines.map(line => {
        const parts = line.split('|').map(p => p.trim());
        if (parts.length < 12) {
            throw new Error(`Invalid data format: ${line}. Expected: email-chatgpt|pass-chatgpt|email-login|pass-email|refresh_token|client_id|first|last|branch|month|day|year`);
        }
        return {
            // Signup data (6 fields đầu)
            email: parts[0],           // email-chatgpt
            password: parts[1],        // pass-chatgpt
            emailLogin: parts[2],      // email-login
            passEmail: parts[3],       // pass-email
            refreshToken: parts[4],    // refresh_token
            clientId: parts[5],        // client_id
            // Verify data (6 fields cuối)
            first: parts[6],           // first name
            last: parts[7],            // last name
            branch: parts[8],          // branch
            month: parts[9],           // month
            day: parts[10],            // day
            year: parts[11],           // year
            original: line,
            signupCompleted: false     // Track if signup is done
        };
    });
}

// Listen for messages from side panel or background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'startVerification' || message.action === 'startSignup') {
        try {
            // New format: separate account and data
            if (message.account && Array.isArray(message.data)) {
                // Separate account and veterans data
                chatgptAccount = message.account;
                dataArray = message.data; // Veterans data array
            } else if (Array.isArray(message.data)) {
                // Old format: combined data (12 fields per line)
                // For backward compatibility, but preferred format is separate
                const combinedData = message.data;
                if (combinedData.length > 0 && combinedData[0].email) {
                    // Extract account from first item
                    chatgptAccount = {
                        email: combinedData[0].email,
                        password: combinedData[0].password,
                        emailLogin: combinedData[0].emailLogin,
                        passEmail: combinedData[0].passEmail,
                        refreshToken: combinedData[0].refreshToken,
                        clientId: combinedData[0].clientId
                    };
                    // Extract veterans data from first item
                    dataArray = [{
                        first: combinedData[0].first,
                        last: combinedData[0].last,
                        branch: combinedData[0].branch,
                        month: combinedData[0].month,
                        day: combinedData[0].day,
                        year: combinedData[0].year,
                        original: combinedData[0].original
                    }];
                }
            } else if (typeof message.data === 'string') {
                // Old string format: parse 12 fields
                const parsedData = parseAccountData(message.data);
                if (parsedData.length > 0) {
                    chatgptAccount = {
                        email: parsedData[0].email,
                        password: parsedData[0].password,
                        emailLogin: parsedData[0].emailLogin,
                        passEmail: parsedData[0].passEmail,
                        refreshToken: parsedData[0].refreshToken,
                        clientId: parsedData[0].clientId
                    };
                    dataArray = parsedData.map(item => ({
                        first: item.first,
                        last: item.last,
                        branch: item.branch,
                        month: item.month,
                        day: item.day,
                        year: item.year,
                        original: item.original
                    }));
                }
            }
            
            if (!chatgptAccount || !dataArray || dataArray.length === 0) {
                throw new Error('Missing ChatGPT account or veterans data');
            }
            
            currentDataIndex = 0;
            stats = { processed: 0, success: 0, failed: 0 };
            isRunning = true;
            currentEmail = '';
            mailRetryCount = 0;

            // Save to storage
            chrome.storage.local.set({
                'chatgpt-account': chatgptAccount,
                'veterans-data-array': dataArray,
                'veterans-current-index': 0,
                'veterans-is-running': true,
                'veterans-stats': stats
            }, () => {
                startSignupLoop();
                sendResponse({ success: true });
            });
        } catch (error) {
            console.error('❌ Error parsing data:', error);
            sendResponse({ success: false, error: error.message });
        }
    } else if (message.action === 'stopVerification' || message.action === 'stopSignup') {
        isRunning = false;
        chrome.storage.local.set({ 'veterans-is-running': false });
        sendStatus('⏹️ Process stopped', 'info');
        sendResponse({ success: true });
    }
    return true;
});

// Auto-resume when page loads
(function autoResumeSignup() {
    chrome.storage.local.get(
        [
            'chatgpt-account',
            'veterans-data-array',
            'veterans-current-index',
            'veterans-is-running',
            'veterans-stats'
        ],
        (result) => {
            if (
                result['veterans-is-running'] &&
                result['veterans-data-array'] &&
                result['chatgpt-account']
            ) {
                chatgptAccount = result['chatgpt-account'];
                dataArray = result['veterans-data-array'];
                currentDataIndex = result['veterans-current-index'] || 0;
                if (result['veterans-stats']) {
                    stats = result['veterans-stats'];
                }
                isRunning = true;
                setTimeout(() => {
                    startSignupLoop();
                }, 2000);
            }
        }
    );
})();

async function startSignupLoop() {
    if (!isRunning) {
        return;
    }

    // Check if signup is already completed, skip to verify
    const signupCompleted = chatgptAccount && chatgptAccount.signupCompleted;
    if (signupCompleted) {
        sendStatus('✅ Signup/Login already completed, starting verify...', 'info');
        // Navigate to veterans-claim if not already there
        const currentUrl = window.location.href;
        if (!currentUrl.includes('chatgpt.com/veterans-claim')) {
            window.location.href = 'https://chatgpt.com/veterans-claim';
            await delay(5000);
        }
        await startVerificationLoop();
        return;
    }

    if (!chatgptAccount) {
        isRunning = false;
        chrome.storage.local.set({ 'veterans-is-running': false });
        sendStatus('❌ No ChatGPT account loaded', 'error');
        return;
    }

    sendStatus(
        `🔄 Signing up/Logging in: ${chatgptAccount.email}`,
        'info'
    );

    // Save current state
    chrome.storage.local.set({
        'chatgpt-account': chatgptAccount,
        'veterans-is-running': true
    });

    try {
        const currentUrl = window.location.href;

        // B1: Truy cập chatgpt.com hoặc auth.openai.com (cả 2 đều OK)
        const isValidUrl = currentUrl.includes('chatgpt.com') || currentUrl.includes('auth.openai.com') || currentUrl.includes('openai.com');
        if (!isValidUrl) {
            window.location.href = 'https://chatgpt.com';
            await delay(5000);
            await startSignupLoop();
            return;
        }

        // Kiểm tra URL auth.openai.com/create-account/password (B4: Password page) - kiểm tra URL trước
        if (currentUrl.includes('auth.openai.com/create-account/password')) {
            sendStatus('🔍 On password page, waiting for form to load...', 'info');

            // Đợi và thử tìm password input nhiều lần
            let passwordInput = null;
            let attempts = 0;
            const maxAttempts = 15;

            while (attempts < maxAttempts && !passwordInput && isRunning) {
                attempts++;
                passwordInput = document.querySelector('input[name="new-password"]') ||
                    document.querySelector('input[id*="-new-password"]') ||
                    document.querySelector('input[type="password"][placeholder="Password"]') ||
                    document.querySelector('input[type="password"]');

                if (passwordInput) {
                    sendStatus('✅ Found password form, filling...', 'success');
                    await fillPassword(currentData);
                    return;
                }

                await delay(500);
            }

            if (!passwordInput) {
                await delay(1000);
                await startSignupLoop();
            }
            return;
        }

        // Kiểm tra URL auth.openai.com/email-verification (B5: OTP page)
        if (currentUrl.includes('auth.openai.com/email-verification') || currentUrl.includes('email-verification')) {
            sendStatus('📧 On email verification page, waiting 10s for email...', 'info');

            // Đợi 10 giây để email được gửi
            await delay(10000);

            if (!isRunning) {
                return;
            }

            // Gọi handleOTPVerification
            await handleOTPVerification(chatgptAccount);
            return;
        }

        // Kiểm tra URL auth.openai.com/about-you (B6: About You page - name & birthday)
        if (currentUrl.includes('auth.openai.com/about-you') || currentUrl.includes('/about-you')) {
            sendStatus('📝 On About You page, filling name and birthday...', 'info');

            await delay(2000);

            if (!isRunning) {
                return;
            }

            // Gọi handleAboutYou
            await handleAboutYou(chatgptAccount);
            return;
        }

        // Kiểm tra xem có form email trên trang (B3: Email input) - kiểm tra email trước
        const hasEmailInput = document.querySelector('input[type="email"], input[name*="email" i], input[id*="email" i], input[placeholder*="Email address" i], input[placeholder*="email" i]');

        // Kiểm tra xem có form password trên trang (B4: Password input) - chỉ kiểm tra nếu KHÔNG có email input
        let hasPasswordInput = null;
        if (!hasEmailInput) {
            const passwordSelectors = [
                'input[name="new-password"]',
                'input[id*="-new-password"]',
                'input[type="password"][placeholder="Password"]',
                'input[type="password"][name*="password" i]',
                'input[type="password"]'
            ];

            for (const selector of passwordSelectors) {
                hasPasswordInput = document.querySelector(selector);
                if (hasPasswordInput) {
                    console.log(`✅ Found password input with selector: ${selector}`);
                    break;
                }
            }

            // Nếu không tìm thấy bằng selector, thử tìm bằng type
            if (!hasPasswordInput) {
                const allInputs = Array.from(document.querySelectorAll('input'));
                hasPasswordInput = allInputs.find(input => input.type === 'password');
            }
        }

        // Kiểm tra xem đang ở bước nào - ưu tiên email trước
        if (hasEmailInput) {
            // B3: Form nhập email (có thể trong modal hoặc trang signup)
            await fillEmailAndContinue(chatgptAccount);
            return;
        } else if (hasPasswordInput) {
            // B4: Form nhập password (chỉ khi không có email input)
            sendStatus('✅ Found password form, filling...', 'success');
            await fillPassword(chatgptAccount);
            return;
        } else if (currentUrl.includes('chatgpt.com/veterans-claim')) {
            // Nếu đang ở trang veterans-claim, có thể đã đăng nhập rồi
            // Kiểm tra xem có thể chuyển sang verify không
            const isLoggedIn = document.body.innerText && (
                document.body.innerText.includes('New chat') ||
                document.body.innerText.includes('Xác minh tư cách đủ điều kiện') ||
                document.body.innerText.includes('Verify') ||
                !document.querySelector('a[href*="login"]')
            );
            
            if (isLoggedIn) {
                sendStatus('✅ Already logged in and on veterans page, starting verify...', 'info');
                // Mark as completed since already logged in
                chatgptAccount.signupCompleted = true;
                chrome.storage.local.set({ 'chatgpt-account': chatgptAccount });
                await delay(2000);
                await startVerificationLoop();
                return;
            } else {
                // Not logged in, go back to signup
                sendStatus('⚠️ Not logged in yet, redirecting to signup...', 'info');
                window.location.href = 'https://chatgpt.com';
                await delay(5000);
                await startSignupLoop();
                return;
            }
        } else if (currentUrl.includes('chatgpt.com/auth/signup') ||
            currentUrl.includes('chatgpt.com/signup') ||
            currentUrl.includes('chatgpt.com/register')) {
            // Đã ở trang signup nhưng chưa có form, thử tìm nút Sign up for free
            await clickSignUpButton();
            return;
        } else if (currentUrl.includes('chatgpt.com/auth/verify') ||
            currentUrl.includes('chatgpt.com/verify')) {
            // On OTP verification page (tạm thời không xử lý)
            sendStatus('⏸️ On OTP page, temporarily paused for debugging', 'info');
            return;
        } else if (currentUrl.includes('chatgpt.com')) {
            // B2: Trang ChatGPT (có thể là homepage hoặc trang khác), kiểm tra xem đã đăng nhập chưa
            // Nếu đã đăng nhập, chuyển sang veterans-claim
            // Nếu chưa, tìm nút Sign up for free
            const isLoggedIn = document.body.innerText && (
                document.body.innerText.includes('New chat') ||
                document.body.innerText.includes('New conversation') ||
                document.querySelector('textarea[placeholder*="Message"]') ||
                !document.querySelector('button:contains("Sign up")')
            );
            
            if (isLoggedIn) {
                sendStatus('✅ Already logged in, navigating to veterans-claim...', 'info');
                // Mark as completed since already logged in
                chatgptAccount.signupCompleted = true;
                chrome.storage.local.set({ 'chatgpt-account': chatgptAccount });
                window.location.href = 'https://chatgpt.com/veterans-claim';
                await delay(5000);
                await startVerificationLoop();
                return;
            } else {
                // Not logged in, start signup flow
                await clickSignUpButton();
                return;
            }
        } else {
            // Không phải trang ChatGPT, redirect
            window.location.href = 'https://chatgpt.com';
            await delay(5000);
            await startSignupLoop();
            return;
        }
    } catch (error) {
        if (!isRunning) {
            return;
        }

        console.error('❌ Error in signup loop:', error);
        const errorMessage = error?.message || String(error);
        sendStatus('❌ Error: ' + errorMessage, 'error');

        // Move to next account on error
        currentDataIndex++;
        stats.processed++;
        stats.failed++;
        updateStats();
        chrome.storage.local.set({
            'veterans-current-index': currentDataIndex
        });

        await delay(2000);
        await startSignupLoop();
    }
}

// B2: Tìm và click nút "Sign up for free"
async function clickSignUpButton() {
    if (!isRunning) {
        return;
    }

    sendStatus('🔍 Looking for Sign up for free button...', 'info');

    // Wait for page to load
    await delay(3000);

    if (!isRunning) {
        return;
    }

    try {
        // Kiểm tra xem đã có form email chưa (có thể modal đã mở)
        const hasEmailInput = document.querySelector('input[type="email"], input[name*="email" i], input[id*="email" i], input[placeholder*="Email address" i], input[placeholder*="email" i]');
        if (hasEmailInput) {
            await startSignupLoop();
            return;
        }

        // Tìm nút "Sign up for free" - thử nhiều cách
        let signUpButton = null;

        // Cách 1: Tìm theo text
        const allButtons = Array.from(document.querySelectorAll('button, a'));
        signUpButton = allButtons.find(btn => {
            const text = (btn.innerText || btn.textContent || '').toLowerCase();
            return text.includes('sign up for free') ||
                text.includes('sign up') ||
                (text.includes('sign') && text.includes('up') && text.includes('free'));
        });

        // Cách 2: Tìm theo selector
        if (!signUpButton) {
            const selectors = [
                'button:contains("Sign up for free")',
                'a:contains("Sign up for free")',
                '[href*="signup"]',
                '[href*="register"]'
            ];

            for (const selector of selectors) {
                try {
                    const elements = Array.from(document.querySelectorAll('button, a'));
                    signUpButton = elements.find(el => {
                        const text = (el.innerText || el.textContent || '').toLowerCase();
                        const href = el.href || '';
                        return text.includes('sign up for free') ||
                            (selector.includes('href') && (href.includes('signup') || href.includes('register')));
                    });
                    if (signUpButton) break;
                } catch (e) {
                    continue;
                }
            }
        }

        if (!signUpButton) {
            throw new Error('Sign up for free button not found');
        }

        sendStatus('✅ Found Sign up for free button, clicking...', 'success');

        // Click button
        signUpButton.click();
        sendStatus('✅ Clicked button, waiting for email form to appear...', 'success');
        await delay(2000);

        if (!isRunning) {
            return;
        }

        // Đợi form email xuất hiện (có thể là modal popup)
        let emailInput = null;
        let attempts = 0;
        const maxAttempts = 10;

        while (attempts < maxAttempts && !emailInput) {
            attempts++;
            emailInput = document.querySelector('input[type="email"], input[name*="email" i], input[id*="email" i], input[placeholder*="Email address" i], input[placeholder*="email" i]');

            if (emailInput) {
                break;
            }

            await delay(1000);

            if (!isRunning) {
                return;
            }
        }

        if (!emailInput) {
            throw new Error('Email form did not appear after clicking Sign up for free button');
        }

        // Form đã xuất hiện, tiếp tục với B3
        await delay(1000);
        await startSignupLoop();
    } catch (error) {
        console.error('❌ Error clicking Sign up button:', error);
        throw error;
    }
}

// B3: Điền email và nhấn Continue
async function fillEmailAndContinue(data) {
    if (!isRunning) {
        return;
    }

    sendStatus('📝 Filling email...', 'info');

    // Wait for page to load
    await delay(3000);

    if (!isRunning) {
        return;
    }

    try {
        // Tìm ô nhập email
        const emailSelectors = [
            'input[type="email"]',
            'input[name*="email" i]',
            'input[id*="email" i]',
            'input[placeholder*="email" i]',
            'input[placeholder*="Email address" i]',
            '#email',
            'input[aria-label*="email" i]'
        ];

        let emailInput = null;
        for (const selector of emailSelectors) {
            emailInput = document.querySelector(selector);
            if (emailInput) {
                break;
            }
        }

        if (!emailInput) {
            // Try to find by scanning all inputs
            const allInputs = Array.from(document.querySelectorAll('input'));
            emailInput = allInputs.find(input => {
                const type = input.type?.toLowerCase();
                const name = (input.name || '').toLowerCase();
                const id = (input.id || '').toLowerCase();
                const placeholder = (input.placeholder || '').toLowerCase();
                return type === 'email' ||
                    name.includes('email') ||
                    id.includes('email') ||
                    placeholder.includes('email');
            });
        }

        if (!emailInput) {
            throw new Error('Email input not found');
        }

        // Fill email
        emailInput.value = data.email;
        emailInput.dispatchEvent(new Event('input', { bubbles: true }));
        emailInput.dispatchEvent(new Event('change', { bubbles: true }));
        emailInput.dispatchEvent(new Event('blur', { bubbles: true }));
        sendStatus('✅ Email filled, looking for Continue button...', 'success');
        await delay(1000);

        if (!isRunning) {
            return;
        }

        // Tìm nút Continue - thử nhiều cách
        let continueButton = null;

        // Cách 1: Tìm theo class và type
        continueButton = document.querySelector('button.btn-primary[type="submit"]');

        // Cách 2: Tìm theo class chứa "btn-primary"
        if (!continueButton) {
            continueButton = document.querySelector('button[class*="btn-primary"][type="submit"]');
        }

        // Cách 3: Tìm theo type="submit"
        if (!continueButton) {
            continueButton = document.querySelector('button[type="submit"]');
        }

        // Cách 4: Tìm theo text "Continue"
        if (!continueButton) {
            const allButtons = Array.from(document.querySelectorAll('button'));
            continueButton = allButtons.find(btn => {
                const text = (btn.innerText || btn.textContent || '').toUpperCase().trim();
                return text === 'CONTINUE' || text.includes('CONTINUE');
            });
        }

        // Cách 5: Tìm button có class "btn" và text "Continue"
        if (!continueButton) {
            const btnElements = Array.from(document.querySelectorAll('button.btn, button[class*="btn"]'));
            continueButton = btnElements.find(btn => {
                const text = (btn.innerText || btn.textContent || '').toUpperCase().trim();
                return text === 'CONTINUE' || text.includes('CONTINUE');
            });
        }

        if (!continueButton) {
            throw new Error('Continue button not found');
        }

        // Kiểm tra xem nút có bị disabled không
        if (continueButton.disabled) {
            sendStatus('⚠️ Continue button is disabled, waiting...', 'info');

            // Đợi nút được enable
            let attempts = 0;
            const maxAttempts = 10;
            while (attempts < maxAttempts && continueButton.disabled) {
                attempts++;
                await delay(1000);
                continueButton = document.querySelector('button.btn-primary[type="submit"]') ||
                    document.querySelector('button[type="submit"]');
                if (!continueButton) {
                    const allButtons = Array.from(document.querySelectorAll('button'));
                    continueButton = allButtons.find(btn => {
                        const text = (btn.innerText || btn.textContent || '').toUpperCase().trim();
                        return text === 'CONTINUE' || text.includes('CONTINUE');
                    });
                }
                if (continueButton && !continueButton.disabled) {
                    break;
                }
            }

            if (!continueButton || continueButton.disabled) {
                throw new Error('Continue button still disabled after waiting');
            }
        }

        sendStatus('✅ Found Continue button, clicking...', 'success');
        await delay(500);

        // Click Continue
        try {
            continueButton.click();
        } catch (e) {
            continueButton.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
        }

        sendStatus('✅ Clicked Continue, waiting for page to change...', 'success');

        // Đợi động: đợi URL thay đổi hoặc password input xuất hiện
        const initialUrl = window.location.href;
        let passwordInput = null;
        let attempts = 0;
        const maxAttempts = 30;

        sendStatus('⏳ Waiting for page to change or password form to appear...', 'info');

        // Tìm password input ngay
        passwordInput = document.querySelector('input[name="new-password"]') ||
            document.querySelector('input[id*="-new-password"]') ||
            document.querySelector('input[type="password"][placeholder="Password"]') ||
            document.querySelector('input[type="password"]');

        if (!passwordInput) {
            const allInputs = Array.from(document.querySelectorAll('input'));
            passwordInput = allInputs.find(input => {
                const type = input.type === 'password';
                const name = (input.name || '').toLowerCase().includes('password');
                const id = (input.id || '').toLowerCase().includes('password');
                const placeholder = (input.placeholder || '').toLowerCase().includes('password');
                return type || name || id || placeholder;
            });
        }

        if (!passwordInput) {
            while (attempts < maxAttempts && !passwordInput && isRunning) {
                attempts++;

                const currentUrl = window.location.href;
                if (currentUrl !== initialUrl && attempts > 2) {
                    if (currentUrl.includes('auth.openai.com')) {
                        sendStatus('🔄 Redirected to auth.openai.com, waiting 5s...', 'info');
                        await delay(5000);
                        await startSignupLoop();
                        return;
                    }
                    sendStatus('✅ URL changed, looking for password input...', 'success');
                }

                passwordInput = document.querySelector('input[type="password"]') ||
                    document.querySelector('input[name="new-password"]') ||
                    document.querySelector('input[id*="-new-password"]') ||
                    document.querySelector('input[type="password"][placeholder*="Password" i]');

                if (!passwordInput) {
                    const currentInputs = Array.from(document.querySelectorAll('input'));
                    passwordInput = currentInputs.find(input => {
                        const type = input.type === 'password';
                        const name = (input.name || '').toLowerCase().includes('password');
                        const id = (input.id || '').toLowerCase().includes('password');
                        const placeholder = (input.placeholder || '').toLowerCase().includes('password');
                        return type || name || id || placeholder;
                    });
                }

                if (passwordInput) {
                    break;
                }

                await delay(1000);
            }
        }

        if (!isRunning) {
            return;
        }

        if (passwordInput) {
            sendStatus('✅ Đã tìm thấy form password, đang điền...', 'success');
            try {
                await fillPassword(data);
            } catch (error) {
                sendStatus('❌ Error filling password: ' + (error?.message || String(error)), 'error');
                throw error;
            }
        } else {
            sendStatus('⚠️ Password input not found, retrying...', 'info');
            setTimeout(async () => {
                try {
                    await startSignupLoop();
                } catch (error) {
                    sendStatus('❌ Error: ' + (error?.message || String(error)), 'error');
                }
            }, 100);
        }
    } catch (error) {
        console.error('❌ Error trong fillEmailAndContinue:', error);
        sendStatus('❌ Error filling email: ' + (error?.message || String(error)), 'error');
        throw error;
    }
}

// B4: Điền password và nhấn Continue
async function fillPassword(data) {
    if (!isRunning) {
        return;
    }

    sendStatus('📝 Filling password...', 'info');

    // Đợi một chút để đảm bảo form đã load (đã đợi 2s ở bước trước rồi)
    await delay(1000);

    if (!isRunning) {
        return;
    }

    try {
        // Tìm ô nhập password - thêm selectors cho auth.openai.com UI mới
        const passwordSelectors = [
            'input[name="new-password"]',  // Chính xác nhất từ HTML
            'input[id*="-new-password"]',  // ID có thể thay đổi nhưng luôn có "-new-password"
            'input[type="password"]',      // Selector đơn giản nhất - ưu tiên cao
            'input[type="password"][placeholder*="Password" i]',
            'input[type="password"][placeholder*="password" i]',
            'input[type="password"][name*="password" i]',
            'input[id*="password" i]',
            'input[placeholder*="Password" i]',
            '#password',
            'input[aria-label*="password" i]',
            'input[autocomplete="new-password"]',
            'input[autocomplete="current-password"]'
        ];

        let passwordInput = null;
        for (const selector of passwordSelectors) {
            try {
                passwordInput = document.querySelector(selector);
                if (passwordInput) {
                    break;
                }
            } catch (e) {
                continue;
            }
        }

        if (!passwordInput) {
            // Try to find by type
            const allInputs = Array.from(document.querySelectorAll('input'));
            passwordInput = allInputs.find(input => input.type === 'password');
        }

        if (!passwordInput) {
            throw new Error('Password input not found');
        }

        // Fill password
        passwordInput.value = data.password;
        passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
        passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
        passwordInput.dispatchEvent(new Event('blur', { bubbles: true }));
        sendStatus('✅ Password filled, looking for Continue button...', 'success');
        await delay(1000);

        if (!isRunning) {
            return;
        }

        // Tìm nút Continue - ưu tiên selector cho auth.openai.com
        let continueButton = null;

        // Cách 1: Tìm theo data-dd-action-name="Continue"
        continueButton = document.querySelector('button[data-dd-action-name="Continue"]');

        // Cách 2: Tìm theo class _primary_wetqs_99 và type="submit"
        if (!continueButton) {
            continueButton = document.querySelector('button._primary_wetqs_99[type="submit"]');
        }

        // Cách 3: Tìm theo class chứa "_primary" và type="submit"
        if (!continueButton) {
            continueButton = document.querySelector('button[class*="_primary"][type="submit"]');
        }

        // Cách 4: Tìm theo type="submit"
        if (!continueButton) {
            continueButton = document.querySelector('button[type="submit"]');
        }

        // Cách 5: Tìm theo text "Continue"
        if (!continueButton) {
            const allButtons = Array.from(document.querySelectorAll('button'));
            continueButton = allButtons.find(btn => {
                const text = (btn.innerText || btn.textContent || '').toUpperCase().trim();
                return text === 'CONTINUE' || text.includes('CONTINUE');
            });
        }

        if (!continueButton) {
            throw new Error('Continue button not found');
        }

        // Kiểm tra xem nút có bị disabled không
        if (continueButton.disabled || continueButton.getAttribute('aria-disabled') === 'true') {
            sendStatus('⚠️ Continue button is disabled, waiting...', 'info');

            // Đợi nút được enable
            let attempts = 0;
            const maxAttempts = 10;
            while (attempts < maxAttempts && (continueButton.disabled || continueButton.getAttribute('aria-disabled') === 'true')) {
                attempts++;
                await delay(1000);
                continueButton = document.querySelector('button[data-dd-action-name="Continue"]') ||
                    document.querySelector('button._primary_wetqs_99[type="submit"]') ||
                    document.querySelector('button[type="submit"]');
                if (!continueButton) {
                    const allButtons = Array.from(document.querySelectorAll('button'));
                    continueButton = allButtons.find(btn => {
                        const text = (btn.innerText || btn.textContent || '').toUpperCase().trim();
                        return text === 'CONTINUE' || text.includes('CONTINUE');
                    });
                }
                if (continueButton && !continueButton.disabled && continueButton.getAttribute('aria-disabled') !== 'true') {
                    break;
                }
            }

            if (!continueButton || continueButton.disabled || continueButton.getAttribute('aria-disabled') === 'true') {
                throw new Error('Continue button still disabled after waiting');
            }
        }

        sendStatus('✅ Found Continue button, clicking...', 'success');
        await delay(500);

        // Click Continue
        try {
            continueButton.click();
        } catch (e) {
            continueButton.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
        }

        sendStatus('✅ Clicked Continue, waiting for page to load...', 'success');
        await delay(3000);

        if (isRunning) {
            await startSignupLoop();
        }
    } catch (error) {
        console.error('❌ Error filling password:', error);
        throw error;
    }
}

// B6: Handle About You page - fill name and birthday
async function handleAboutYou(data) {
    if (!isRunning) {
        return;
    }

    sendStatus('📝 Filling personal information...', 'info');

    try {
        // Generate name from email (first 7 characters before @)
        const emailPrefix = data.email.split('@')[0];
        const fullName = emailPrefix.substring(0, Math.min(emailPrefix.length, 10)); // Use up to 10 chars

        // Generate random birthday - use 10-12 for month, 10-28 for day to ensure 2 digits
        const year = Math.floor(Math.random() * (1980 - 1960 + 1)) + 1960;
        const month = Math.floor(Math.random() * 3) + 10; // 10, 11, or 12
        const day = Math.floor(Math.random() * 19) + 10; // 10 to 28

        // Fill Full Name input
        const nameInput = document.querySelector('input[name="name"]') ||
            document.querySelector('input[id*="-name"]') ||
            document.querySelector('input[placeholder*="Full name" i]') ||
            document.querySelector('input[placeholder*="name" i]');

        if (nameInput) {
            nameInput.value = fullName;
            nameInput.dispatchEvent(new Event('input', { bubbles: true }));
            nameInput.dispatchEvent(new Event('change', { bubbles: true }));
            sendStatus(`✅ Name filled: ${fullName}`, 'success');
        }

        await delay(2000);

        // Fill Birthday - React Aria DateField has separate segments for month, day, year
        // Need to fill each segment individually: month (2 digits), day (2 digits), year (4 digits)
        
        const monthSegment = document.querySelector('[data-type="month"][role="spinbutton"]');
        const daySegment = document.querySelector('[data-type="day"][role="spinbutton"]');
        const yearSegment = document.querySelector('[data-type="year"][role="spinbutton"]');

        // Helper function to fill a segment with value by typing each digit
        async function fillSegment(segment, value) {
            if (!segment) return false;

            // Focus on segment
            segment.focus();
            await delay(150);

            // Click to ensure focus
            segment.click();
            await delay(150);

            // Clear existing content by selecting all and deleting
            segment.textContent = '';
            segment.innerText = '';
            
            // Type each digit one by one to simulate real user input
            for (let i = 0; i < value.length; i++) {
                const digit = value[i];
                
                // Method 1: beforeinput event (React Aria listens to this)
                const beforeInputEvent = new InputEvent('beforeinput', {
                    inputType: 'insertText',
                    data: digit,
                    bubbles: true,
                    cancelable: true,
                    composed: true
                });
                const beforeInputAllowed = segment.dispatchEvent(beforeInputEvent);
                
                if (beforeInputAllowed) {
                    // Method 2: Update text content
                    segment.textContent = (segment.textContent || '') + digit;
                    segment.innerText = (segment.innerText || '') + digit;
                    
                    // Method 3: input event
                    const inputEvent = new InputEvent('input', {
                        inputType: 'insertText',
                        data: digit,
                        bubbles: true,
                        cancelable: true,
                        composed: true
                    });
                    segment.dispatchEvent(inputEvent);
                    
                    // Method 4: Keyboard events for compatibility
                    const keydownEvent = new KeyboardEvent('keydown', {
                        key: digit,
                        code: `Digit${digit}`,
                        keyCode: 48 + parseInt(digit),
                        which: 48 + parseInt(digit),
                        bubbles: true,
                        cancelable: true,
                        composed: true
                    });
                    segment.dispatchEvent(keydownEvent);
                    
                    const keypressEvent = new KeyboardEvent('keypress', {
                        key: digit,
                        code: `Digit${digit}`,
                        keyCode: 48 + parseInt(digit),
                        which: 48 + parseInt(digit),
                        bubbles: true,
                        cancelable: true,
                        composed: true
                    });
                    segment.dispatchEvent(keypressEvent);
                    
                    const keyupEvent = new KeyboardEvent('keyup', {
                        key: digit,
                        code: `Digit${digit}`,
                        keyCode: 48 + parseInt(digit),
                        which: 48 + parseInt(digit),
                        bubbles: true,
                        cancelable: true,
                        composed: true
                    });
                    segment.dispatchEvent(keyupEvent);
                }
                
                await delay(100); // Delay between digits
            }

            // Dispatch change event to finalize
            const changeEvent = new Event('change', { bubbles: true, cancelable: true });
            segment.dispatchEvent(changeEvent);
            
            // Blur to finalize
            await delay(200);
            segment.blur();
            await delay(100);

            return true;
        }

        // Check for error
        function hasError() {
            return document.querySelector('._error_afhkj_109') !== null ||
                document.querySelector('[data-invalid="true"]') !== null ||
                document.querySelector('[aria-describedby*="error"]') !== null;
        }

        if (monthSegment && daySegment && yearSegment) {
            const monthStr = String(month).padStart(2, '0');
            const dayStr = String(day).padStart(2, '0');
            const yearStr = String(year);

            let attempts = 0;
            const maxAttempts = 3;

            while (attempts < maxAttempts) {
                attempts++;

                // Clear any previous errors by clicking outside
                document.body.click();
                await delay(200);

                // Fill month segment (2 digits)
                await fillSegment(monthSegment, monthStr);
                await delay(300);

                // Fill day segment (2 digits)
                await fillSegment(daySegment, dayStr);
                await delay(300);

                // Fill year segment (4 digits)
                await fillSegment(yearSegment, yearStr);
                await delay(500);

                // Check for error
                await delay(500);
                if (!hasError()) {
                    sendStatus(`✅ Birthday filled: ${month}/${day}/${year}`, 'success');
                    break;
                } else {
                    if (attempts < maxAttempts) {
                        sendStatus(`⚠️ Birthday error, retrying attempt ${attempts + 1}...`, 'info');
                        await delay(500);
                    } else {
                        sendStatus(`❌ Failed to fill birthday after ${maxAttempts} attempts`, 'error');
                    }
                }
            }
        }

        await delay(2000);

        if (!isRunning) {
            return;
        }

        // Click Continue button
        const continueButton = document.querySelector('button[data-dd-action-name="Continue"]') ||
            document.querySelector('button[type="submit"]') ||
            document.querySelector('button._primary_wetqs_99');

        if (continueButton) {
            // Lưu URL hiện tại để so sánh sau
            const initialUrl = window.location.href;
            
            continueButton.click();
            sendStatus('✅ Clicked Continue, waiting for page to change...', 'info');
            
            // Đợi và kiểm tra xem trang có chuyển không hoặc có xuất hiện trang survey không
            let surveyFound = false;
            let urlChanged = false;
            let attempts = 0;
            const maxAttempts = 20; // Tối đa 10 giây (20 * 500ms)
            
            while (attempts < maxAttempts && !surveyFound && isRunning) {
                attempts++;
                await delay(500);
                
                // Kiểm tra URL có thay đổi không
                const currentUrl = window.location.href;
                if (currentUrl !== initialUrl) {
                    urlChanged = true;
                }
                
                // Kiểm tra xem có trang survey "What brings you to ChatGPT?" không
                // Kiểm tra bằng cách tìm text cụ thể trên trang
                const pageText = document.body.innerText || document.body.textContent || '';
                const pageTextLower = pageText.toLowerCase();
                
                // Tìm câu hỏi survey
                const hasSurveyQuestion = pageTextLower.includes('what brings you to chatgpt');
                
                // Tìm các option của survey (School, Work, Personal tasks, Fun and entertainment, Other)
                const hasSchool = pageTextLower.includes('school');
                const hasWork = pageTextLower.includes('work') && !pageTextLower.includes('personal tasks'); // Tránh match "Personal tasks"
                const hasPersonalTasks = pageTextLower.includes('personal tasks');
                const hasFunEntertainment = pageTextLower.includes('fun and entertainment') || pageTextLower.includes('fun & entertainment');
                const hasOther = pageTextLower.includes('other') && (pageTextLower.includes('school') || pageTextLower.includes('work'));
                
                // Cần có ít nhất 3 trong số các option này để xác định là trang survey
                const surveyOptionsCount = [hasSchool, hasWork, hasPersonalTasks, hasFunEntertainment, hasOther].filter(Boolean).length;
                const hasSurveyOptions = surveyOptionsCount >= 3;
                
                // Tìm nút "Next" và "Skip" (đặc trưng của trang survey)
                const hasNextButton = Array.from(document.querySelectorAll('button')).some(btn => {
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    return text === 'next';
                });
                const hasSkipLink = Array.from(document.querySelectorAll('a, button')).some(el => {
                    const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                    return text === 'skip';
                });
                
                if (hasSurveyQuestion || (hasSurveyOptions && hasNextButton && hasSkipLink)) {
                    surveyFound = true;
                    sendStatus('✅ Signup successful! Reached survey page.', 'success');
                    break;
                }
                
                // Log mỗi 5 lần thử
                if (attempts % 5 === 0) {
                    sendStatus(`⏳ Checking signup result... (${attempts}/${maxAttempts})`, 'info');
                }
            }
            
            if (!isRunning) {
                return;
            }
            
            // Kiểm tra kết quả
            if (surveyFound) {
                // Đăng ký thành công - đã đến trang survey
                sendStatus('✅ Signup successful! Skipping survey and moving to verify...', 'success');
                
                // Try to skip survey if possible
                try {
                    const skipButton = Array.from(document.querySelectorAll('a, button')).find(el => {
                        const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                        return text === 'skip';
                    });
                    if (skipButton) {
                        skipButton.click();
                        await delay(2000);
                    }
                } catch (e) {
                    console.log('Could not skip survey, continuing...');
                }
                
                // Mark signup as completed
                chatgptAccount.signupCompleted = true;
                chrome.storage.local.set({ 'chatgpt-account': chatgptAccount });
                
                // Navigate to veterans-claim page and start verify
                sendStatus('🌐 Navigating to veterans-claim page...', 'info');
                window.location.href = 'https://chatgpt.com/veterans-claim';
                await delay(5000);
                
                // Start verify process
                await startVerificationLoop();
                return;
            } else if (urlChanged) {
                // URL đã thay đổi nhưng chưa thấy survey, có thể đang load hoặc chuyển trang khác
                sendStatus('⚠️ Page changed, checking...', 'info');
                await delay(2000);
                await startSignupLoop();
            } else {
                // Không chuyển trang sau khi click Continue -> Lỗi
                sendStatus('❌ Error: Page did not change after filling information', 'error');
                
                // Đánh dấu thất bại
                stats.processed++;
                stats.failed++;
                updateStats();

                // Move to next account
                currentDataIndex++;
                chrome.storage.local.set({
                    'chatgpt-signup-current-index': currentDataIndex,
                    'chatgpt-signup-stats': stats
                });

                // Continue with next account after delay
                await delay(3000);
                await startSignupLoop();
            }
        } else {
            throw new Error('Continue button not found');
        }

    } catch (error) {
        console.error('❌ Error in handleAboutYou:', error);
        sendStatus('❌ Error filling information: ' + error.message, 'error');
        throw error;
    }
}

async function handleOTPVerification(data) {
    if (!isRunning) {
        return;
    }

    sendStatus('📧 Getting OTP code from email...', 'info');

    try {
        // Kiểm tra xem có refresh_token và client_id không
        if (!data.refreshToken || !data.clientId) {
            throw new Error('Thiếu refresh_token hoặc client_id. Format: email-chatgpt|pass-chatgpt|email-login|pass-email|refresh_token|client_id');
        }

        // Gọi API dongvanfb.net để đọc email
        const EMAIL_API_URL = 'https://tools.dongvanfb.net/api/get_messages_oauth2';

        const payload = {
            email: data.emailLogin,  // Sử dụng email-login để đọc email
            refresh_token: data.refreshToken,
            client_id: data.clientId
        };

        sendStatus('📡 Reading email from API...', 'info');

        const response = await fetch(EMAIL_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();

        if (!result.status || !result.messages) {
            throw new Error(`API trả về lỗi: ${result.error || result.code || 'Unknown error'}`);
        }

        let messages = result.messages || [];

        if (messages.length === 0) {
            throw new Error('No emails found');
        }

        // SORT messages by date - newest first
        messages = messages.sort((a, b) => {
            const dateA = new Date(a.date || 0);
            const dateB = new Date(b.date || 0);
            return dateB - dateA;
        });

        // Tìm email mới nhất có subject "Your ChatGPT code is XXXXXX"
        let otpCode = null;
        let foundEmail = null;

        for (const msg of messages) {
            const subject = msg.subject || '';
            const subjectLower = subject.toLowerCase();

            // Tìm email có subject chứa "your chatgpt code is"
            if (subjectLower.includes('your chatgpt code is') || subjectLower.includes('chatgpt code')) {
                foundEmail = msg;

                // Extract OTP từ SUBJECT trước (vì subject rõ ràng hơn): "Your ChatGPT code is 679436"
                const subjectOtpMatch = subject.match(/code\s*(?:is\s*)?(\d{6})/i);
                if (subjectOtpMatch) {
                    otpCode = subjectOtpMatch[1];
                    break;
                }

                // Fallback: tìm bất kỳ 6 số trong subject
                const subjectMatch = subject.match(/(\d{6})/);
                if (subjectMatch) {
                    otpCode = subjectMatch[1];
                    break;
                }

                // Nếu không có trong subject, thử body
                const body = msg.message || msg.html_body || '';
                const bodyMatch = body.match(/code\s*(?:is\s*)?(\d{6})/i) || body.match(/(\d{6})/);
                if (bodyMatch) {
                    otpCode = bodyMatch[1];
                    break;
                }
            }
        }

        if (!otpCode) {
            // Nếu không tìm thấy, thử tìm bất kỳ email nào có mã 6 số
            for (const msg of messages) {
                const body = msg.message || msg.html_body || '';
                const subject = (msg.subject || '').toLowerCase();

                // Tìm mã 6 số trong body hoặc subject
                const otpMatch = (body + ' ' + subject).match(/\b(\d{6})\b/);
                if (otpMatch) {
                    otpCode = otpMatch[1];
                    foundEmail = msg;
                    break;
                }
            }
        }

        if (!otpCode) {
            throw new Error('6-digit OTP code not found in email. Subject: ' + (foundEmail?.subject || 'N/A'));
        }

        sendStatus('✅ Received OTP code, filling...', 'success');
        await delay(1000);

        if (!isRunning) {
            return;
        }

        // Find OTP input - try multiple selectors (auth.openai.com specific first)
        const otpSelectors = [
            'input[name="code"]',              // auth.openai.com specific
            'input[id*="-code"]',              // auth.openai.com: id="_r_4_-code"
            'input[type="text"][name*="code"]',
            'input[type="text"][name*="otp"]',
            'input[type="text"][name*="verification"]',
            'input[id*="code"]',
            'input[id*="otp"]',
            'input[id*="verification"]',
            'input[placeholder*="code" i]',
            'input[placeholder*="Code" i]',
            'input[placeholder*="otp" i]',
            'input[placeholder*="mã" i]',
            '#code',
            '#otp',
            '#verification-code'
        ];

        let otpInput = null;
        for (const selector of otpSelectors) {
            try {
                otpInput = document.querySelector(selector);
                if (otpInput) {
                    break;
                }
            } catch (e) {
                continue;
            }
        }

        // If not found, try to find by looking for input with 6 digits pattern
        if (!otpInput) {
            const allInputs = Array.from(document.querySelectorAll('input[type="text"], input[type="number"]'));
            otpInput = allInputs.find(input => {
                const maxLength = input.maxLength || input.getAttribute('maxlength');
                const placeholder = (input.placeholder || '').toLowerCase();
                return (maxLength && parseInt(maxLength) <= 10) ||
                    placeholder.includes('code') ||
                    placeholder.includes('otp') ||
                    placeholder.includes('mã');
            });
        }

        if (!otpInput) {
            throw new Error('OTP input not found');
        }

        // Fill OTP
        otpInput.value = otpCode;
        otpInput.dispatchEvent(new Event('input', { bubbles: true }));
        otpInput.dispatchEvent(new Event('change', { bubbles: true }));
        otpInput.dispatchEvent(new Event('blur', { bubbles: true }));
        await delay(1000);

        if (!isRunning) {
            return;
        }

        // Find and click verify/submit button
        const verifyButtonSelectors = [
            'button[type="submit"]',
            'button:has-text("Verify")',
            'button:has-text("Xác thực")',
            'button:has-text("Continue")',
            'button:has-text("Tiếp tục")',
            'button.btn-primary',
            'button[class*="primary"]'
        ];

        let verifyButton = null;
        for (const selector of verifyButtonSelectors) {
            try {
                verifyButton = document.querySelector(selector);
                if (verifyButton) {
                    const text = (verifyButton.innerText || verifyButton.textContent || '').toLowerCase();
                    if (text.includes('verify') ||
                        text.includes('xác thực') ||
                        text.includes('continue') ||
                        text.includes('tiếp tục') ||
                        selector.includes('submit') ||
                        selector.includes('primary')) {
                        break;
                    }
                }
            } catch (e) {
                // Continue to next selector
            }
        }

        // If not found, try to find by text
        if (!verifyButton) {
            const allButtons = Array.from(document.querySelectorAll('button'));
            verifyButton = allButtons.find(btn => {
                const text = (btn.innerText || btn.textContent || '').toLowerCase();
                return text.includes('verify') ||
                    text.includes('xác thực') ||
                    text.includes('continue') ||
                    text.includes('tiếp tục') ||
                    btn.type === 'submit';
            });
        }

        if (!verifyButton) {
            throw new Error('OTP verify button not found');
        }

        // Click verify button
        verifyButton.click();
        sendStatus('✅ OTP code submitted, waiting for result...', 'success');
        await delay(5000);

        if (!isRunning) {
            return;
        }

        // Check if signup was successful
        const currentUrl = window.location.href;
        if (currentUrl.includes('chatgpt.com') &&
            !currentUrl.includes('signup') &&
            !currentUrl.includes('verify') &&
            !currentUrl.includes('auth')) {
            // Success - on main ChatGPT page
            sendStatus('✅ Signup successful! Moving to verify...', 'success');

            // Mark signup as completed
            chatgptAccount.signupCompleted = true;
            chrome.storage.local.set({ 'chatgpt-account': chatgptAccount });
            
            // Navigate to veterans-claim page and start verify
            sendStatus('🌐 Navigating to veterans-claim page...', 'info');
            window.location.href = 'https://chatgpt.com/veterans-claim';
            await delay(5000);
            
            // Start verify process
            await startVerificationLoop();
            return;
        } else {
            // Check for error messages
            const errorMessages = document.querySelectorAll('.error, .alert, [role="alert"]');
            if (errorMessages.length > 0) {
                const errorText = Array.from(errorMessages)
                    .map(el => el.innerText || el.textContent)
                    .join(' ');
                throw new Error('Verification error: ' + errorText);
            }

            // Continue loop to check next state
            await delay(3000);
            await startSignupLoop();
        }
    } catch (error) {
        console.error('❌ Error handling OTP verification:', error);
        throw error;
    }
}

// Helper functions
function waitForElement(selector, timeout = 10000) {
    return new Promise((resolve, reject) => {
        if (!isRunning) {
            reject('Signup stopped');
            return;
        }

        const check = () => {
            if (!isRunning) {
                observer?.disconnect();
                reject('Signup stopped');
                return false;
            }

            const element = document.querySelector(selector);
            if (element) {
                resolve(element);
                return true;
            }
            return false;
        };

        if (check()) {
            return;
        }

        const observer = new MutationObserver(() => {
            if (check()) {
                observer.disconnect();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true
        });

        const checkInterval = setInterval(() => {
            if (!isRunning) {
                clearInterval(checkInterval);
                observer.disconnect();
                reject('Signup stopped');
            }
        }, 500);

        setTimeout(() => {
            clearInterval(checkInterval);
            observer.disconnect();
            reject('Timeout for: ' + selector);
        }, timeout);
    });
}

function waitForUrlChange(contains, timeout = 15000) {
    return new Promise((resolve) => {
        if (!isRunning) {
            resolve(false);
            return;
        }

        // Support both string and array for compatibility
        const checkUrl = () => {
            const currentUrl = window.location.href.toLowerCase();
            if (Array.isArray(contains)) {
                return contains.some(term => currentUrl.includes(term.toLowerCase()));
            } else {
                return currentUrl.includes(contains.toLowerCase());
            }
        };

        if (checkUrl()) {
            resolve(true);
            return;
        }

        const checkInterval = setInterval(() => {
            if (!isRunning) {
                clearInterval(checkInterval);
                resolve(false);
                return;
            }

            if (checkUrl()) {
                clearInterval(checkInterval);
                resolve(true);
            }
        }, 500);

        setTimeout(() => {
            clearInterval(checkInterval);
            resolve(false);
        }, timeout);
    });
}

function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function sendStatus(message, type = 'info') {
    chrome.storage.local.set({
        'veterans-status': {
            message: message,
            type: type,
            timestamp: Date.now()
        }
    });
}

function updateStats() {
    chrome.storage.local.set({
        'veterans-stats': stats
    });
}

function updateUIOnStop() {
    // UI updates are handled by side panel via storage changes
}

function removeProcessedData(keepRunning = true) {
    // Remove the current data from array and update storage
    // keepRunning: if false, don't update 'veterans-is-running' (used when stopping after verified)
    if (currentDataIndex < dataArray.length) {
        const processedData = dataArray[currentDataIndex];
        dataArray.splice(currentDataIndex, 1);

        // Rebuild data list string from remaining data
        const updatedDataList = dataArray
            .map((data) => data.original)
            .join('\n');

        // Use atomic operation to prevent race condition when multiple browsers run
        chrome.storage.local.get(['veterans-data-lock'], (lockResult) => {
            // Simple lock mechanism - wait if locked
            if (lockResult['veterans-data-lock']) {
                setTimeout(() => removeProcessedData(keepRunning), 100);
                return;
            }

            // Set lock
            chrome.storage.local.set({ 'veterans-data-lock': true }, () => {
                // Prepare storage update object
                const storageUpdate = {
                    'veterans-data-array': dataArray,
                    'veterans-data-list': updatedDataList,
                    'veterans-current-index': currentDataIndex
                };
                
                // Only update 'veterans-is-running' if keepRunning is true
                if (keepRunning) {
                    storageUpdate['veterans-is-running'] = true;
                }
                
                // Update storage with new array and updated data list
                chrome.storage.local.set(
                    storageUpdate,
                    () => {
                        // Release lock after 500ms
                        setTimeout(() => {
                            chrome.storage.local.remove('veterans-data-lock');
                        }, 500);
                    }
                );
            });
        });

        console.log('🗑️ Removed processed data:', processedData.original);
        console.log('💾 Updated data list saved to storage');
    }
}

// ============================================
// VERIFICATION FUNCTIONS (from veterans verify)
// ============================================

async function startVerificationLoop() {
    // Check if stopped - FORCE STOP check
    if (!isRunning) {
        console.log('⏹️ Tool stopped, exiting verification loop');
        return;
    }

    if (currentDataIndex >= dataArray.length) {
        isRunning = false;
        chrome.storage.local.set({ 'veterans-is-running': false });
        sendStatus('✅ All data processed', 'success');
        return;
    }

    const currentData = dataArray[currentDataIndex];
    mailRetryCount = 0; // Reset mail retry count for new data
    currentEmail = ''; // Reset email for new data (will be auto-generated)
    
    // Calculate the correct position
    const originalTotal = stats.processed + dataArray.length;
    const currentPosition = stats.processed + 1;
    
    sendStatus(
        `🔄 Verifying ${currentPosition}/${originalTotal}: ${currentData.first} ${currentData.last}`,
        'info'
    );
    updateStats();

    // Save current state
    chrome.storage.local.set({
        'veterans-current-index': currentDataIndex,
        'veterans-is-running': true
    });

    try {
        // Check current URL
        const currentUrl = window.location.href;
        console.log('📍 Current URL:', currentUrl);
        
        // Check for sourcesUnavailable error in URL
        if (currentUrl.includes('sourcesUnavailable') || currentUrl.includes('Error sourcesUnavailable')) {
            console.log('🚫 sourcesUnavailable error detected in URL, stopping tool...');
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            sendStatus(
                '🚫 VPN Error: sourcesUnavailable detected. Please change VPN and restart.',
                'error'
            );
            return;
        }

        if (currentUrl.includes('chatgpt.com/veterans-claim')) {
            // Step 1: Click verify button
            console.log('🔍 On ChatGPT page, clicking verify button...');
            await clickVerifyButton();
        } else if (currentUrl.includes('services.sheerid.com/verify')) {
            // Step 2: Check if we're on verification page
            console.log('🔍 On SheerID page, checking form...');
            // Auto-generate email if not already set
            if (!currentEmail) {
                console.log('📧 Generating new email...');
                await generateNewEmail();
            }
            console.log('📝 Starting to fill form...');
            await checkAndFillForm();
        } else {
            // Navigate to start page
            console.log('🌐 Navigating to ChatGPT page...');
            window.location.href = 'https://chatgpt.com/veterans-claim';
            await delay(5000);
            await startVerificationLoop();
            return;
        }
    } catch (error) {
        // Check if stopped before processing error
        if (!isRunning) {
            console.log('⏹️ Tool stopped during error handling, exiting');
            return;
        }
        
        console.error('❌ Error in verification loop:', error);
        
        // Extract error message
        let errorMessage = 'Unknown error';
        if (error) {
            if (typeof error === 'string') {
                errorMessage = error;
            } else if (error.message) {
                errorMessage = error.message;
            } else {
                errorMessage = String(error);
            }
        }
        
        // Check if it's a Status-related error (CRITICAL - must stop)
        const isStatusError = errorMessage.toLowerCase().includes('status') || 
                             errorMessage.toLowerCase().includes('không tìm thấy');
        
        // Status errors are critical - stop tool immediately
        if (isStatusError) {
            console.log('🚫 Critical Status error detected in verification loop, stopping tool...');
            const finalStatusMsg = errorMessage.toLowerCase().includes('❌') 
                ? errorMessage 
                : '❌ Lỗi nghiêm trọng: ' + errorMessage;
            sendStatus(finalStatusMsg, 'error');
            await delay(100);
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            return;
        }
        
        // For other errors, stop tool
        sendStatus('❌ Error: ' + errorMessage, 'error');
        isRunning = false;
        chrome.storage.local.set({ 'veterans-is-running': false });
        updateUIOnStop();
        return;
    }
}

async function generateNewEmail() {
    if (!isRunning) {
        console.log('⏹️ Tool stopped, exiting generateNewEmail');
        return;
    }
    
    try {
        sendStatus('📧 Generating new email...', 'info');

        // Get random domains
        const domainsResponse = await fetch(
            'https://tinyhost.shop/api/random-domains/?limit=10'
        );
        if (!domainsResponse.ok) {
            throw new Error('Failed to fetch domains');
        }

        const domainsData = await domainsResponse.json();
        const domains = domainsData.domains || [];

        if (domains.length === 0) {
            throw new Error('No domains available');
        }

        // Filter out blocked domains
        const blockedDomains = ['tempmail.com', 'guerrillamail.com'];
        const filteredDomains = domains.filter(
            (domain) =>
                !blockedDomains.some((blocked) => domain.endsWith(blocked))
        );

        if (filteredDomains.length === 0) {
            throw new Error('No valid domains available');
        }

        // Pick random domain
        const domain =
            filteredDomains[Math.floor(Math.random() * filteredDomains.length)];

        // Generate random username
        const username = generateRandomString(16);
        const email = `${username}@${domain}`;

        // Set current email
        currentEmail = email;

        // Save to localStorage
        localStorage.setItem('veterans-saved-email', email);
        localStorage.setItem('veterans-email-domain', domain);
        localStorage.setItem('veterans-email-username', username);

        // Save to chrome.storage.local for side panel
        chrome.storage.local.set({ 'veterans-saved-email': email });

        sendStatus('✅ Email generated: ' + email, 'success');
    } catch (error) {
        console.error('Error generating email:', error);
        const errorMsg = error && error.message ? error.message : 'Unknown error';
        sendStatus('❌ Failed to generate email: ' + errorMsg, 'error');
        throw error;
    }
}

function generateRandomString(length = 12) {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

async function clickVerifyButton() {
    if (!isRunning) {
        console.log('⏹️ Tool stopped, exiting clickVerifyButton');
        return;
    }
    
    sendStatus('🔍 Looking for verify button...', 'info');
    await delay(2000);
    
    if (!isRunning) return;
    
    let button = null;
    let attempts = 0;
    const maxAttempts = 10;

    while (attempts < maxAttempts && !button) {
        attempts++;
        const buttons = document.querySelectorAll('button.btn-primary, button[class*="btn-primary"]');
        
        for (let btn of buttons) {
            const buttonText = btn.innerText || btn.textContent || '';
            if (buttonText.includes('Xác minh tư cách đủ điều kiện') ||
                buttonText.includes('Xác minh') ||
                buttonText.includes('Verify')) {
                if (btn.offsetParent !== null && !btn.disabled) {
                    button = btn;
                    break;
                }
            }
        }
        if (!button) await delay(1000);
    }

    if (!button) {
        const allButtons = Array.from(document.querySelectorAll('button'));
        button = allButtons.find((btn) => {
            const text = btn.innerText || btn.textContent || '';
            return text.includes('Xác minh') || text.includes('Verify');
        });
    }

    if (!button) {
        throw new Error('Verify button not found');
    }

    await delay(1000);
    if (!isRunning) return;

    button.click();
    sendStatus('✅ Clicked verify button', 'success');
    await delay(3000);
    
    if (!isRunning) return;
    
    const urlChanged = await waitForUrlChange('services.sheerid.com', 15000);
    
    if (!isRunning || !urlChanged) return;
    
    await delay(3000);
    if (!isRunning) return;
    
    await generateNewEmail();
    if (!isRunning) return;
    
    await delay(1000);
    if (!isRunning) return;
    
    await checkAndFillForm();
}

async function checkAndFillForm() {
    if (!isRunning) {
        console.log('⏹️ Tool stopped, exiting checkAndFillForm');
        return;
    }
    
    sendStatus('🔍 Checking verification page...', 'info');
    await delay(3000);
    
    if (!isRunning) return;
    
    const currentUrl = window.location.href;
    if (currentUrl.includes('sourcesUnavailable') || currentUrl.includes('Error sourcesUnavailable')) {
        isRunning = false;
        chrome.storage.local.set({ 'veterans-is-running': false });
        updateUIOnStop();
        sendStatus('🚫 VPN Error: sourcesUnavailable detected. Please change VPN and restart.', 'error');
        return;
    }

    try {
        const errorDiv = document.querySelector('.sid-error-msg');
        if (errorDiv) {
            const errorText = errorDiv.innerText || errorDiv.textContent || '';
            
            if (errorText.includes('We are unable to verify you at this time') ||
                errorText.includes('unable to verify you') ||
                errorText.includes('contact SheerID support') ||
                errorText.includes("It looks like we're having difficulty verifying you") ||
                errorText.includes('having difficulty verifying') ||
                errorText.includes('sourcesUnavailable') ||
                errorText.toLowerCase().includes('sources unavailable')) {
                isRunning = false;
                chrome.storage.local.set({ 'veterans-is-running': false });
                updateUIOnStop();
                sendStatus('🚫 VPN Error: Unable to verify. Please change VPN and restart.', 'error');
                return;
            }

            if (errorText.includes('Not approved')) {
                if (currentDataIndex + 1 >= dataArray.length) {
                    isRunning = false;
                    chrome.storage.local.set({ 'veterans-is-running': false });
                    updateUIOnStop();
                    sendStatus('❌ All data failed, no more to try', 'error');
                    return;
                }

                removeProcessedData();
                stats.processed++;
                stats.failed++;
                updateStats();
                chrome.storage.local.set({
                    'veterans-current-index': currentDataIndex,
                    'veterans-is-running': true
                });

                const originalTotal = stats.processed + dataArray.length;
                const nextPosition = stats.processed + 1;
                sendStatus(`🔄 Trying next data: ${nextPosition}/${originalTotal}`, 'info');

                await delay(2000);
                if (!isRunning) return;
                
                window.location.href = 'https://chatgpt.com/veterans-claim';
                await delay(5000);
                if (!isRunning) return;
                
                await startVerificationLoop();
                return;
            }
        }

        let heading = null;
        let headingText = '';

        for (let i = 0; i < 5; i++) {
            try {
                heading = await waitForElement('h1', 5000);
                if (heading) {
                    headingText = heading.innerText || heading.textContent || '';
                    if (headingText) break;
                }
            } catch (e) {
                await delay(1000);
            }
        }

        if (!heading || !headingText) {
            const bodyText = document.body.innerText || document.body.textContent || '';

            if (bodyText.includes('We are unable to verify you at this time') ||
                bodyText.includes('unable to verify you') ||
                bodyText.includes('sourcesUnavailable') ||
                bodyText.toLowerCase().includes('sources unavailable')) {
                isRunning = false;
                chrome.storage.local.set({ 'veterans-is-running': false });
                updateUIOnStop();
                sendStatus('🚫 VPN Error: Unable to verify. Please change VPN and restart.', 'error');
                return;
            }

            if (bodyText.includes('Not approved')) {
                if (currentDataIndex + 1 >= dataArray.length) {
                    isRunning = false;
                    chrome.storage.local.set({ 'veterans-is-running': false });
                    updateUIOnStop();
                    sendStatus('❌ All data failed, no more to try', 'error');
                    return;
                }

                removeProcessedData();
                stats.processed++;
                stats.failed++;
                updateStats();
                chrome.storage.local.set({
                    'veterans-current-index': currentDataIndex,
                    'veterans-is-running': true
                });

                await delay(2000);
                if (!isRunning) return;
                
                window.location.href = 'https://chatgpt.com/veterans-claim';
                await delay(4000);
                if (!isRunning) return;
                
                await startVerificationLoop();
                return;
            }

            if (bodyText.includes("You've been verified") || bodyText.includes('verified')) {
                sendStatus('✅ Verification successful!', 'success');
                isRunning = false;
                chrome.storage.local.set({ 'veterans-is-running': false });
                removeProcessedData(false);
                stats.processed++;
                stats.success++;
                updateStats();
                updateUIOnStop();
                return;
            }
            
            if (bodyText.includes('Check your email')) {
                sendStatus('📧 Email check page detected, reading mail...', 'info');
                await readMailAndVerify();
                return;
            }
            
            const formExists = document.querySelector('#sid-military-status + button');
            if (formExists) {
                sendStatus('✅ Found verification form directly, filling...', 'success');
                if (!currentEmail) await generateNewEmail();
                if (!isRunning) return;
                await fillForm();
                return;
            }
            throw new Error('Page heading not found and form not detected');
        }

        if (headingText.includes('Unlock this Military-Only Offer')) {
            if (!currentEmail) await generateNewEmail();
            sendStatus('✅ Found verification form, filling...', 'success');
            await delay(1000);
            if (!isRunning) return;
            await fillForm();
        } else if (headingText.includes('Check your email')) {
            sendStatus('📧 Email check page detected, reading mail...', 'info');
            await readMailAndVerify();
        } else if (headingText.includes('We are unable to verify you at this time') ||
                   headingText.includes('unable to verify you') ||
                   headingText.includes('sourcesUnavailable') ||
                   headingText.toLowerCase().includes('sources unavailable')) {
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            sendStatus('🚫 VPN Error: Unable to verify. Please change VPN and restart.', 'error');
            return;
        } else if (headingText.includes('Error') ||
                   headingText.includes('Verification Limit Exceeded') ||
                   headingText.includes('limit exceeded')) {
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            sendStatus('❌ Verification failed: ' + (headingText.includes('limit exceeded') ? 'Verification Limit Exceeded' : 'Error'), 'error');
            return;
        } else if (headingText.includes('verified') || headingText.includes("You've been verified")) {
            sendStatus('✅ Verification successful!', 'success');
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            removeProcessedData(false);
            stats.processed++;
            stats.success++;
            updateStats();
            updateUIOnStop();
            return;
        } else {
            const formExists = document.querySelector('#sid-military-status + button');
            if (formExists) {
                sendStatus('✅ Found verification form (by selector), filling...', 'success');
                if (!currentEmail) await generateNewEmail();
                if (!isRunning) return;
                await delay(1000);
                if (!isRunning) return;
                await fillForm();
            } else {
                sendStatus('⚠️ Unknown page state: ' + headingText, 'info');
                await delay(2000);
                if (!isRunning) return;
                await checkAndFillForm();
            }
        }
    } catch (error) {
        if (!isRunning) return;
        
        let errorMessage = 'Unknown error';
        if (error) {
            if (typeof error === 'string') {
                errorMessage = error;
            } else if (error.message) {
                errorMessage = error.message;
            } else {
                errorMessage = String(error);
            }
        }
        
        const isStatusError = errorMessage.toLowerCase().includes('status') || 
                             errorMessage.toLowerCase().includes('không tìm thấy');
        
        if (isStatusError) {
            sendStatus('❌ ' + errorMessage, 'error');
            await delay(100);
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            return;
        }
        
        sendStatus(`❌ Lỗi khi kiểm tra trang: ${errorMessage}`, 'error');
        await delay(2000);
        if (!isRunning) return;
        
        const formExists = document.querySelector('#sid-military-status + button');
        if (formExists) {
            sendStatus('✅ Found form on retry, filling...', 'success');
            if (!currentEmail) await generateNewEmail();
            if (!isRunning) return;
            await fillForm();
        } else {
            throw error;
        }
    }
}

async function fillForm() {
    if (!isRunning) {
        console.log('⏹️ Tool stopped, exiting fillForm');
        return;
    }
    
    if (!dataArray || dataArray.length === 0 || currentDataIndex >= dataArray.length) {
        sendStatus('❌ No data available', 'error');
        return;
    }

    const data = dataArray[currentDataIndex];
    const first = data.first;
    const last = data.last;
    const branch = data.branch.trim();
    const monthName = data.month.trim();
    const day = data.day.trim();
    const year = data.year.trim();
    
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                        'July', 'August', 'September', 'October', 'November', 'December'];
    const monthIndex = monthNames.findIndex(m => m.toLowerCase() === monthName.toLowerCase());
    
    if (monthIndex === -1) {
        throw new Error('Invalid month name: ' + monthName);
    }

    try {
        sendStatus('📝 Selecting status...', 'info');
        if (!isRunning) return;
        
        const statusButton = await waitForElement('#sid-military-status + button', 10000).catch((error) => {
            if (error === 'Tool stopped') return null;
            sendStatus('❌ NOT FOUND STATUS MENU. Có thể trang chưa load xong.', 'error');
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            return null;
        });
        
        if (!isRunning || !statusButton) return;
        
        let statusItem = document.getElementById('sid-military-status-item-1');
        const menuAlreadyOpen = statusItem !== null && statusItem.offsetParent !== null;
        
        if (!menuAlreadyOpen) {
            statusButton.click();
            await waitForElement('#sid-military-status-item-1', 10000).catch((error) => {
                if (error === 'Tool stopped') return null;
                sendStatus('❌ NOT FOUND STATUS MENU.', 'error');
                isRunning = false;
                chrome.storage.local.set({ 'veterans-is-running': false });
                updateUIOnStop();
                return null;
            });
            if (!isRunning) return;
            await delay(1000);
            statusItem = document.getElementById('sid-military-status-item-1');
        } else {
            await delay(500);
        }
        
        if (!statusItem) {
            sendStatus('❌ NOT FOUND STATUS MENU.', 'error');
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            return;
        }
        
        const statusButtonText = statusButton.innerText || statusButton.textContent || '';
        const isAlreadySelected = statusButtonText.toLowerCase().includes('veteran') || 
                                  statusButtonText.toLowerCase().includes('retiree');
        
        if (!isAlreadySelected) {
            statusItem.click();
            await delay(3000);
        } else {
            await delay(3000);
        }

        sendStatus('📝 Selecting branch...', 'info');
        const branchButton = await waitForElement('#sid-branch-of-service + button', 10000);
        if (!branchButton) throw new Error('Branch button not found');
        branchButton.click();
        await waitForElement('#sid-branch-of-service-menu', 10000);
        await delay(1000);
        const branchItems = document.querySelectorAll('#sid-branch-of-service-menu .sid-input-select-list__item');
        if (branchItems.length === 0) throw new Error('Branch items not found');
        
        let matched = false;
        const branchUpper = branch.toUpperCase().trim();
        const branchNoPrefix = branchUpper.replace(/^US\s+/, '');
        
        for (let item of branchItems) {
            let itemText = item.innerText.toUpperCase().trim();
            const itemTextNoPrefix = itemText.replace(/^US\s+/, '');
            
            if (itemText === branchUpper || 
                itemTextNoPrefix === branchNoPrefix ||
                itemText.includes(branchUpper) ||
                branchUpper.includes(itemTextNoPrefix) ||
                itemTextNoPrefix.includes(branchNoPrefix) ||
                branchNoPrefix.includes(itemTextNoPrefix)) {
                item.click();
                matched = true;
                break;
            }
        }
        if (!matched) throw new Error('Branch not found: ' + branch);
        await delay(200);

        sendStatus('📝 Entering name...', 'info');
        const firstNameInput = document.getElementById('sid-first-name');
        const lastNameInput = document.getElementById('sid-last-name');
        if (!firstNameInput || !lastNameInput) throw new Error('Name inputs not found');

        firstNameInput.value = first;
        firstNameInput.dispatchEvent(new Event('input', { bubbles: true }));
        firstNameInput.dispatchEvent(new Event('change', { bubbles: true }));
        await delay(200);

        lastNameInput.value = last;
        lastNameInput.dispatchEvent(new Event('input', { bubbles: true }));
        lastNameInput.dispatchEvent(new Event('change', { bubbles: true }));
        await delay(200);

        sendStatus('📝 Entering date of birth...', 'info');
        const dayInput = document.getElementById('sid-birthdate-day');
        const yearInput = document.getElementById('sid-birthdate-year');

        const monthButton = await waitForElement('#sid-birthdate__month + button', 10000);
        if (!monthButton) throw new Error('Month button not found');
        monthButton.click();
        await waitForElement('#sid-birthdate__month-menu', 10000);
        await delay(200);
        const monthItem = document.getElementById(`sid-birthdate__month-item-${monthIndex}`);
        if (!monthItem) throw new Error('Month item not found: ' + monthIndex);
        monthItem.click();
        await delay(200);

        if (!dayInput || !yearInput) throw new Error('Date inputs not found');
        dayInput.value = parseInt(day).toString();
        dayInput.dispatchEvent(new Event('input', { bubbles: true }));
        dayInput.dispatchEvent(new Event('change', { bubbles: true }));
        await delay(200);

        yearInput.value = year;
        yearInput.dispatchEvent(new Event('input', { bubbles: true }));
        yearInput.dispatchEvent(new Event('change', { bubbles: true }));
        await delay(200);

        sendStatus('📝 Entering discharge date...', 'info');
        const dischargeDayInput = document.getElementById('sid-discharge-date-day');
        const dischargeYearInput = document.getElementById('sid-discharge-date-year');

        const dischargeMonthButton = await waitForElement('#sid-discharge-date__month + button', 10000);
        if (!dischargeMonthButton) throw new Error('Discharge month button not found');
        dischargeMonthButton.click();
        await waitForElement('#sid-discharge-date__month-menu', 10000);
        await delay(200);
        const dischargeMonthItem = document.getElementById('sid-discharge-date__month-item-1');
        if (!dischargeMonthItem) throw new Error('Discharge month item not found');
        dischargeMonthItem.click();
        await delay(200);

        if (!dischargeDayInput || !dischargeYearInput) throw new Error('Discharge date inputs not found');
        dischargeDayInput.value = '1';
        dischargeDayInput.dispatchEvent(new Event('input', { bubbles: true }));
        dischargeDayInput.dispatchEvent(new Event('change', { bubbles: true }));
        await delay(200);

        dischargeYearInput.value = '2025';
        dischargeYearInput.dispatchEvent(new Event('input', { bubbles: true }));
        dischargeYearInput.dispatchEvent(new Event('change', { bubbles: true }));
        await delay(200);

        sendStatus('📝 Entering email...', 'info');
        const emailInput = document.getElementById('sid-email');
        if (!emailInput) throw new Error('Email input not found');
        emailInput.value = currentEmail;
        emailInput.dispatchEvent(new Event('input', { bubbles: true }));
        emailInput.dispatchEvent(new Event('change', { bubbles: true }));
        await delay(200);

        sendStatus('🚀 Submitting form...', 'info');
        const submitBtn = document.getElementById('sid-submit-btn-collect-info');
        if (!submitBtn) throw new Error('Submit button not found');
        submitBtn.click();
        sendStatus('✅ Form submitted, waiting for response...', 'success');

        await delay(5000);
        if (!isRunning) return;

        await checkAndFillForm();
    } catch (error) {
        if (!isRunning) return;
        
        let errorMessage = 'Unknown error';
        if (error) {
            if (typeof error === 'string') {
                errorMessage = error;
            } else if (error.message) {
                errorMessage = error.message;
            } else {
                errorMessage = String(error);
            }
        }
        
        const isStatusError = errorMessage.toLowerCase().includes('status') || 
                             errorMessage.toLowerCase().includes('không tìm thấy');
        
        if (isStatusError) {
            sendStatus('❌ ' + errorMessage, 'error');
            await delay(100);
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            return;
        }
        
        sendStatus(`❌ Lỗi khi điền form: ${errorMessage}`, 'error');
        throw error;
    }
}

async function readMailAndVerify() {
    if (!isRunning) {
        console.log('⏹️ Tool stopped, exiting readMailAndVerify');
        return;
    }
    
    try {
        sendStatus('📧 Reading emails...', 'info');

        const [username, domain] = currentEmail.split('@');
        if (!username || !domain) {
            throw new Error('Invalid email format');
        }

        const emailsResponse = await fetch(
            `https://tinyhost.shop/api/email/${domain}/${username}/?page=1&limit=20`
        );

        if (!emailsResponse.ok) {
            throw new Error('Failed to fetch emails');
        }

        const emailsData = await emailsResponse.json();
        let emails = emailsData.emails || [];

        if (emails.length === 0) {
            mailRetryCount++;
            if (mailRetryCount >= MAX_MAIL_RETRIES) {
                sendStatus('❌ Max retries reached for reading mail, stopping tool', 'error');
                mailRetryCount = 0;
                isRunning = false;
                chrome.storage.local.set({ 'veterans-is-running': false });
                updateUIOnStop();
                return;
            }
            sendStatus(`📭 No emails found, retrying... (${mailRetryCount}/${MAX_MAIL_RETRIES})`, 'info');
            await delay(5000);
            await readMailAndVerify();
            return;
        }

        mailRetryCount = 0;

        emails.sort((a, b) => {
            const dateA = new Date(a.date);
            const dateB = new Date(b.date);
            return dateB - dateA;
        });

        let verificationLink = null;
        for (const email of emails) {
            if (email.html_body) {
                const htmlLinkMatch = email.html_body.match(/https:\/\/services\.sheerid\.com\/verify\/[^"'\s<>]+/i);
                if (htmlLinkMatch) {
                    verificationLink = htmlLinkMatch[0].replace(/&amp;/g, '&');
                    break;
                }
            }

            if (email.body) {
                const bodyLinkMatch = email.body.match(/https:\/\/services\.sheerid\.com\/verify\/[^"'\s<>()]+/i);
                if (bodyLinkMatch) {
                    verificationLink = bodyLinkMatch[0].replace(/&amp;/g, '&');
                    break;
                }
            }
        }

        if (verificationLink) {
            if (!isRunning) return;
            
            sendStatus('✅ Verification link found, opening...', 'success');
            mailRetryCount = 0;
            window.location.href = verificationLink;
            await delay(5000);
            
            if (!isRunning) return;
            
            await checkAndFillForm();
        } else {
            if (!isRunning) return;
            
            mailRetryCount++;
            if (mailRetryCount >= MAX_MAIL_RETRIES) {
                sendStatus('❌ Max retries reached, stopping tool', 'error');
                mailRetryCount = 0;
                isRunning = false;
                chrome.storage.local.set({ 'veterans-is-running': false });
                updateUIOnStop();
                return;
            }
            sendStatus(`⚠️ No verification link found, retrying... (${mailRetryCount}/${MAX_MAIL_RETRIES})`, 'info');
            await delay(5000);
            
            if (!isRunning) return;
            
            await readMailAndVerify();
        }
    } catch (error) {
        if (!isRunning) return;
        
        console.error('Error reading mail:', error);
        mailRetryCount++;
        if (mailRetryCount >= MAX_MAIL_RETRIES) {
            sendStatus('❌ Max retries reached, stopping tool', 'error');
            mailRetryCount = 0;
            isRunning = false;
            chrome.storage.local.set({ 'veterans-is-running': false });
            updateUIOnStop();
            return;
        }
        sendStatus(`❌ Error reading mail, retrying... (${mailRetryCount}/${MAX_MAIL_RETRIES}): ` + error.message, 'error');
        await delay(5000);
        
        if (!isRunning) return;
        
        await readMailAndVerify();
    }
}

