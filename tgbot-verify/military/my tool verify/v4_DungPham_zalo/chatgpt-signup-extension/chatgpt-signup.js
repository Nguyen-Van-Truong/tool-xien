// Content script for ChatGPT account signup automation
let isRunning = false;
let currentDataIndex = 0;
let dataArray = [];
let stats = {
    processed: 0,
    success: 0,
    failed: 0
};

// Parse data from format: email-chatgpt|pass-chatgpt|email-login|pass-email|refresh_token|client_id
function parseAccountData(dataString) {
    const lines = dataString.trim().split('\n').filter(line => line.trim());
    return lines.map(line => {
        const parts = line.split('|').map(p => p.trim());
        if (parts.length < 6) {
            throw new Error(`Invalid data format: ${line}. Expected: email-chatgpt|pass-chatgpt|email-login|pass-email|refresh_token|client_id`);
        }
        return {
            email: parts[0],           // email-chatgpt
            password: parts[1],        // pass-chatgpt
            emailLogin: parts[2],      // email-login
            passEmail: parts[3],       // pass-email
            refreshToken: parts[4],    // refresh_token
            clientId: parts[5],        // client_id
            original: line
        };
    });
}

// Listen for messages from side panel or background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'startSignup') {
        console.log('🚀 Received startSignup message');
        try {
            const parsedData = parseAccountData(message.data);
            dataArray = parsedData;
            currentDataIndex = 0;
            stats = { processed: 0, success: 0, failed: 0 };
            isRunning = true;

            // Save API endpoint if provided
            if (message.apiEndpoint) {
                chrome.storage.local.set({
                    'chatgpt-signup-api-endpoint': message.apiEndpoint
                });
            }

            // Save to storage
            chrome.storage.local.set({
                'chatgpt-signup-data-array': dataArray,
                'chatgpt-signup-current-index': 0,
                'chatgpt-signup-is-running': true,
                'chatgpt-signup-stats': stats
            }, () => {
                console.log('✅ Data saved to storage');
                startSignupLoop();
                sendResponse({ success: true });
            });
        } catch (error) {
            console.error('❌ Error parsing data:', error);
            sendResponse({ success: false, error: error.message });
        }
    } else if (message.action === 'stopSignup') {
        console.log('⏹️ Stop signup requested');
        isRunning = false;
        chrome.storage.local.set({ 'chatgpt-signup-is-running': false });
        sendStatus('⏹️ Đăng ký đã dừng', 'info');
        sendResponse({ success: true });
    }
    return true;
});

// Auto-resume when page loads
(function autoResumeSignup() {
    console.log('🔍 Checking if we need to auto-resume signup...');
    chrome.storage.local.get(
        [
            'chatgpt-signup-data-array',
            'chatgpt-signup-current-index',
            'chatgpt-signup-is-running',
            'chatgpt-signup-stats'
        ],
        (result) => {
            if (
                result['chatgpt-signup-is-running'] &&
                result['chatgpt-signup-data-array']
            ) {
                dataArray = result['chatgpt-signup-data-array'];
                currentDataIndex = result['chatgpt-signup-current-index'] || 0;
                if (result['chatgpt-signup-stats']) {
                    stats = result['chatgpt-signup-stats'];
                }
                isRunning = true;

                console.log('🔄 Auto-resuming signup...');
                setTimeout(() => {
                    startSignupLoop();
                }, 2000);
            }
        }
    );
})();

async function startSignupLoop() {
    if (!isRunning) {
        console.log('⏹️ Signup stopped, exiting loop');
        return;
    }

    if (currentDataIndex >= dataArray.length) {
        isRunning = false;
        chrome.storage.local.set({ 'chatgpt-signup-is-running': false });
        sendStatus('✅ Đã xử lý tất cả tài khoản', 'success');
        return;
    }

    const currentData = dataArray[currentDataIndex];
    const currentPosition = currentDataIndex + 1;
    const total = dataArray.length;

    sendStatus(
        `🔄 Đang xử lý ${currentPosition}/${total}: ${currentData.email}`,
        'info'
    );
    updateStats();

    // Save current state
    chrome.storage.local.set({
        'chatgpt-signup-current-index': currentDataIndex,
        'chatgpt-signup-is-running': true
    });

    try {
        const currentUrl = window.location.href;
        console.log('📍 Current URL:', currentUrl);

        // B1: Truy cập chatgpt.com hoặc auth.openai.com (cả 2 đều OK)
        const isValidUrl = currentUrl.includes('chatgpt.com') || currentUrl.includes('auth.openai.com') || currentUrl.includes('openai.com');
        if (!isValidUrl) {
            console.log('🌐 B1: Navigating to chatgpt.com...');
            window.location.href = 'https://chatgpt.com';
            await delay(5000);
            await startSignupLoop();
            return;
        }

        // Kiểm tra URL auth.openai.com/create-account/password (B4: Password page) - kiểm tra URL trước
        if (currentUrl.includes('auth.openai.com/create-account/password')) {
            console.log('🔍 B4: On password page (auth.openai.com), waiting for password input...');
            sendStatus('🔍 Đang ở trang password, đợi form load...', 'info');

            // Đợi và thử tìm password input nhiều lần
            let passwordInput = null;
            let attempts = 0;
            const maxAttempts = 15;

            while (attempts < maxAttempts && !passwordInput && isRunning) {
                attempts++;
                console.log(`⏳ Đợi password input xuất hiện... (${attempts}/${maxAttempts})`);

                // Thử tìm password input
                passwordInput = document.querySelector('input[name="new-password"]') ||
                    document.querySelector('input[id*="-new-password"]') ||
                    document.querySelector('input[type="password"][placeholder="Password"]') ||
                    document.querySelector('input[type="password"]');

                if (passwordInput) {
                    console.log('✅ Tìm thấy password input trên trang password!');
                    sendStatus('✅ Đã tìm thấy form password, đang điền...', 'success');
                    await fillPassword(currentData);
                    return;
                }

                // Đợi một chút trước khi thử lại
                await delay(500);
            }

            // Nếu vẫn không tìm thấy sau nhiều lần thử, gọi lại startSignupLoop()
            if (!passwordInput) {
                console.log('⚠️ Không tìm thấy password input sau nhiều lần thử, gọi lại startSignupLoop()...');
                await delay(1000);
                await startSignupLoop();
            }
            return;
        }

        // Kiểm tra URL auth.openai.com/email-verification (B5: OTP page)
        if (currentUrl.includes('auth.openai.com/email-verification') || currentUrl.includes('email-verification')) {
            console.log('🔍 B5: On email verification page, waiting 10s before fetching OTP...');
            sendStatus('📧 Đang ở trang xác thực email, đợi 10s để nhận email...', 'info');

            // Đợi 10 giây để email được gửi
            await delay(10000);

            if (!isRunning) {
                return;
            }

            // Gọi handleOTPVerification
            await handleOTPVerification(currentData);
            return;
        }

        // Kiểm tra URL auth.openai.com/about-you (B6: About You page - name & birthday)
        if (currentUrl.includes('auth.openai.com/about-you') || currentUrl.includes('/about-you')) {
            console.log('🔍 B6: On About You page, filling name and birthday...');
            sendStatus('📝 Đang ở trang About You, điền tên và ngày sinh...', 'info');

            await delay(2000);

            if (!isRunning) {
                return;
            }

            // Gọi handleAboutYou
            await handleAboutYou(currentData);
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
            console.log('🔍 B3: Found email input form...');
            await fillEmailAndContinue(currentData);
            return;
        } else if (hasPasswordInput) {
            // B4: Form nhập password (chỉ khi không có email input)
            console.log('🔍 B4: Found password input form, calling fillPassword()...');
            sendStatus('✅ Đã tìm thấy form password, đang điền...', 'success');
            await fillPassword(currentData);
            return;
        } else if (currentUrl.includes('chatgpt.com/auth/signup') ||
            currentUrl.includes('chatgpt.com/signup') ||
            currentUrl.includes('chatgpt.com/register')) {
            // Đã ở trang signup nhưng chưa có form, thử tìm nút Sign up for free
            console.log('🔍 On signup page but no form found, checking for Sign up for free button...');
            await clickSignUpButton();
            return;
        } else if (currentUrl.includes('chatgpt.com/auth/verify') ||
            currentUrl.includes('chatgpt.com/verify')) {
            // On OTP verification page (tạm thời không xử lý)
            console.log('🔍 On OTP verification page (tạm thời dừng)...');
            sendStatus('⏸️ Đã đến trang OTP, tạm thời dừng để debug', 'info');
            return;
        } else if (currentUrl.includes('chatgpt.com')) {
            // B2: Trang ChatGPT (có thể là homepage hoặc trang khác), tìm nút Sign up for free
            console.log('🔍 B2: On ChatGPT page, looking for Sign up for free button...');
            await clickSignUpButton();
            return;
        } else {
            // Không phải trang ChatGPT, redirect
            console.log('🌐 Not on ChatGPT page, redirecting...');
            window.location.href = 'https://chatgpt.com';
            await delay(5000);
            await startSignupLoop();
            return;
        }
    } catch (error) {
        if (!isRunning) {
            console.log('⏹️ Signup stopped during error handling');
            return;
        }

        console.error('❌ Error in signup loop:', error);
        const errorMessage = error?.message || String(error);
        sendStatus('❌ Lỗi: ' + errorMessage, 'error');

        // Move to next account on error
        currentDataIndex++;
        stats.processed++;
        stats.failed++;
        updateStats();
        chrome.storage.local.set({
            'chatgpt-signup-current-index': currentDataIndex
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

    console.log('🔍 B2: Looking for "Sign up for free" button...');
    sendStatus('🔍 B2: Đang tìm nút Sign up for free...', 'info');

    // Wait for page to load
    await delay(3000);

    if (!isRunning) {
        return;
    }

    try {
        // Kiểm tra xem đã có form email chưa (có thể modal đã mở)
        const hasEmailInput = document.querySelector('input[type="email"], input[name*="email" i], input[id*="email" i], input[placeholder*="Email address" i], input[placeholder*="email" i]');
        if (hasEmailInput) {
            console.log('✅ Form email đã xuất hiện, bỏ qua bước click nút');
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
            throw new Error('Không tìm thấy nút "Sign up for free"');
        }

        console.log('✅ Found Sign up for free button:', signUpButton);
        sendStatus('✅ Đã tìm thấy nút Sign up for free, đang click...', 'success');

        // Click button
        signUpButton.click();
        sendStatus('✅ Đã click nút, đợi form email xuất hiện...', 'success');
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
            console.log(`⏳ Đợi form email xuất hiện... (${attempts}/${maxAttempts})`);

            emailInput = document.querySelector('input[type="email"], input[name*="email" i], input[id*="email" i], input[placeholder*="Email address" i], input[placeholder*="email" i]');

            if (emailInput) {
                console.log('✅ Form email đã xuất hiện!');
                break;
            }

            await delay(1000);

            if (!isRunning) {
                return;
            }
        }

        if (!emailInput) {
            throw new Error('Form email không xuất hiện sau khi click nút Sign up for free');
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
        console.log('⏹️ [DEBUG] fillEmailAndContinue: isRunning = false, exiting');
        return;
    }

    console.log('📝 [DEBUG] B3: Bắt đầu fillEmailAndContinue...');
    console.log('📝 [DEBUG] Data:', { email: data.email });
    sendStatus('📝 B3: Đang điền email...', 'info');

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
                console.log(`✅ Found email input with selector: ${selector}`);
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
            throw new Error('Không tìm thấy ô nhập email');
        }

        // Fill email
        emailInput.value = data.email;
        emailInput.dispatchEvent(new Event('input', { bubbles: true }));
        emailInput.dispatchEvent(new Event('change', { bubbles: true }));
        emailInput.dispatchEvent(new Event('blur', { bubbles: true }));
        console.log('✅ Đã điền email:', data.email);
        sendStatus('✅ Đã điền email, đang tìm nút Continue...', 'success');
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
            // Log tất cả buttons để debug
            const allButtons = Array.from(document.querySelectorAll('button'));
            console.log('🔍 All buttons found:', allButtons.map(btn => ({
                text: btn.innerText || btn.textContent,
                type: btn.type,
                class: btn.className,
                disabled: btn.disabled
            })));
            throw new Error('Không tìm thấy nút Continue');
        }

        // Kiểm tra xem nút có bị disabled không
        if (continueButton.disabled) {
            console.log('⚠️ Continue button is disabled, waiting...');
            sendStatus('⚠️ Nút Continue đang disabled, đợi...', 'info');

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
                throw new Error('Nút Continue vẫn bị disabled sau khi đợi');
            }
        }

        console.log('✅ Found Continue button:', continueButton);
        console.log('   Text:', continueButton.innerText || continueButton.textContent);
        console.log('   Type:', continueButton.type);
        console.log('   Class:', continueButton.className);
        console.log('   Disabled:', continueButton.disabled);
        sendStatus('✅ Đã tìm thấy nút Continue, đang click...', 'success');

        // Đợi một chút để đảm bảo nút sẵn sàng
        await delay(500);

        // Click Continue - thử nhiều cách
        console.log('🖱️ [DEBUG] Đang click nút Continue...');
        try {
            continueButton.click();
            console.log('✅ [DEBUG] Đã click nút Continue thành công');
        } catch (e) {
            // Thử cách khác nếu click() không work
            console.log('⚠️ [DEBUG] Normal click failed, trying alternative methods...');
            continueButton.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
            console.log('✅ [DEBUG] Đã click bằng dispatchEvent');
        }

        console.log('📢 [DEBUG] Đang cập nhật status: "Đã click Continue, đợi 2 giây rồi quét trang..."');
        sendStatus('✅ Đã click Continue, đang đợi trang chuyển...', 'success');
        console.log('🔄 [DEBUG] ========== BẮT ĐẦU XỬ LÝ SAU KHI CLICK CONTINUE ==========');

        // Đợi động: đợi URL thay đổi hoặc password input xuất hiện (KHÔNG đợi cố định 2 giây)
        const initialUrl = window.location.href;
        console.log('📍 [DEBUG] URL ban đầu:', initialUrl);

        let passwordInput = null;
        let attempts = 0;
        const maxAttempts = 30; // Tối đa 15 giây (30 * 500ms)

        console.log('⏳ [DEBUG] Bắt đầu đợi động (đợi URL thay đổi hoặc password input xuất hiện)...');
        sendStatus('⏳ Đang đợi trang chuyển hoặc form password xuất hiện...', 'info');

        // Kiểm tra ngay lập tức xem có password input không (có thể đã có sẵn)
        console.log('🔍 [DEBUG] Kiểm tra password input ngay lập tức...');
        const allInputs = Array.from(document.querySelectorAll('input'));
        console.log('🔍 [DEBUG] Tổng số inputs trên trang:', allInputs.length);

        // Log tất cả inputs để debug
        allInputs.forEach((input, index) => {
            if (input.type === 'password' || (input.name && input.name.includes('password')) ||
                (input.id && input.id.includes('password')) ||
                (input.placeholder && input.placeholder.toLowerCase().includes('password'))) {
                console.log(`🔍 [DEBUG] Input ${index + 1} (có thể là password):`, {
                    type: input.type,
                    name: input.name,
                    id: input.id,
                    placeholder: input.placeholder,
                    className: input.className,
                    visible: input.offsetParent !== null,
                    disabled: input.disabled,
                    readonly: input.readOnly
                });
            }
        });

        // Tìm password input ngay
        passwordInput = document.querySelector('input[name="new-password"]') ||
            document.querySelector('input[id*="-new-password"]') ||
            document.querySelector('input[type="password"][placeholder="Password"]') ||
            document.querySelector('input[type="password"]');

        // Nếu không tìm thấy bằng selector, thử tìm bằng cách quét tất cả inputs
        if (!passwordInput) {
            passwordInput = allInputs.find(input => {
                const type = input.type === 'password';
                const name = (input.name || '').toLowerCase().includes('password');
                const id = (input.id || '').toLowerCase().includes('password');
                const placeholder = (input.placeholder || '').toLowerCase().includes('password');
                return type || name || id || placeholder;
            });
        }

        if (passwordInput) {
            console.log('✅ [DEBUG] Tìm thấy password input ngay lập tức!');
            console.log('📝 [DEBUG] Password input:', {
                type: passwordInput.type,
                name: passwordInput.name,
                id: passwordInput.id,
                placeholder: passwordInput.placeholder
            });
        } else {
            console.log('⚠️ [DEBUG] Không tìm thấy password input ngay, bắt đầu đợi động...');

            while (attempts < maxAttempts && !passwordInput && isRunning) {
                attempts++;

                // Kiểm tra URL có thay đổi không
                const currentUrl = window.location.href;
                if (currentUrl !== initialUrl && attempts > 2) {
                    console.log(`✅ [DEBUG] URL đã thay đổi: "${initialUrl}" → "${currentUrl}"`);

                    // Nếu URL chuyển sang auth.openai.com, đợi lâu hơn rồi restart loop
                    if (currentUrl.includes('auth.openai.com')) {
                        console.log('🔄 [DEBUG] Detected auth.openai.com, waiting 5s then restarting loop...');
                        sendStatus('🔄 Chuyển trang auth.openai.com, đợi 5s...', 'info');
                        await delay(5000);
                        await startSignupLoop();
                        return;
                    }

                    sendStatus('✅ URL đã thay đổi, đang tìm password input...', 'success');
                }

                // Tìm password input - thêm type="password" lên đầu
                passwordInput = document.querySelector('input[type="password"]') ||
                    document.querySelector('input[name="new-password"]') ||
                    document.querySelector('input[id*="-new-password"]') ||
                    document.querySelector('input[type="password"][placeholder*="Password" i]');

                // Nếu không tìm thấy, thử quét tất cả inputs
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
                    console.log('✅ [DEBUG] Tìm thấy password input ở lần thử ' + attempts);
                    break;
                }

                // Log mỗi 5 lần thử
                if (attempts % 5 === 0) {
                    console.log(`⏳ [DEBUG] Đang đợi... (${attempts}/${maxAttempts})`);
                }

                await delay(1000); // Tăng delay lên 1s
            }
        }

        console.log('✅ [DEBUG] Kết thúc đợi động. Tìm thấy: ' + (passwordInput ? 'CÓ' : 'KHÔNG'));

        if (!isRunning) {
            console.log('⏹️ [DEBUG] Signup stopped');
            return;
        }

        // Nếu tìm thấy password input, gọi fillPassword() ngay
        if (passwordInput) {
            console.log('✅ [DEBUG] ========== TÌM THẤY PASSWORD INPUT ==========');
            sendStatus('✅ Đã tìm thấy form password, đang điền...', 'success');
            try {
                await fillPassword(data);
                console.log('✅ [DEBUG] fillPassword() đã hoàn thành');
            } catch (error) {
                console.error('❌ [DEBUG] Lỗi trong fillPassword():', error);
                sendStatus('❌ Lỗi khi điền password: ' + (error?.message || String(error)), 'error');
                throw error;
            }
        } else {
            // Nếu không tìm thấy, gọi startSignupLoop() trong setTimeout để tránh block
            console.log('⚠️ [DEBUG] Không tìm thấy password input, gọi startSignupLoop()...');
            sendStatus('⚠️ Không tìm thấy password input, thử lại...', 'info');

            // Dùng setTimeout để tránh block
            setTimeout(async () => {
                try {
                    await startSignupLoop();
                } catch (error) {
                    console.error('❌ [DEBUG] Lỗi trong startSignupLoop():', error);
                    sendStatus('❌ Lỗi: ' + (error?.message || String(error)), 'error');
                }
            }, 100);
        }

        console.log('🔄 [DEBUG] ========== KẾT THÚC XỬ LÝ SAU KHI CLICK CONTINUE ==========');
    } catch (error) {
        console.error('❌ [DEBUG] Error trong fillEmailAndContinue:', error);
        console.error('❌ [DEBUG] Error stack:', error.stack);
        console.error('❌ [DEBUG] Error name:', error.name);
        console.error('❌ [DEBUG] Error message:', error.message);
        sendStatus('❌ Lỗi khi điền email: ' + (error?.message || String(error)), 'error');
        throw error;
    }
}

// B4: Điền password và nhấn Continue
async function fillPassword(data) {
    if (!isRunning) {
        return;
    }

    console.log('📝 B4: Filling password...');
    sendStatus('📝 B4: Đang điền mật khẩu...', 'info');

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
                    console.log(`✅ Found password input with selector: ${selector}`);
                    break;
                }
            } catch (e) {
                // Selector might be invalid
                continue;
            }
        }

        if (!passwordInput) {
            // Try to find by type
            const allInputs = Array.from(document.querySelectorAll('input'));
            passwordInput = allInputs.find(input => input.type === 'password');
        }

        if (!passwordInput) {
            throw new Error('Không tìm thấy ô nhập password');
        }

        // Fill password
        passwordInput.value = data.password;
        passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
        passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
        passwordInput.dispatchEvent(new Event('blur', { bubbles: true }));
        console.log('✅ Đã điền password');
        sendStatus('✅ Đã điền mật khẩu, đang tìm nút Continue...', 'success');
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
            // Log tất cả buttons để debug
            const allButtons = Array.from(document.querySelectorAll('button'));
            console.log('🔍 All buttons found:', allButtons.map(btn => ({
                text: btn.innerText || btn.textContent,
                type: btn.type,
                class: btn.className,
                dataAction: btn.getAttribute('data-dd-action-name'),
                disabled: btn.disabled
            })));
            throw new Error('Không tìm thấy nút Continue');
        }

        // Kiểm tra xem nút có bị disabled không
        if (continueButton.disabled || continueButton.getAttribute('aria-disabled') === 'true') {
            console.log('⚠️ Continue button is disabled, waiting...');
            sendStatus('⚠️ Nút Continue đang disabled, đợi...', 'info');

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
                throw new Error('Nút Continue vẫn bị disabled sau khi đợi');
            }
        }

        console.log('✅ Found Continue button:', continueButton);
        console.log('   Text:', continueButton.innerText || continueButton.textContent);
        console.log('   Type:', continueButton.type);
        console.log('   Class:', continueButton.className);
        console.log('   Data Action:', continueButton.getAttribute('data-dd-action-name'));
        console.log('   Disabled:', continueButton.disabled);
        sendStatus('✅ Đã tìm thấy nút Continue, đang click...', 'success');

        // Đợi một chút để đảm bảo nút sẵn sàng
        await delay(500);

        // Click Continue - thử nhiều cách
        try {
            continueButton.click();
        } catch (e) {
            // Thử cách khác nếu click() không work
            console.log('⚠️ Normal click failed, trying alternative methods...');
            continueButton.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
        }

        sendStatus('✅ Đã click Continue, đợi trang load...', 'success');
        await delay(3000);

        // Continue to next stage (email-verification or about-you)
        console.log('🔄 Continuing to next stage...');
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

    console.log('📝 B6: Handling About You page...');
    sendStatus('📝 Đang điền thông tin cá nhân...', 'info');

    try {
        // Generate name from email (first 7 characters before @)
        const emailPrefix = data.email.split('@')[0];
        const fullName = emailPrefix.substring(0, Math.min(emailPrefix.length, 10)); // Use up to 10 chars
        console.log(`📝 Full name: ${fullName}`);

        // Generate random birthday - use 10-12 for month, 10-28 for day to ensure 2 digits
        const year = Math.floor(Math.random() * (1980 - 1960 + 1)) + 1960;
        const month = Math.floor(Math.random() * 3) + 10; // 10, 11, or 12
        const day = Math.floor(Math.random() * 19) + 10; // 10 to 28
        console.log(`🎂 Birthday: ${month}/${day}/${year}`);

        // Fill Full Name input
        const nameInput = document.querySelector('input[name="name"]') ||
            document.querySelector('input[id*="-name"]') ||
            document.querySelector('input[placeholder*="Full name" i]') ||
            document.querySelector('input[placeholder*="name" i]');

        if (nameInput) {
            nameInput.value = fullName;
            nameInput.dispatchEvent(new Event('input', { bubbles: true }));
            nameInput.dispatchEvent(new Event('change', { bubbles: true }));
            console.log('✅ Đã điền Full Name');
            sendStatus(`✅ Đã điền tên: ${fullName}`, 'success');
        } else {
            console.log('⚠️ Không tìm thấy input Full Name');
        }

        await delay(2000);

        // Fill Birthday with 2-click approach and retry logic
        // Step 1: Click "Birthday" label first
        // Step 2: Click on monthSpinner  
        // Step 3: Type 8 digits MMDDYYYY
        // If error appears, retry

        const birthdayLabel = document.querySelector('._typeableLabelText_afhkj_87');
        const monthSpinner = document.querySelector('[data-type="month"][role="spinbutton"]');

        // Helper function to type birthday digits - ONLY keyboard events, 1s delay
        async function typeBirthdayDigits(dateString) {
            console.log(`📝 Typing digits: ${dateString}`);

            for (let i = 0; i < dateString.length; i++) {
                const digit = dateString[i];
                const activeEl = document.activeElement;
                console.log(`⌨️ Typing digit ${i + 1}/${dateString.length}: ${digit} into ${activeEl.getAttribute('data-type') || 'unknown'}`);

                // Only dispatch keyboard events - no execCommand!
                // KeyboardEvent with all required properties
                const keydownEvent = new KeyboardEvent('keydown', {
                    key: digit,
                    code: `Digit${digit}`,
                    keyCode: 48 + parseInt(digit),
                    which: 48 + parseInt(digit),
                    charCode: 0,
                    bubbles: true,
                    cancelable: true,
                    composed: true,
                    view: window
                });
                activeEl.dispatchEvent(keydownEvent);

                const keypressEvent = new KeyboardEvent('keypress', {
                    key: digit,
                    code: `Digit${digit}`,
                    keyCode: 48 + parseInt(digit),
                    which: 48 + parseInt(digit),
                    charCode: 48 + parseInt(digit),
                    bubbles: true,
                    cancelable: true,
                    composed: true,
                    view: window
                });
                activeEl.dispatchEvent(keypressEvent);

                const keyupEvent = new KeyboardEvent('keyup', {
                    key: digit,
                    code: `Digit${digit}`,
                    keyCode: 48 + parseInt(digit),
                    which: 48 + parseInt(digit),
                    charCode: 0,
                    bubbles: true,
                    cancelable: true,
                    composed: true,
                    view: window
                });
                activeEl.dispatchEvent(keyupEvent);

                // 1 second delay so user can see each digit
                await delay(1000);
            }
            console.log('✅ Finished typing all digits');
        }

        // Check for error
        function hasError() {
            return document.querySelector('._error_afhkj_109') !== null ||
                document.querySelector('[data-invalid="true"]') !== null;
        }

        if (monthSpinner) {
            const dateString = String(month).padStart(2, '0') + String(day).padStart(2, '0') + String(year);
            console.log(`📅 Typing date string: ${dateString}`);

            let attempts = 0;
            const maxAttempts = 3;

            while (attempts < maxAttempts) {
                attempts++;
                console.log(`🔄 Birthday attempt ${attempts}/${maxAttempts}`);

                // Step 1: Click Birthday label first (if exists)
                if (birthdayLabel) {
                    birthdayLabel.click();
                    console.log('✅ Clicked Birthday label');
                    await delay(300);
                }

                // Step 2: Click on monthSpinner
                monthSpinner.click();
                console.log('✅ Clicked monthSpinner');
                await delay(200);

                // Focus on monthSpinner
                monthSpinner.focus();
                await delay(200);

                // Step 3: Type all 8 digits
                await typeBirthdayDigits(dateString);

                // Blur to finalize
                document.activeElement.blur();

                // Wait 3 seconds before checking for errors
                console.log('⏳ Waiting 3 seconds before checking for errors...');
                await delay(3000);

                // Check for error
                if (!hasError()) {
                    console.log(`✅ Birthday filled successfully: ${month}/${day}/${year}`);
                    sendStatus(`✅ Đã điền ngày sinh: ${month}/${day}/${year}`, 'success');
                    break;
                } else {
                    console.log(`⚠️ Birthday error detected, retrying...`);
                    if (attempts < maxAttempts) {
                        sendStatus(`⚠️ Lỗi birthday, thử lại lần ${attempts + 1}...`, 'info');
                        await delay(500);
                    }
                }
            }
        } else {
            console.log('⚠️ Không tìm thấy monthSpinner cho birthday');
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
            console.log('✅ Found Continue button, clicking...');
            continueButton.click();
            sendStatus('✅ Đã click Continue, hoàn thành đăng ký!', 'success');
            await delay(3000);

            // Mark as success
            stats.processed++;
            stats.success++;
            updateStats();

            // Move to next account
            currentDataIndex++;
            chrome.storage.local.set({
                'chatgpt-signup-current-index': currentDataIndex,
                'chatgpt-signup-stats': stats
            });

            sendStatus(`✅ Hoàn thành tài khoản ${currentDataIndex}/${dataArray.length}!`, 'success');
            console.log(`🎉 Account ${currentDataIndex} completed successfully!`);

            // Continue with next account after delay
            await delay(5000);
            await startSignupLoop();
        } else {
            throw new Error('Không tìm thấy nút Continue');
        }

    } catch (error) {
        console.error('❌ Error in handleAboutYou:', error);
        sendStatus('❌ Lỗi khi điền thông tin: ' + error.message, 'error');
        throw error;
    }
}

async function handleOTPVerification(data) {
    if (!isRunning) {
        return;
    }

    console.log('📧 Handling OTP verification...');
    sendStatus('📧 Đang lấy mã OTP từ email...', 'info');

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

        console.log('📡 Calling dongvanfb.net API for emails...');
        sendStatus('📡 Đang đọc email từ API...', 'info');

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
            throw new Error('Không tìm thấy email nào');
        }

        console.log(`✅ Nhận được ${messages.length} email(s)`);

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

            console.log(`📧 Checking email: "${subject.substring(0, 50)}..."`);

            // Tìm email có subject chứa "your chatgpt code is"
            if (subjectLower.includes('your chatgpt code is') || subjectLower.includes('chatgpt code')) {
                foundEmail = msg;

                // Extract OTP từ SUBJECT trước (vì subject rõ ràng hơn): "Your ChatGPT code is 679436"
                const subjectOtpMatch = subject.match(/code\s*(?:is\s*)?(\d{6})/i);
                if (subjectOtpMatch) {
                    otpCode = subjectOtpMatch[1];
                    console.log(`✅ Tìm thấy mã OTP trong subject: ${otpCode}`);
                    break;
                }

                // Fallback: tìm bất kỳ 6 số trong subject
                const subjectMatch = subject.match(/(\d{6})/);
                if (subjectMatch) {
                    otpCode = subjectMatch[1];
                    console.log(`✅ Fallback OTP từ subject: ${otpCode}`);
                    break;
                }

                // Nếu không có trong subject, thử body
                const body = msg.message || msg.html_body || '';
                const bodyMatch = body.match(/code\s*(?:is\s*)?(\d{6})/i) || body.match(/(\d{6})/);
                if (bodyMatch) {
                    otpCode = bodyMatch[1];
                    console.log(`✅ Tìm thấy mã OTP trong body: ${otpCode}`);
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
                    console.log(`✅ Tìm thấy mã OTP trong email khác: ${otpCode}`);
                    break;
                }
            }
        }

        if (!otpCode) {
            throw new Error('Không tìm thấy mã OTP 6 số trong email. Subject: ' + (foundEmail?.subject || 'N/A'));
        }

        console.log('✅ Received OTP code');
        sendStatus('✅ Đã nhận mã OTP, đang điền...', 'success');
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
                    console.log(`✅ Found OTP input with selector: ${selector}`);
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
            throw new Error('Không tìm thấy ô nhập mã OTP');
        }

        // Fill OTP
        otpInput.value = otpCode;
        otpInput.dispatchEvent(new Event('input', { bubbles: true }));
        otpInput.dispatchEvent(new Event('change', { bubbles: true }));
        otpInput.dispatchEvent(new Event('blur', { bubbles: true }));
        console.log('✅ Đã điền mã OTP');
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
                        console.log(`✅ Found verify button with selector: ${selector}`);
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
            throw new Error('Không tìm thấy nút xác thực OTP');
        }

        // Click verify button
        console.log('🚀 Clicking verify button...');
        verifyButton.click();
        sendStatus('✅ Đã gửi mã OTP, đang đợi kết quả...', 'success');
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
            console.log('✅ Signup successful!');
            sendStatus('✅ Đăng ký thành công!', 'success');

            // Mark as success and move to next
            currentDataIndex++;
            stats.processed++;
            stats.success++;
            updateStats();
            chrome.storage.local.set({
                'chatgpt-signup-current-index': currentDataIndex
            });

            await delay(2000);
            await startSignupLoop();
        } else {
            // Check for error messages
            const errorMessages = document.querySelectorAll('.error, .alert, [role="alert"]');
            if (errorMessages.length > 0) {
                const errorText = Array.from(errorMessages)
                    .map(el => el.innerText || el.textContent)
                    .join(' ');
                throw new Error('Lỗi xác thực: ' + errorText);
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

function waitForUrlChange(containsArray, timeout = 15000) {
    return new Promise((resolve) => {
        if (!isRunning) {
            resolve(false);
            return;
        }

        const checkUrl = () => {
            const currentUrl = window.location.href.toLowerCase();
            return containsArray.some(term => currentUrl.includes(term.toLowerCase()));
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
        'chatgpt-signup-status': {
            message: message,
            type: type,
            timestamp: Date.now()
        }
    });
}

function updateStats() {
    chrome.storage.local.set({
        'chatgpt-signup-stats': stats
    });
}

