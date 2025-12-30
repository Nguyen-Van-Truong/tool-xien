// SheerID Form Auto-Fill Content Script
// Injects into SheerID verification pages and auto-fills the form

console.log('[SheerID Form] Content script loaded');

// Month name to number mapping
const MONTH_TO_NUM = {
    "January": "01", "February": "02", "March": "03", "April": "04",
    "May": "05", "June": "06", "July": "07", "August": "08",
    "September": "09", "October": "10", "November": "11", "December": "12"
};

// Listen for fill command
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'FILL_FORM' && message.veteran) {
        console.log('[SheerID Form] Received fill command:', message.veteran);
        fillForm(message.veteran);
    }
});

// Auto-check if we should fill form on page load
window.addEventListener('load', () => {
    setTimeout(checkAndAutoFill, 1500);
});

async function checkAndAutoFill() {
    // Check if extension is running and has veteran data
    const result = await chrome.storage.local.get(['verifyState', 'veterans', 'currentIndex']);

    if (result.verifyState?.isRunning && result.veterans?.length > 0) {
        const currentIndex = result.currentIndex || 0;
        const veteran = result.veterans[currentIndex];

        if (veteran) {
            console.log('[SheerID Form] Auto-filling for:', veteran.firstName);
            fillForm(veteran);
        }
    }
}

// Main fill function
async function fillForm(veteran) {
    console.log('[SheerID Form] Starting form fill...');

    try {
        // Wait for form to be ready
        await waitForElement('input, select, button');

        // Try different form field selectors
        const filled = await tryFillFields(veteran);

        if (filled) {
            console.log('[SheerID Form] Form filled successfully');
            chrome.runtime.sendMessage({ type: 'FORM_FILLED' });

            // Wait a bit then check for submit
            setTimeout(() => {
                trySubmitForm();
            }, 1000);
        } else {
            console.log('[SheerID Form] Could not fill form - fields not found');
        }

    } catch (error) {
        console.error('[SheerID Form] Error:', error);
    }
}

// Try to fill form fields with various selectors
async function tryFillFields(vet) {
    let filledCount = 0;

    // === FIRST NAME ===
    const firstNameFields = [
        'input[name="firstName"]',
        'input[id="firstName"]',
        'input[placeholder*="First"]',
        'input[aria-label*="First"]',
        'input[data-testid="firstName"]'
    ];
    if (fillField(firstNameFields, vet.firstName)) filledCount++;

    // === LAST NAME ===
    const lastNameFields = [
        'input[name="lastName"]',
        'input[id="lastName"]',
        'input[placeholder*="Last"]',
        'input[aria-label*="Last"]',
        'input[data-testid="lastName"]'
    ];
    if (fillField(lastNameFields, vet.lastName)) filledCount++;

    // === EMAIL ===
    const emailFields = [
        'input[name="email"]',
        'input[type="email"]',
        'input[id="email"]',
        'input[placeholder*="email"]',
        'input[aria-label*="email"]'
    ];
    if (fillField(emailFields, vet.email)) filledCount++;

    // === BIRTH DATE ===
    // Try combined date field first
    const birthDate = formatDate(vet.birthYear, vet.birthMonth, vet.birthDay);
    const birthDateFields = [
        'input[name="birthDate"]',
        'input[id="birthDate"]',
        'input[type="date"][name*="birth"]',
        'input[aria-label*="birth"]'
    ];
    if (fillField(birthDateFields, birthDate)) {
        filledCount++;
    } else {
        // Try separate fields
        fillBirthDateSeparate(vet);
    }

    // === BRANCH (SELECT) ===
    const branchSelects = [
        'select[name="organization"]',
        'select[id="organization"]',
        'select[name*="branch"]',
        'select[aria-label*="branch"]'
    ];
    if (selectOption(branchSelects, vet.branch)) filledCount++;

    // Also try clicking branch buttons if present
    tryClickBranchButton(vet.branch);

    // === DISCHARGE DATE ===
    const dischargeDate = formatDischargeDate(vet);
    const dischargeDateFields = [
        'input[name="dischargeDate"]',
        'input[id="dischargeDate"]',
        'input[type="date"][name*="discharge"]',
        'input[aria-label*="discharge"]'
    ];
    if (fillField(dischargeDateFields, dischargeDate)) filledCount++;

    // === STATUS (VETERAN) ===
    // Try to select "Veteran" option if present
    const statusSelects = [
        'select[name="status"]',
        'select[name="militaryStatus"]',
        'input[value="VETERAN"]'
    ];
    selectOption(statusSelects, 'VETERAN');

    // Try clicking Veteran button/radio
    tryClickVeteranStatus();

    console.log(`[SheerID Form] Filled ${filledCount} fields`);
    return filledCount >= 2; // At least name filled
}

// Fill a field with value
function fillField(selectors, value) {
    for (const selector of selectors) {
        const el = document.querySelector(selector);
        if (el) {
            el.focus();
            el.value = value;
            // Trigger events
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.dispatchEvent(new Event('blur', { bubbles: true }));
            console.log(`[SheerID Form] Filled ${selector} with ${value}`);
            return true;
        }
    }
    return false;
}

// Select an option in a dropdown
function selectOption(selectors, value) {
    for (const selector of selectors) {
        const el = document.querySelector(selector);
        if (el && el.tagName === 'SELECT') {
            // Find matching option
            for (const option of el.options) {
                if (option.text.includes(value) || option.value.includes(value)) {
                    el.value = option.value;
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    console.log(`[SheerID Form] Selected ${value} in ${selector}`);
                    return true;
                }
            }
        }
    }
    return false;
}

// Try to fill birth date in separate fields
function fillBirthDateSeparate(vet) {
    // Month
    fillField([
        'select[name="birthMonth"]',
        'input[name="birthMonth"]',
        'select[name*="month"]'
    ], vet.birthMonth);

    // Day
    fillField([
        'input[name="birthDay"]',
        'select[name="birthDay"]',
        'input[name*="day"]'
    ], vet.birthDay);

    // Year
    fillField([
        'input[name="birthYear"]',
        'select[name="birthYear"]',
        'input[name*="year"]'
    ], vet.birthYear);
}

// Format date to YYYY-MM-DD
function formatDate(year, month, day) {
    const monthNum = MONTH_TO_NUM[month] || '01';
    return `${year}-${monthNum.padStart(2, '0')}-${day.padStart(2, '0')}`;
}

// Format discharge date (use Dec 1, 2025 if not 2025)
function formatDischargeDate(vet) {
    if (vet.dischargeYear === '2025') {
        return formatDate(vet.dischargeYear, vet.dischargeMonth, vet.dischargeDay);
    } else {
        console.log('[SheerID Form] Using default discharge date: Dec 1, 2025');
        return '2025-12-01';
    }
}

// Try clicking branch button (for radio-style selection)
function tryClickBranchButton(branch) {
    const buttons = document.querySelectorAll('button, div[role="button"], label');
    for (const btn of buttons) {
        if (btn.textContent.includes(branch)) {
            btn.click();
            console.log(`[SheerID Form] Clicked branch button: ${branch}`);
            return true;
        }
    }
    return false;
}

// Try clicking Veteran status radio/button
function tryClickVeteranStatus() {
    const elements = document.querySelectorAll('button, div[role="button"], label, input[type="radio"]');
    for (const el of elements) {
        if (el.textContent?.toLowerCase().includes('veteran') || el.value === 'VETERAN') {
            el.click();
            console.log('[SheerID Form] Clicked Veteran status');
            return true;
        }
    }
    return false;
}

// Try to submit the form
function trySubmitForm() {
    const submitSelectors = [
        'button[type="submit"]',
        'button[data-testid="submit"]',
        'input[type="submit"]',
        'button:contains("Submit")',
        'button:contains("Verify")',
        'button:contains("Continue")'
    ];

    for (const selector of submitSelectors) {
        try {
            const btn = document.querySelector(selector);
            if (btn && !btn.disabled) {
                console.log('[SheerID Form] Found submit button, clicking...');
                btn.click();
                return true;
            }
        } catch (e) {
            // :contains is not standard, try text search
        }
    }

    // Fallback: find by text content
    const buttons = document.querySelectorAll('button');
    for (const btn of buttons) {
        const text = btn.textContent.toLowerCase();
        if ((text.includes('submit') || text.includes('verify') || text.includes('continue'))
            && !btn.disabled) {
            console.log('[SheerID Form] Clicking button:', btn.textContent);
            btn.click();
            return true;
        }
    }

    console.log('[SheerID Form] No submit button found');
    return false;
}

// Wait for element to appear
function waitForElement(selector, timeout = 10000) {
    return new Promise((resolve, reject) => {
        const el = document.querySelector(selector);
        if (el) {
            resolve(el);
            return;
        }

        const observer = new MutationObserver((mutations, obs) => {
            const el = document.querySelector(selector);
            if (el) {
                obs.disconnect();
                resolve(el);
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        setTimeout(() => {
            observer.disconnect();
            resolve(null); // Resolve with null instead of reject
        }, timeout);
    });
}
