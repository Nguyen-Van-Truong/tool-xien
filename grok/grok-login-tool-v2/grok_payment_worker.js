/**
 * Grok Payment Worker - Puppeteer Automation Module
 * Handles login + SuperGrok trial payment via Stripe
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');

class GrokPaymentWorker {
    constructor(mainWindow, browserId, options = {}) {
        this.mainWindow = mainWindow;
        this.browsers = [];
        this.isRunning = false;
        this.maxConcurrent = options.maxConcurrent || 3;
        this.keepBrowserOpen = options.keepBrowserOpen !== false;
        this.headless = options.headless || false;
        this.results = { success: 0, failed: 0, total: 0 };
        this.cards = [];
        
        // Autofill options (like Propaganda extension)
        this.autofillDelay = options.autofillDelay || 7; // seconds
        this.randomName = options.randomName !== false; // default true
        this.randomAddress = options.randomAddress !== false; // default true
        this.billingInfo = options.billingInfo || {};
    }

    log(message, type = 'info') {
        console.log(message);
        if (this.mainWindow) {
            this.mainWindow.webContents.send('log', { message, type });
        }
    }

    updateProgress(current, total, text) {
        if (this.mainWindow) {
            this.mainWindow.webContents.send('progress', { current, total, text });
        }
    }

    updateBrowserCount() {
        const count = this.browsers.length;
        if (this.mainWindow) {
            this.mainWindow.webContents.send('browser-count', {
                active: count,
                max: this.maxConcurrent
            });
        }
    }

    saveResult(account, status, extraData = {}) {
        const timestamp = new Date().toISOString();
        if (status === 'success') {
            // Format: email|password|cardUsed
            const cardInfo = extraData.cardUsed || 'unknown';
            const line = `${account.email}|${account.password}|${cardInfo}\n`;
            fs.appendFileSync('success.txt', line);
            this.results.success++;
        } else {
            // Failed format: email|password|error|timestamp
            const line = `${account.email}|${account.password}|${extraData.error || 'unknown'}|${timestamp}\n`;
            fs.appendFileSync('failed.txt', line);
            this.results.failed++;
        }
        if (this.mainWindow) {
            this.mainWindow.webContents.send('result', this.results);
        }
    }

    // Generate random cardholder name
    generateRandomName() {
        const firstNames = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emma', 'James', 'Emily', 'Robert', 'Olivia', 'William', 'Sophia', 'Benjamin', 'Isabella', 'Daniel', 'Mia', 'Alexander', 'Charlotte', 'Henry', 'Amelia', 'Ethan', 'Harper', 'Mason', 'Evelyn', 'Logan', 'Abigail', 'Lucas', 'Elizabeth', 'Jackson', 'Sofia'];
        const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Martinez', 'Lopez', 'Wilson', 'Anderson', 'Taylor', 'Thomas', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White', 'Harris', 'Clark', 'Lewis', 'Robinson', 'Walker', 'Young', 'Hall', 'Allen', 'King', 'Wright'];
        
        const firstName = firstNames[Math.floor(Math.random() * firstNames.length)];
        const lastName = lastNames[Math.floor(Math.random() * lastNames.length)];
        return `${firstName} ${lastName}`;
    }

    // Generate random US address (like Propaganda extension)
    generateRandomAddress() {
        const streetNumbers = Array.from({length: 9999}, (_, i) => i + 1);
        const streetNames = ['Main', 'Oak', 'Park', 'Elm', 'Maple', 'Cedar', 'Pine', 'Washington', 'Lake', 'Hill', 'Sunset', 'Spring', 'River', 'Forest', 'Valley', 'Highland', 'Meadow', 'Garden', 'Ridge', 'View'];
        const streetTypes = ['St', 'Ave', 'Blvd', 'Dr', 'Ln', 'Way', 'Rd', 'Ct', 'Pl', 'Cir'];
        const aptTypes = ['Apt', 'Suite', 'Unit', '#'];
        
        const cities = [
            { city: 'New York', state: 'NY', zip: '10001' },
            { city: 'Los Angeles', state: 'CA', zip: '90001' },
            { city: 'Chicago', state: 'IL', zip: '60601' },
            { city: 'Houston', state: 'TX', zip: '77001' },
            { city: 'Phoenix', state: 'AZ', zip: '85001' },
            { city: 'Philadelphia', state: 'PA', zip: '19101' },
            { city: 'San Antonio', state: 'TX', zip: '78201' },
            { city: 'San Diego', state: 'CA', zip: '92101' },
            { city: 'Dallas', state: 'TX', zip: '75201' },
            { city: 'San Jose', state: 'CA', zip: '95101' },
            { city: 'Austin', state: 'TX', zip: '78701' },
            { city: 'Jacksonville', state: 'FL', zip: '32201' },
            { city: 'Fort Worth', state: 'TX', zip: '76101' },
            { city: 'Columbus', state: 'OH', zip: '43201' },
            { city: 'Charlotte', state: 'NC', zip: '28201' },
            { city: 'Seattle', state: 'WA', zip: '98101' },
            { city: 'Denver', state: 'CO', zip: '80201' },
            { city: 'Boston', state: 'MA', zip: '02101' },
            { city: 'Portland', state: 'OR', zip: '97201' },
            { city: 'Miami', state: 'FL', zip: '33101' }
        ];
        
        const streetNum = streetNumbers[Math.floor(Math.random() * 999)] + 1;
        const streetName = streetNames[Math.floor(Math.random() * streetNames.length)];
        const streetType = streetTypes[Math.floor(Math.random() * streetTypes.length)];
        const cityData = cities[Math.floor(Math.random() * cities.length)];
        
        // 30% chance of having apt number
        let address2 = '';
        if (Math.random() < 0.3) {
            const aptType = aptTypes[Math.floor(Math.random() * aptTypes.length)];
            const aptNum = Math.floor(Math.random() * 999) + 1;
            address2 = `${aptType} ${aptNum}`;
        }
        
        return {
            address1: `${streetNum} ${streetName} ${streetType}`,
            address2: address2,
            city: cityData.city,
            state: cityData.state,
            zip: cityData.zip
        };
    }

    async start(accounts, cards) {
        this.isRunning = true;
        this.cards = [...cards]; // Copy cards array
        this.results = { success: 0, failed: 0, total: accounts.length };
        const startTime = Date.now();

        this.log(`🚀 Starting login + payment for ${accounts.length} accounts (max ${this.maxConcurrent} concurrent)...`, 'info');
        this.log(`💳 ${cards.length} cards available for payment`, 'info');

        // Process in batches
        for (let i = 0; i < accounts.length && this.isRunning; i += this.maxConcurrent) {
            const batch = accounts.slice(i, i + this.maxConcurrent);
            const batchNum = Math.floor(i / this.maxConcurrent) + 1;
            const totalBatches = Math.ceil(accounts.length / this.maxConcurrent);

            this.log(`\n📦 Batch ${batchNum}/${totalBatches}: ${batch.length} account(s) with 1s stagger...`, 'info');

            // Staggered launch - 1 second delay between each browser
            const promises = batch.map((account, idx) => {
                const accountNum = i + idx + 1;
                return new Promise(async (resolve) => {
                    // Wait idx seconds before starting (0s, 1s, 2s, ...)
                    await new Promise(r => setTimeout(r, idx * 1000));
                    const result = await this.processAccount(account, accountNum, accounts.length);
                    resolve(result);
                });
            });

            await Promise.allSettled(promises);
            this.log(`✅ Batch ${batchNum}/${totalBatches} completed!`, 'success');
        }

        const totalTime = Math.round((Date.now() - startTime) / 1000);
        this.log(`\n🎉 Done! Success: ${this.results.success}, Failed: ${this.results.failed} (${totalTime}s)`, 'success');

        if (this.keepBrowserOpen) {
            this.log(`🌐 ${this.browsers.length} browser(s) kept open. Use "Close All Browsers" to close.`, 'info');
        }

        if (this.mainWindow) {
            this.mainWindow.webContents.send('complete', { ...this.results, totalTime });
        }
    }

    async processAccount(account, accountNum, total) {
        const { email, password } = account;
        let browser = null;

        try {
            this.log(`\n━━ [${accountNum}/${total}] ${email} ━━`, 'info');
            this.updateProgress(accountNum, total, `Processing ${accountNum}/${total}...`);

            // Launch browser
            this.log('🌐 1/19: Launching browser...', 'info');
            const chromePaths = [
                'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
                process.env.LOCALAPPDATA + '\\Google\\Chrome\\Application\\chrome.exe'
            ];
            const executablePath = chromePaths.find(p => fs.existsSync(p));
            if (!executablePath) throw new Error('Chrome not found');

            browser = await puppeteer.launch({
                executablePath,
                headless: this.headless,
                args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled'],
                defaultViewport: { width: 1280, height: 800 }
            });
            this.browsers.push({ browser, email });
            this.updateBrowserCount();
            const page = await browser.newPage();

            // ========== LOGIN PHASE ==========
            
            // Navigate to sign-in
            this.log('🔗 2/19: Navigating to sign-in...', 'info');
            await page.goto('https://accounts.x.ai/sign-in', { waitUntil: 'networkidle2', timeout: 30000 });

            // Click "Sign in with email"
            this.log('🖱️ 3/19: Clicking email button...', 'info');
            await page.waitForSelector('button svg.lucide-mail', { timeout: 10000 });
            await page.evaluate(() => document.querySelector('button svg.lucide-mail').closest('button').click());
            await page.waitForTimeout(2000);

            // Enter email
            this.log('📧 4/19: Entering email...', 'info');
            await page.waitForSelector('input[type="email"]', { timeout: 10000 });
            await page.type('input[type="email"]', email, { delay: 50 });
            await page.waitForTimeout(500);

            // Click Next
            this.log('➡️ 5/19: Clicking Next...', 'info');
            await page.waitForSelector('button[type="submit"]', { timeout: 5000 });
            await page.click('button[type="submit"]');
            await page.waitForTimeout(2000);

            // Enter password
            this.log('🔑 6/19: Entering password...', 'info');
            await page.waitForSelector('input[type="password"]', { timeout: 10000 });
            await page.type('input[type="password"]', password, { delay: 50 });
            await page.waitForTimeout(500);

            // Click Login
            this.log('🔓 7/19: Clicking Login...', 'info');
            await page.click('button[type="submit"]');
            await page.waitForTimeout(3000);

            // Wait for login success - check URL or page content
            this.log('⏳ 8/19: Verifying login...', 'info');
            await page.waitForTimeout(2000);
            
            const currentUrl = page.url();
            if (currentUrl.includes('sign-in') || currentUrl.includes('sign-up')) {
                throw new Error('Login failed - still on auth page');
            }

            this.log('✅ Login successful!', 'success');

            // ========== PAYMENT PHASE ==========
            
            // Navigate to subscribe page
            this.log('💳 9/19: Navigating to subscribe...', 'info');
            await page.goto('https://grok.com/#subscribe', { waitUntil: 'networkidle2', timeout: 30000 });
            await page.waitForTimeout(3000); // Wait for page to fully render

            // Click "Start 7-day free trial" button - wait for button to be visible and enabled
            this.log('🖱️ 10/19: Clicking trial button...', 'info');
            
            // Wait for button to appear and be visible
            await page.waitForSelector('button[aria-label="Upgrade to SuperGrok"]', { visible: true, timeout: 15000 });
            
            // Additional delay to ensure button is fully interactive
            await page.waitForTimeout(2000);
            
            // Check if button is enabled before clicking
            const buttonEnabled = await page.evaluate(() => {
                const btn = document.querySelector('button[aria-label="Upgrade to SuperGrok"]');
                return btn && !btn.disabled && btn.offsetParent !== null;
            });
            
            if (!buttonEnabled) {
                this.log('⏳ Button not ready, waiting...', 'warning');
                await page.waitForTimeout(2000);
            }
            
            // Click the button
            await page.click('button[aria-label="Upgrade to SuperGrok"]');
            this.log('✅ Trial button clicked!', 'success');
            await page.waitForTimeout(3000);

            // Wait for Stripe checkout page
            this.log('⏳ 11/19: Waiting for Stripe checkout...', 'info');
            await page.waitForFunction(
                () => window.location.href.includes('checkout.stripe.com'),
                { timeout: 30000 }
            );
            await page.waitForTimeout(2000);

            // Try each card until success or all cards exhausted
            let paymentSuccess = false;
            let usedCard = null;

            for (let cardIdx = 0; cardIdx < this.cards.length && !paymentSuccess; cardIdx++) {
                const card = this.cards[cardIdx];
                this.log(`💳 Trying card ${cardIdx + 1}/${this.cards.length}: ****${card.number.slice(-4)}`, 'info');

                try {
                    paymentSuccess = await this.tryPayment(page, card);
                    if (paymentSuccess) {
                        usedCard = card;
                        this.log(`✅ Payment successful with card ****${card.number.slice(-4)}!`, 'success');
                    }
                } catch (payError) {
                    this.log(`❌ Card ****${card.number.slice(-4)} failed: ${payError.message}`, 'warning');
                    
                    // If not last card, go back and try again
                    if (cardIdx < this.cards.length - 1) {
                        this.log('🔄 Reloading checkout page for next card...', 'info');
                        await page.goto('https://grok.com/#subscribe', { waitUntil: 'networkidle2', timeout: 30000 });
                        await page.waitForTimeout(2000);
                        await page.waitForSelector('button[aria-label="Upgrade to SuperGrok"]', { timeout: 15000 });
                        await page.click('button[aria-label="Upgrade to SuperGrok"]');
                        await page.waitForTimeout(3000);
                        await page.waitForFunction(
                            () => window.location.href.includes('checkout.stripe.com'),
                            { timeout: 30000 }
                        );
                        await page.waitForTimeout(2000);
                    }
                }
            }

            if (paymentSuccess) {
                this.log(`🎉 SUCCESS: ${email} - card ****${usedCard.number.slice(-4)}`, 'success');
                this.saveResult(account, 'success', { cardUsed: `****${usedCard.number.slice(-4)}` });
            } else {
                throw new Error('All cards failed');
            }

        } catch (error) {
            this.log(`❌ FAILED: ${email} - ${error.message}`, 'error');
            this.saveResult(account, 'failed', { error: error.message });
        } finally {
            if (!this.keepBrowserOpen && browser) {
                await browser.close();
                this.browsers = this.browsers.filter(b => b.browser !== browser);
                this.updateBrowserCount();
            }
        }
    }

    async tryPayment(page, card) {
        // Autofill delay (like Propaganda extension)
        if (this.autofillDelay > 0) {
            this.log(`⏳ Waiting ${this.autofillDelay}s before autofill...`, 'info');
            for (let i = this.autofillDelay; i > 0; i--) {
                this.log(`⏳ Autofill in ${i}s...`, 'info');
                await page.waitForTimeout(1000);
            }
        }

        // Click Card payment method if not selected
        this.log('💳 12/19: Selecting card payment...', 'info');
        try {
            const cardRadio = await page.$('#payment-method-accordion-item-title-card');
            if (cardRadio) {
                const isChecked = await page.evaluate(el => el.getAttribute('aria-checked') === 'true', cardRadio);
                if (!isChecked) {
                    await page.click('.card-accordion-item-cover');
                    await page.waitForTimeout(1000);
                }
            }
        } catch (e) {
            // Card might already be selected or different UI
        }

        // Wait for card inputs
        await page.waitForSelector('#cardNumber', { timeout: 10000 });

        // Clear and fill card number
        this.log('💳 13/19: Entering card number...', 'info');
        await page.click('#cardNumber', { clickCount: 3 });
        await page.type('#cardNumber', card.number, { delay: 30 });
        await page.waitForTimeout(500);

        // Fill expiry (MM/YY format)
        this.log('📅 14/19: Entering expiry...', 'info');
        const expiryFormatted = `${card.month}${card.year.slice(-2)}`; // MMYY
        await page.click('#cardExpiry', { clickCount: 3 });
        await page.type('#cardExpiry', expiryFormatted, { delay: 30 });
        await page.waitForTimeout(500);

        // Fill CVC
        this.log('🔒 15/19: Entering CVC...', 'info');
        await page.click('#cardCvc', { clickCount: 3 });
        await page.type('#cardCvc', card.cvc, { delay: 30 });
        await page.waitForTimeout(500);

        // Fill cardholder name
        this.log('👤 16/19: Entering cardholder name...', 'info');
        let cardholderName;
        if (this.randomName) {
            cardholderName = this.generateRandomName();
            this.log(`🎲 Using random name: ${cardholderName}`, 'info');
        } else if (this.billingInfo.name) {
            cardholderName = this.billingInfo.name;
            this.log(`📝 Using default name: ${cardholderName}`, 'info');
        } else {
            cardholderName = this.generateRandomName();
            this.log(`🎲 No default, using random: ${cardholderName}`, 'info');
        }
        await page.click('#billingName', { clickCount: 3 });
        await page.type('#billingName', cardholderName, { delay: 30 });
        await page.waitForTimeout(500);

        // Fill billing address if fields exist (like Propaganda extension)
        let addressInfo;
        if (this.randomAddress) {
            addressInfo = this.generateRandomAddress();
            this.log(`🎲 Using random address: ${addressInfo.address1}, ${addressInfo.city}`, 'info');
        } else if (this.billingInfo.address1) {
            addressInfo = {
                address1: this.billingInfo.address1,
                address2: this.billingInfo.address2 || '',
                city: this.billingInfo.city || '',
                state: this.billingInfo.state || '',
                zip: this.billingInfo.zip || ''
            };
            this.log(`📝 Using default address: ${addressInfo.address1}`, 'info');
        } else {
            addressInfo = this.generateRandomAddress();
            this.log(`🎲 No default, using random address`, 'info');
        }

        // Try to fill address fields if they exist
        try {
            const addressLine1 = await page.$('#billingAddressLine1, #billingAddress, input[name="billingAddressLine1"]');
            if (addressLine1) {
                this.log('🏠 Filling billing address...', 'info');
                await addressLine1.click({ clickCount: 3 });
                await addressLine1.type(addressInfo.address1, { delay: 30 });
                await page.waitForTimeout(300);
                
                // Address line 2
                const addressLine2 = await page.$('#billingAddressLine2, input[name="billingAddressLine2"]');
                if (addressLine2 && addressInfo.address2) {
                    await addressLine2.click({ clickCount: 3 });
                    await addressLine2.type(addressInfo.address2, { delay: 30 });
                    await page.waitForTimeout(300);
                }
                
                // City
                const cityField = await page.$('#billingLocality, #billingCity, input[name="billingLocality"]');
                if (cityField && addressInfo.city) {
                    await cityField.click({ clickCount: 3 });
                    await cityField.type(addressInfo.city, { delay: 30 });
                    await page.waitForTimeout(300);
                }
                
                // State
                const stateField = await page.$('#billingAdministrativeArea, #billingState, input[name="billingAdministrativeArea"]');
                if (stateField && addressInfo.state) {
                    await stateField.click({ clickCount: 3 });
                    await stateField.type(addressInfo.state, { delay: 30 });
                    await page.waitForTimeout(300);
                }
                
                // ZIP
                const zipField = await page.$('#billingPostalCode, #billingZip, input[name="billingPostalCode"]');
                if (zipField && addressInfo.zip) {
                    await zipField.click({ clickCount: 3 });
                    await zipField.type(addressInfo.zip, { delay: 30 });
                    await page.waitForTimeout(300);
                }
            }
        } catch (e) {
            this.log(`⚠️ Address fields not found or not required`, 'warning');
        }

        // Click submit button
        this.log('🚀 17/19: Submitting payment...', 'info');
        await page.click('.SubmitButton');
        await page.waitForTimeout(3000);

        // Check for hCaptcha verification - MUST handle iframe properly
        this.log('🔍 18/19: Checking for hCaptcha verification...', 'info');
        await page.waitForTimeout(2000); // Wait for verification UI to appear
        
        try {
            // Check if hCaptcha dialog appeared
            const hasHCaptcha = await page.evaluate(() => {
                const text = document.body.innerText || '';
                return text.includes('One more step') || text.includes('Select the checkbox') || 
                       document.querySelector('iframe[src*="hcaptcha"]') !== null;
            });
            
            if (hasHCaptcha) {
                this.log('🤖 hCaptcha detected! Looking for checkbox...', 'info');
                
                // Wait for hCaptcha iframe to fully load
                await page.waitForTimeout(2000);
                
                // Find the hCaptcha iframe
                let checkboxClicked = false;
                let retryCount = 0;
                const maxRetries = 3;
                
                while (!checkboxClicked && retryCount < maxRetries) {
                    retryCount++;
                    this.log(`🔄 Attempt ${retryCount}/${maxRetries} to click checkbox...`, 'info');
                    
                    // Get all frames and find hCaptcha iframe
                    const frames = page.frames();
                    this.log(`📋 Found ${frames.length} frames`, 'info');
                    
                    for (const frame of frames) {
                        try {
                            const frameUrl = frame.url();
                            
                            // Check if this is hCaptcha iframe
                            if (frameUrl.includes('hcaptcha') || frameUrl.includes('newassets.hcaptcha')) {
                                this.log(`🎯 Found hCaptcha iframe: ${frameUrl.substring(0, 50)}...`, 'info');
                                
                                // Wait for checkbox to be present in iframe
                                await page.waitForTimeout(1000);
                                
                                // Find checkbox inside iframe
                                const checkbox = await frame.$('#checkbox');
                                if (checkbox) {
                                    // Check current state
                                    const isChecked = await frame.evaluate(() => {
                                        const cb = document.querySelector('#checkbox');
                                        return cb ? cb.getAttribute('aria-checked') === 'true' : false;
                                    });
                                    
                                    if (isChecked) {
                                        this.log('✅ Checkbox already checked!', 'success');
                                        checkboxClicked = true;
                                        break;
                                    }
                                    
                                    // Click the checkbox
                                    this.log('🖱️ Clicking hCaptcha checkbox...', 'info');
                                    await checkbox.click();
                                    await page.waitForTimeout(2000);
                                    
                                    // Verify if clicked successfully
                                    const nowChecked = await frame.evaluate(() => {
                                        const cb = document.querySelector('#checkbox');
                                        return cb ? cb.getAttribute('aria-checked') === 'true' : false;
                                    });
                                    
                                    if (nowChecked) {
                                        this.log('✅ Checkbox clicked successfully!', 'success');
                                        checkboxClicked = true;
                                        break;
                                    } else {
                                        this.log('⚠️ Click may not have registered, will retry...', 'warning');
                                    }
                                } else {
                                    this.log('⚠️ Checkbox element not found in iframe', 'warning');
                                }
                            }
                        } catch (frameErr) {
                            this.log(`⚠️ Frame error: ${frameErr.message}`, 'warning');
                        }
                    }
                    
                    // If not clicked yet, wait before retry
                    if (!checkboxClicked && retryCount < maxRetries) {
                        this.log('⏳ Waiting 2s before retry...', 'info');
                        await page.waitForTimeout(2000);
                    }
                }
                
                if (!checkboxClicked) {
                    this.log('⚠️ Could not click checkbox after all retries', 'warning');
                }
                
                // Wait for hCaptcha to process
                await page.waitForTimeout(3000);
            } else {
                this.log('ℹ️ No hCaptcha detected', 'info');
            }
            
        } catch (e) {
            this.log(`⚠️ Verification error: ${e.message}`, 'warning');
        }

        // Wait for redirect (success or failure)
        this.log('⏳ 19/19: Waiting for result (max 45s)...', 'info');
        
        // Wait up to 45 seconds for redirect (payment processing can be slow)
        let success = false;
        let lastUrl = '';
        
        for (let i = 0; i < 45 && !success; i++) {
            await page.waitForTimeout(1000);
            const url = page.url();
            
            // Log URL change
            if (url !== lastUrl) {
                this.log(`🔗 URL: ${url.substring(0, 60)}...`, 'info');
                lastUrl = url;
            }
            
            // Check for success conditions
            if (url.includes('grok.com') && !url.includes('checkout.stripe.com')) {
                // Redirected back to grok.com - success!
                this.log('✅ Redirected to grok.com!', 'success');
                success = true;
            } else if (url.includes('checkout=success')) {
                this.log('✅ Checkout success detected!', 'success');
                success = true;
            }
            
            // Check for error messages on Stripe page (wait longer before declaring failure)
            if (url.includes('checkout.stripe.com') && i > 10) {
                const errorInfo = await page.evaluate(() => {
                    // Check for specific Stripe error elements
                    const fieldError = document.querySelector('.FieldError');
                    const paymentError = document.querySelector('[class*="PaymentError"]');
                    const declineError = document.querySelector('[class*="decline"]');
                    const errorBanner = document.querySelector('.Banner--error, .Banner--danger');
                    
                    // Check for error text content
                    const bodyText = document.body.innerText || '';
                    const hasDeclineText = bodyText.includes('declined') || 
                                          bodyText.includes('couldn\'t be processed') ||
                                          bodyText.includes('card was declined') ||
                                          bodyText.includes('insufficient funds');
                    
                    return {
                        hasFieldError: fieldError && fieldError.textContent.length > 0,
                        hasPaymentError: !!paymentError || !!declineError || !!errorBanner,
                        hasDeclineText: hasDeclineText,
                        errorMessage: fieldError?.textContent || ''
                    };
                });
                
                if (errorInfo.hasDeclineText || errorInfo.hasPaymentError) {
                    this.log(`❌ Payment error detected: ${errorInfo.errorMessage || 'Card declined'}`, 'error');
                    throw new Error('Payment declined');
                }
            }
            
            // Progress indicator
            if (i > 0 && i % 10 === 0) {
                this.log(`⏳ Still waiting... (${i}s)`, 'info');
            }
        }

        if (!success) {
            throw new Error('Payment timeout - no redirect after 45s');
        }

        return true;
    }

    async stop() {
        this.isRunning = false;
        this.log('⏸️ Stopping...', 'warning');
        await this.closeAllBrowsers();
    }

    async closeAllBrowsers() {
        this.log(`🗑️ Closing ${this.browsers.length} browser(s)...`, 'warning');
        for (const b of this.browsers) {
            try {
                await b.browser.close();
                this.log(`✅ Closed: ${b.email}`, 'success');
            } catch (e) { }
        }
        this.browsers = [];
        this.updateBrowserCount();
    }
}

module.exports = { GrokPaymentWorker };
