// Content script for SheerID verification forms
// Tested and working with SheerID's React-based custom combobox inputs

console.log('Military Verify Extension: Content script loaded for SheerID');

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'fillForm') {
        fillSheerIDForm(request.data);
        sendResponse({ success: true });
    }
    return true;
});

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Fill text input using execCommand for React compatibility
async function fillInput(id, value) {
    const element = document.getElementById(id);
    if (!element || !value) return false;

    element.scrollIntoView({ block: 'center' });
    element.focus();
    element.select();

    // Use execCommand for better React form compatibility
    document.execCommand('insertText', false, value.toString());

    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
    element.dispatchEvent(new Event('blur', { bubbles: true }));

    console.log(`Filled input ${id}: ${value}`);
    return true;
}

// Handle SheerID custom combobox - click to open, select option
async function fillCombobox(inputId, value) {
    const input = document.getElementById(inputId);
    if (!input || !value) return false;

    input.scrollIntoView({ block: 'center' });
    input.click();
    input.focus();
    await delay(800);

    // Find and click matching option
    const options = document.querySelectorAll('[role="option"]');
    for (const opt of options) {
        const optText = opt.textContent.toLowerCase();
        if (optText.includes(value.toLowerCase())) {
            opt.click();
            await delay(400);
            console.log(`Selected combobox ${inputId}: ${value}`);
            return true;
        }
    }

    console.log(`Option not found for ${inputId}: ${value}`);
    return false;
}

// Map status code to display value
function getStatusDisplay(status) {
    const map = {
        'MILITARY_VETERAN': 'Military Veteran or Retiree',
        'ACTIVE_DUTY': 'Active Duty',
        'RESERVIST': 'Reservist',
        'MILITARY_FAMILY': 'Military Family Member'
    };
    return map[status] || status;
}

// Main fill function
async function fillSheerIDForm(data) {
    console.log('Filling SheerID form with data:', data);

    window.scrollTo(0, 0);
    await delay(300);

    try {
        // === STEP 1: Fill all comboboxes first ===

        // Status
        if (data.status) {
            const statusValue = getStatusDisplay(data.status);
            await fillCombobox('sid-military-status', statusValue);
            await delay(200);
        }

        // Branch of Service
        if (data.branch) {
            await fillCombobox('sid-branch-of-service', data.branch);
            await delay(200);
        }

        // Birth Month
        if (data.birthMonth) {
            await fillCombobox('sid-birthdate__month', data.birthMonth);
            await delay(200);
        }

        // Discharge Month
        if (data.dischargeMonth) {
            await fillCombobox('sid-discharge-date__month', data.dischargeMonth);
            await delay(500);
        }

        // === STEP 2: Fill all text inputs ===

        // First Name
        if (data.firstName) {
            await fillInput('sid-first-name', data.firstName);
            await delay(100);
        }

        // Last Name
        if (data.lastName) {
            await fillInput('sid-last-name', data.lastName);
            await delay(100);
        }

        // Birth Day & Year
        if (data.birthDay) {
            await fillInput('sid-birthdate-day', data.birthDay);
            await delay(100);
        }
        if (data.birthYear) {
            await fillInput('sid-birthdate-year', data.birthYear);
            await delay(100);
        }

        // Discharge Day & Year
        if (data.dischargeDay) {
            await fillInput('sid-discharge-date-day', data.dischargeDay);
            await delay(100);
        }
        if (data.dischargeYear) {
            await fillInput('sid-discharge-date-year', data.dischargeYear);
            await delay(100);
        }

        // Email
        if (data.email) {
            await fillInput('sid-email', data.email);
        }

        console.log('Form filled successfully!');
        showNotification('✅ Form filled successfully!');

    } catch (error) {
        console.error('Error filling form:', error);
        showNotification('❌ Error: ' + error.message);
    }
}

// Show notification on page
function showNotification(message) {
    const existing = document.querySelector('.military-verify-notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.className = 'military-verify-notification';
    notification.textContent = message;
    notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 999999;
    padding: 12px 24px;
    background: linear-gradient(135deg, #00d9ff, #00ff88);
    color: #000;
    border-radius: 8px;
    font-weight: bold;
    font-size: 14px;
    box-shadow: 0 4px 15px rgba(0,217,255,0.4);
    animation: slideIn 0.3s ease;
  `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add floating button for quick fill
function addFloatingButton() {
    if (document.querySelector('.military-verify-btn')) return;

    const btn = document.createElement('button');
    btn.className = 'military-verify-btn';
    btn.innerHTML = '🎖️ Auto Fill';
    btn.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 999999;
    padding: 12px 20px;
    background: linear-gradient(135deg, #00d9ff, #00ff88);
    color: #000;
    border: none;
    border-radius: 25px;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(0,217,255,0.4);
    transition: all 0.3s ease;
    font-size: 14px;
  `;

    btn.addEventListener('mouseenter', () => btn.style.transform = 'scale(1.05)');
    btn.addEventListener('mouseleave', () => btn.style.transform = 'scale(1)');

    btn.addEventListener('click', async () => {
        const result = await chrome.storage.local.get(['lastUsed', 'veterans']);
        const data = result.lastUsed || (result.veterans && result.veterans[0]);

        if (data) {
            fillSheerIDForm(data);
        } else {
            showNotification('❌ No saved data. Open extension popup first.');
        }
    });

    document.body.appendChild(btn);
}

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
`;
document.head.appendChild(style);

// Initialize
setTimeout(addFloatingButton, 1500);
